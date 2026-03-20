"""Tests for features/momentum.py — Phase 2 tests."""

import pandas as pd
import numpy as np

from features.momentum import compute_momentum_features, classify_regime


def _make_composite(n=24):
    idx = pd.date_range("2022-01-01", periods=n, freq="ME")
    values = [80.0 + i * 0.5 for i in range(n)]
    return pd.Series(values, index=idx, name="global_liquidity_composite")


# --- compute_momentum_features ---

def test_momentum_columns():
    composite = _make_composite()
    result = compute_momentum_features(composite)
    expected = ["m2_roc_1m", "m2_roc_3m", "m2_roc_6m", "m2_acceleration", "m2_zscore_12m", "m2_trend"]
    for col in expected:
        assert col in result.columns


def test_momentum_empty():
    empty = pd.Series(dtype=float, name="global_liquidity_composite")
    result = compute_momentum_features(empty)
    assert result.empty


def test_momentum_index_preserved():
    composite = _make_composite()
    result = compute_momentum_features(composite)
    assert (result.index == composite.index).all()


def test_momentum_roc_1m_formula():
    """m2_roc_1m = composite.pct_change(1)"""
    composite = _make_composite(6)
    result = compute_momentum_features(composite)
    expected = composite.pct_change(1)
    pd.testing.assert_series_equal(result["m2_roc_1m"], expected, check_names=False)


def test_momentum_roc_3m_formula():
    """m2_roc_3m = composite.pct_change(3)"""
    composite = _make_composite(6)
    result = compute_momentum_features(composite)
    expected = composite.pct_change(3)
    pd.testing.assert_series_equal(result["m2_roc_3m"], expected, check_names=False)


def test_momentum_acceleration_formula():
    """m2_acceleration = m2_roc_3m.diff(1)"""
    composite = _make_composite(6)
    result = compute_momentum_features(composite)
    expected = composite.pct_change(3).diff(1)
    pd.testing.assert_series_equal(result["m2_acceleration"], expected, check_names=False)


def test_momentum_zscore_formula():
    """m2_zscore_12m uses trailing 12-month rolling mean/std on m2_roc_3m."""
    composite = _make_composite(24)
    result = compute_momentum_features(composite)
    roc3 = composite.pct_change(3)
    rm = roc3.rolling(12).mean()
    rs = roc3.rolling(12).std()
    expected = (roc3 - rm) / rs
    pd.testing.assert_series_equal(result["m2_zscore_12m"], expected, check_names=False)


def test_momentum_trend_formula():
    """m2_trend = sign(m2_roc_3m.rolling(3).mean())"""
    composite = _make_composite(12)
    result = compute_momentum_features(composite)
    expected = np.sign(composite.pct_change(3).rolling(3).mean())
    pd.testing.assert_series_equal(result["m2_trend"], expected, check_names=False)


# --- classify_regime ---

def test_classify_regime():
    roc = pd.Series([0.02, 0.005, -0.01, 0.0], name="m2_roc_3m")
    result = classify_regime(roc)
    assert result.iloc[0] == "EXPANDING"
    assert result.iloc[1] == "NEUTRAL"
    assert result.iloc[2] == "CONTRACTING"
    assert result.iloc[3] == "NEUTRAL"


def test_classify_regime_empty():
    empty = pd.Series(dtype=float, name="m2_roc_3m")
    result = classify_regime(empty)
    assert result.empty


def test_classify_regime_boundary_values():
    """Test exact boundary values: 0.01 is NOT expanding, -0.005 is NOT contracting."""
    roc = pd.Series([0.01, -0.005, 0.0100001, -0.0050001])
    result = classify_regime(roc)
    assert result.iloc[0] == "NEUTRAL"    # exactly 0.01 is not > 0.01
    assert result.iloc[1] == "NEUTRAL"    # exactly -0.005 is not < -0.005
    assert result.iloc[2] == "EXPANDING"  # just above
    assert result.iloc[3] == "CONTRACTING"  # just below
