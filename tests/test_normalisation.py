"""Tests for features/normalisation.py."""

import pandas as pd
import numpy as np

from features.normalisation import (
    to_usd_trillions,
    resample_to_month_end,
    normalize_component,
    WEEKLY_COMPONENTS,
    SOURCE_DIVISOR,
)


def _make_df(col, values, freq="ME", start="2024-01-01", tz="UTC"):
    idx = pd.date_range(start, periods=len(values), freq=freq, tz=tz)
    return pd.DataFrame({col: values}, index=idx)


# --- to_usd_trillions ---

def test_to_usd_trillions_from_billions():
    s = pd.Series([1000.0, 2000.0])
    result = to_usd_trillions(s, fx_rate=1.0, divisor=1000.0)
    assert result.iloc[0] == 1.0
    assert result.iloc[1] == 2.0


def test_to_usd_trillions_from_millions():
    s = pd.Series([1_000_000.0])
    result = to_usd_trillions(s, fx_rate=1.0, divisor=1_000_000.0)
    assert result.iloc[0] == 1.0


def test_to_usd_trillions_with_fx():
    s = pd.Series([1000.0])
    result = to_usd_trillions(s, fx_rate=0.14, divisor=1000.0)
    assert abs(result.iloc[0] - 0.14) < 1e-6


# --- resample_to_month_end ---

def test_resample_weekly_to_month_end():
    idx = pd.date_range("2024-01-05", periods=8, freq="W", tz="UTC")
    s = pd.Series(range(1, 9), index=idx, dtype=float, name="test")
    result = resample_to_month_end(s)
    assert all(d.is_month_end for d in result.index)
    assert result.iloc[0] == 4.0


def test_resample_empty():
    s = pd.Series(dtype=float, name="test")
    result = resample_to_month_end(s)
    assert result.empty


# --- normalize_component ---

def test_normalize_component_empty():
    df = pd.DataFrame(columns=["us_m2"])
    df.index = pd.DatetimeIndex([], name="date")
    result = normalize_component(df, "us_m2", "us_m2")
    assert isinstance(result, pd.Series)
    assert result.empty


def test_normalize_us_m2():
    """US M2 is billions USD — divisor 1000 -> trillions."""
    df = _make_df("us_m2", [21000.0, 21100.0, 21200.0])
    result = normalize_component(df, "us_m2", "us_m2")
    assert result.name == "us_m2"
    assert len(result) == 3
    assert abs(result.iloc[0] - 21.0) < 1e-6


def test_normalize_fed_bs_weekly_resampled():
    """Fed BS is millions USD, weekly — divisor 1e6, resampled to month-end."""
    idx = pd.date_range("2024-01-05", periods=8, freq="W", tz="UTC")
    df = pd.DataFrame({"fed_total_assets": [7_000_000.0] * 8}, index=idx)
    result = normalize_component(df, "fed_total_assets", "fed_bs")
    assert result.name == "fed_bs"
    assert "fed_bs" in WEEKLY_COMPONENTS
    assert all(d.is_month_end for d in result.index)
    assert abs(result.iloc[0] - 7.0) < 1e-6


def test_normalize_pboc_m2_raw_cny():
    """PBoC M2 is raw CNY units — divisor 1e12 * FX -> USD trillions."""
    # ~190 trillion CNY
    value = 190_000_000_000_000.0
    df = _make_df("pboc_m2", [value])
    fx = pd.Series([0.14], index=df.index)
    result = normalize_component(df, "pboc_m2", "pboc_m2", fx_series=fx)
    expected = value * 0.14 / 1e12
    assert abs(result.iloc[0] - expected) < 0.01
    assert 20.0 < result.iloc[0] < 35.0  # sanity: ~26.6 T USD


def test_normalize_pboc_m2_fallback_fx():
    """PBoC M2 uses fallback FX when no fx_series provided."""
    value = 190e12
    df = _make_df("pboc_m2", [value])
    result = normalize_component(df, "pboc_m2", "pboc_m2")
    expected = value * 0.14 / 1e12
    assert abs(result.iloc[0] - expected) < 0.01


def test_normalize_ecb_bs_weekly_with_fx():
    """ECB BS is millions EUR, weekly — divisor 1e6, resampled."""
    idx = pd.date_range("2024-01-05", periods=8, freq="W", tz="UTC")
    df = pd.DataFrame({"ecb_total_assets": [6_000_000.0] * 8}, index=idx)
    fx = pd.Series([1.08] * 8, index=idx)
    result = normalize_component(df, "ecb_total_assets", "ecb_bs", fx_series=fx)
    assert "ecb_bs" in WEEKLY_COMPONENTS
    assert all(d.is_month_end for d in result.index)
    expected = 6_000_000.0 * 1.08 / 1_000_000.0
    assert abs(result.iloc[0] - expected) < 1e-6


def test_normalize_boj_bs():
    """BOJ BS is 100 million JPY — divisor 10000 * FX -> USD trillions."""
    # ~6.8 million in 100M JPY units = 680 trillion JPY
    value = 6_800_000.0
    df = _make_df("boj_total_assets", [value])
    fx = pd.Series([0.0067], index=df.index)
    result = normalize_component(df, "boj_total_assets", "boj_bs", fx_series=fx)
    expected = value * 0.0067 / 10_000.0
    assert abs(result.iloc[0] - expected) < 0.01
    assert 3.0 < result.iloc[0] < 7.0  # sanity: ~4.56 T USD


def test_normalize_missing_column():
    df = _make_df("wrong_col", [100.0])
    result = normalize_component(df, "us_m2", "us_m2")
    assert result.empty
    assert result.name == "us_m2"


def test_normalize_fed_bs_monthly_input_still_works():
    """If Fed data is already month-end, resampling should be a no-op."""
    df = _make_df("fed_total_assets", [7_400_000.0, 7_500_000.0])
    result = normalize_component(df, "fed_total_assets", "fed_bs")
    assert len(result) == 2
    assert abs(result.iloc[0] - 7.4) < 1e-6


def test_source_divisor_covers_all_components():
    """Every composite component has an explicit divisor."""
    import config
    for comp in config.COMPOSITE_COMPONENTS:
        assert comp in SOURCE_DIVISOR, f"Missing divisor for {comp}"
