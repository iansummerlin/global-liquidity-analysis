"""Tests for features/aggregation.py — Phase 2 tests."""

import pandas as pd

from features.aggregation import (
    build_global_m2,
    build_global_balance_sheet,
    build_global_liquidity_composite,
    get_sources_metadata,
    _align_to_month_end,
)


def _make_series(name, values, freq="ME"):
    idx = pd.date_range("2024-01-01", periods=len(values), freq=freq)
    return pd.Series(values, index=idx, name=name)


# --- build_global_m2 ---

def test_build_global_m2():
    components = {
        "us_m2": _make_series("us_m2", [21.0, 21.1, 21.2]),
        "pboc_m2": _make_series("pboc_m2", [40.0, 40.5, 41.0]),
    }
    result = build_global_m2(components)
    assert result.name == "global_m2"
    assert len(result) == 3
    assert result.iloc[0] == 61.0


def test_build_global_m2_missing_pboc():
    components = {
        "us_m2": _make_series("us_m2", [21.0, 21.1]),
    }
    result = build_global_m2(components)
    assert result.name == "global_m2"
    assert len(result) == 2
    assert result.iloc[0] == 21.0


def test_build_global_m2_empty():
    result = build_global_m2({})
    assert result.empty
    assert result.name == "global_m2"


# --- build_global_balance_sheet ---

def test_build_global_balance_sheet():
    components = {
        "fed_bs": _make_series("fed_bs", [7.0, 7.1, 7.2]),
        "ecb_bs": _make_series("ecb_bs", [6.0, 6.1, 6.2]),
        "boj_bs": _make_series("boj_bs", [4.0, 4.1, 4.2]),
    }
    result = build_global_balance_sheet(components)
    assert result.name == "global_balance_sheet"
    assert len(result) == 3
    assert result.iloc[0] == 17.0


def test_build_global_balance_sheet_missing_boj():
    """BOJ stub returns empty — balance sheet should still work with Fed + ECB."""
    components = {
        "fed_bs": _make_series("fed_bs", [7.0, 7.1]),
        "ecb_bs": _make_series("ecb_bs", [6.0, 6.1]),
        "boj_bs": pd.Series(dtype=float, name="boj_bs"),
    }
    result = build_global_balance_sheet(components)
    assert result.name == "global_balance_sheet"
    assert len(result) == 2
    assert result.iloc[0] == 13.0


# --- build_global_liquidity_composite ---

def test_build_global_liquidity_composite():
    components = {
        "us_m2": _make_series("us_m2", [21.0]),
        "fed_bs": _make_series("fed_bs", [7.0]),
        "ecb_bs": _make_series("ecb_bs", [6.0]),
        "boj_bs": _make_series("boj_bs", [4.0]),
        "pboc_m2": _make_series("pboc_m2", [40.0]),
    }
    result = build_global_liquidity_composite(components)
    assert result.name == "global_liquidity_composite"
    assert result.iloc[0] == 78.0


def test_build_composite_empty():
    result = build_global_liquidity_composite({})
    assert result.empty
    assert result.name == "global_liquidity_composite"


def test_build_composite_partial_components():
    """Composite with only 2 of 5 components should still produce values."""
    components = {
        "us_m2": _make_series("us_m2", [21.0, 21.5]),
        "fed_bs": _make_series("fed_bs", [7.0, 7.1]),
    }
    result = build_global_liquidity_composite(components)
    assert len(result) == 2
    assert result.iloc[0] == 28.0


# --- month-end alignment ---

def test_align_to_month_end():
    components = {
        "a": _make_series("a", [1.0, 2.0, 3.0]),
        "b": _make_series("b", [10.0, 20.0, 30.0]),
    }
    aligned = _align_to_month_end(components)
    assert len(aligned) == 2
    for k, s in aligned.items():
        assert all(d.is_month_end for d in s.index)


def test_align_non_month_end_index():
    """Regression: real FRED data has first-of-month dates, not month-end.

    _align_to_month_end must handle to_period('M').to_timestamp('M') without
    raising ValueError on the 'ME' frequency string.
    """
    idx = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])
    components = {
        "a": pd.Series([1.0, 2.0, 3.0], index=idx, name="a"),
    }
    aligned = _align_to_month_end(components)
    assert len(aligned) == 1
    for s in aligned.values():
        assert all(d.is_month_end for d in s.index)


def test_align_empty():
    result = _align_to_month_end({})
    assert result == {}


# --- get_sources_metadata ---

def test_get_sources_metadata():
    components = {
        "us_m2": _make_series("us_m2", [21.0]),
        "fed_bs": _make_series("fed_bs", [7.0]),
    }
    included, missing = get_sources_metadata(components)
    assert "us_m2" in included
    assert "fed_bs" in included
    assert "boj_bs" in missing
    assert "ecb_bs" in missing
    assert "pboc_m2" in missing


def test_get_sources_metadata_all_present():
    components = {
        "us_m2": _make_series("us_m2", [21.0]),
        "fed_bs": _make_series("fed_bs", [7.0]),
        "ecb_bs": _make_series("ecb_bs", [6.0]),
        "boj_bs": _make_series("boj_bs", [4.0]),
        "pboc_m2": _make_series("pboc_m2", [40.0]),
    }
    included, missing = get_sources_metadata(components)
    assert len(included) == 5
    assert len(missing) == 0
