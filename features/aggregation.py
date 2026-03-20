"""Aggregate normalised components into composite signals."""

from __future__ import annotations

import pandas as pd

import config


def _align_to_month_end(components: dict[str, pd.Series]) -> dict[str, pd.Series]:
    """Align all component series to a common month-end DatetimeIndex.

    Components should already be in month-end frequency after normalisation
    (weekly series are resampled there). This builds a shared index from the
    intersection of available months and joins without forward-filling — missing
    months for a component contribute NaN (omitted from sum).
    """
    available = {k: v for k, v in components.items() if not v.empty}
    if not available:
        return {}

    df = pd.DataFrame(available)
    # Ensure index is month-end aligned (no-op if already ME)
    if not df.empty and hasattr(df.index, 'freqstr') and df.index.freqstr != 'ME':
        df.index = df.index.to_period("M").to_timestamp("M")
    return {col: df[col].dropna() for col in df.columns}


def _aggregate(components: dict[str, pd.Series], keys: list[str], name: str) -> pd.Series:
    available = {k: components[k] for k in keys if k in components and not components[k].empty}
    if not available:
        return pd.Series(dtype=float, name=name)
    aligned = _align_to_month_end(available)
    if not aligned:
        return pd.Series(dtype=float, name=name)
    result = pd.DataFrame(aligned).sum(axis=1)
    result.name = name
    return result


def build_global_m2(components: dict[str, pd.Series]) -> pd.Series:
    return _aggregate(components, ["us_m2", "pboc_m2"], "global_m2")


def build_global_balance_sheet(components: dict[str, pd.Series]) -> pd.Series:
    return _aggregate(components, ["fed_bs", "ecb_bs", "boj_bs"], "global_balance_sheet")


def build_global_liquidity_composite(components: dict[str, pd.Series]) -> pd.Series:
    return _aggregate(components, list(components.keys()), "global_liquidity_composite")


def get_sources_metadata(components: dict[str, pd.Series]) -> tuple[list[str], list[str]]:
    included = [k for k in config.COMPOSITE_COMPONENTS if k in components and not components[k].empty]
    missing = [k for k in config.COMPOSITE_COMPONENTS if k not in included]
    return included, missing
