"""Normalize source series into USD trillions."""

from __future__ import annotations

import pandas as pd

import config

# Components with weekly source frequency that need month-end resampling.
WEEKLY_COMPONENTS = {"fed_bs", "ecb_bs"}

# Divisor to convert source units to trillions in local currency.
# value_in_trillions = raw_value / SOURCE_DIVISOR[component]
SOURCE_DIVISOR = {
    "us_m2": 1_000.0,           # Billions USD -> trillions
    "fed_bs": 1_000_000.0,      # Millions USD -> trillions
    "pboc_m2": 1e12,            # Units CNY -> trillions
    "ecb_bs": 1_000_000.0,      # Millions EUR -> trillions
    "boj_bs": 10_000.0,         # 100 Million JPY -> trillions (1e8 units, /1e4 = trillions)
}


def to_usd_trillions(
    series: pd.Series,
    fx_rate: float | pd.Series = 1.0,
    divisor: float = 1_000.0,
) -> pd.Series:
    return (series * fx_rate) / divisor


def resample_to_month_end(series: pd.Series) -> pd.Series:
    """Resample a higher-frequency series to month-end using last observation."""
    if series.empty:
        return series
    result = series.resample("ME").last().dropna()
    result.name = series.name
    return result


def normalize_component(
    df: pd.DataFrame,
    col: str,
    component: str,
    fx_series: pd.Series | None = None,
) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype=float, name=component)

    s = df[col].astype(float)

    fallback_fx = {
        "us_m2": 1.0,
        "fed_bs": 1.0,
        "pboc_m2": config.FALLBACK_FX["CNYUSD"],
        "ecb_bs": config.FALLBACK_FX["EURUSD"],
        "boj_bs": config.FALLBACK_FX["JPYUSD"],
    }

    fallback_rate = fallback_fx.get(component, 1.0)
    divisor = SOURCE_DIVISOR.get(component, 1_000.0)

    if fx_series is not None and not fx_series.empty:
        fx = fx_series.reindex(s.index, method="ffill").fillna(fallback_rate)
    else:
        fx = fallback_rate

    result = to_usd_trillions(s, fx_rate=fx, divisor=divisor)
    result.name = component

    # Resample weekly sources to month-end after conversion.
    if component in WEEKLY_COMPONENTS:
        result = resample_to_month_end(result)

    return result
