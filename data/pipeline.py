"""Data pipeline: fetch all sources, validate, and return unified frames."""

from __future__ import annotations

import logging

import pandas as pd

import config
from data.fred import fetch_us_m2, fetch_fed_balance_sheet, fetch_pboc_m2, fetch_fx_rates
from data.ecb import fetch_ecb_balance_sheet
from data.boj import fetch_boj_balance_sheet
from data.validation import validate_frame

logger = logging.getLogger(__name__)

SOURCE_NAMES = ["us_m2", "fed_bs", "pboc_m2", "fx_rates", "ecb_bs", "boj_bs"]


def _get_fetchers() -> dict:
    return {
        "us_m2": fetch_us_m2,
        "fed_bs": fetch_fed_balance_sheet,
        "pboc_m2": fetch_pboc_m2,
        "fx_rates": fetch_fx_rates,
        "ecb_bs": fetch_ecb_balance_sheet,
        "boj_bs": fetch_boj_balance_sheet,
    }


def fetch_all() -> dict[str, pd.DataFrame]:
    fetchers = _get_fetchers()
    results = {}
    for name, fn in fetchers.items():
        try:
            df = fn()
        except Exception as e:
            logger.error("Loader %s raised: %s", name, e)
            df = pd.DataFrame()
        results[name] = df
    return results


def fetch_and_validate() -> dict[str, pd.DataFrame]:
    raw = fetch_all()
    validated = {}
    for name, df in raw.items():
        validated[name] = validate_frame(df, name)
    return validated


def report_sources(data: dict[str, pd.DataFrame]) -> str:
    lines = []
    for name in SOURCE_NAMES:
        df = data.get(name, pd.DataFrame())
        if df.empty:
            status = "EMPTY (stub or no data)"
        else:
            cols = ", ".join(df.columns)
            first = df.index.min().strftime("%Y-%m-%d") if len(df) > 0 else "n/a"
            last = df.index.max().strftime("%Y-%m-%d") if len(df) > 0 else "n/a"
            lag_info = config.PUBLICATION_LAG.get(name, {})
            lag = f"{lag_info.get('typical_min', '?')}-{lag_info.get('typical_max', '?')}d" if lag_info else "?"
            status = f"{len(df)} rows | {first} to {last} | cols=[{cols}] | lag={lag}"
        lines.append(f"  {name}: {status}")
    return "\n".join(lines)
