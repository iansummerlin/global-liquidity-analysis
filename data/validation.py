"""Validation rules for source data frames.

All source frames must satisfy:
- expected column name present
- numeric positive values
- monotonic increasing index
- no duplicate timestamps
- no future dates
"""

from __future__ import annotations

import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


# Expected column(s) per pipeline source key.
EXPECTED_COLUMNS: dict[str, list[str]] = {
    "us_m2": [config.SOURCE_COLUMNS["us_m2"]],
    "fed_bs": [config.SOURCE_COLUMNS["fed_bs"]],
    "pboc_m2": [config.SOURCE_COLUMNS["pboc_m2"]],
    "ecb_bs": [config.SOURCE_COLUMNS["ecb_bs"]],
    "boj_bs": [config.SOURCE_COLUMNS["boj_bs"]],
    "fx_rates": [
        config.SOURCE_COLUMNS["fx_eurusd"],
        config.SOURCE_COLUMNS["fx_jpyusd"],
        config.SOURCE_COLUMNS["fx_cnyusd"],
    ],
}


def validate_frame(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if df.empty:
        _check_schema(df, name)
        return df

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValidationError(f"{name}: index must be DatetimeIndex")

    _check_schema(df, name)

    if df.index.duplicated().any():
        raise ValidationError(f"{name}: duplicate timestamps found")

    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    now = pd.Timestamp.now(tz="UTC")
    future = df.index > now
    if future.any():
        raise ValidationError(f"{name}: future dates found ({future.sum()} rows)")

    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        valid = df[col].dropna()
        if (valid < 0).any():
            raise ValidationError(f"{name}.{col}: negative values found")

    return df


def _check_schema(df: pd.DataFrame, name: str) -> None:
    expected = EXPECTED_COLUMNS.get(name)
    if expected is None:
        return
    for col in expected:
        if col not in df.columns:
            raise ValidationError(f"{name}: missing expected column '{col}'")
