"""Tests for evaluation/regime.py — Phase 4 evaluation tests."""

import numpy as np
import pandas as pd
import pytest

from evaluation.regime import (
    regime_conditional_stats,
    unconditional_stats,
    lead_lag_analysis,
    apply_bonferroni,
    halving_era_split,
)


def _make_idx(n=24, start="2020-01-01"):
    return pd.date_range(start, periods=n, freq="ME", tz="UTC")


def _make_returns(n=24, seed=42):
    rng = np.random.RandomState(seed)
    idx = _make_idx(n)
    return pd.Series(rng.normal(0.02, 0.10, n), index=idx, name="btc_return")


def _make_regimes(n=24):
    idx = _make_idx(n)
    cycle = ["EXPANDING", "EXPANDING", "NEUTRAL", "CONTRACTING"] * (n // 4 + 1)
    return pd.Series(cycle[:n], index=idx, name="regime")


def _make_roc(n=24, seed=42):
    rng = np.random.RandomState(seed)
    idx = _make_idx(n)
    return pd.Series(rng.normal(0.005, 0.01, n), index=idx, name="m2_roc_3m")


# --- regime_conditional_stats ---

def test_regime_stats_with_data():
    returns = pd.Series([0.05, -0.02, 0.03, -0.01, 0.04, 0.01])
    regimes = pd.Series(["EXPANDING", "EXPANDING", "NEUTRAL", "CONTRACTING", "EXPANDING", "NEUTRAL"])
    result = regime_conditional_stats(returns, regimes)
    assert isinstance(result, pd.DataFrame)
    assert "mean" in result.columns
    assert "n_months" in result.columns
    assert "EXPANDING" in result.index


def test_regime_stats_empty():
    returns = pd.Series(dtype=float)
    regimes = pd.Series(dtype=str)
    result = regime_conditional_stats(returns, regimes)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_regime_stats_all_columns():
    returns = _make_returns()
    regimes = _make_regimes()
    result = regime_conditional_stats(returns, regimes)
    for col in ["mean", "median", "std", "sharpe", "hit_rate", "max_drawdown", "n_months"]:
        assert col in result.columns


# --- unconditional_stats ---

def test_unconditional_stats():
    returns = _make_returns()
    result = unconditional_stats(returns)
    assert result["regime"] == "UNCONDITIONAL"
    assert result["n_months"] == 24
    assert isinstance(result["mean"], float)


def test_unconditional_stats_empty():
    result = unconditional_stats(pd.Series(dtype=float))
    assert result["n_months"] == 0


# --- lead_lag_analysis ---

def test_lead_lag_basic():
    roc = _make_roc()
    btc = _make_returns()
    reg = _make_regimes()
    result = lead_lag_analysis(roc, btc, reg)
    assert isinstance(result, pd.DataFrame)
    assert "lag" in result.columns
    assert "pearson_r" in result.columns
    assert "ttest_p" in result.columns
    assert len(result) == 10  # -6 to +3


def test_lead_lag_empty():
    empty = pd.Series(dtype=float)
    result = lead_lag_analysis(empty, empty, pd.Series(dtype=str))
    assert result.empty


def test_lead_lag_custom_lags():
    roc = _make_roc()
    btc = _make_returns()
    reg = _make_regimes()
    result = lead_lag_analysis(roc, btc, reg, lags=[0, 1])
    assert len(result) == 2


def test_lead_lag_n_overlap():
    roc = _make_roc()
    btc = _make_returns()
    reg = _make_regimes()
    result = lead_lag_analysis(roc, btc, reg, lags=[0])
    assert result.iloc[0]["n_overlap"] > 0


# --- apply_bonferroni ---

def test_bonferroni_correction():
    p = pd.Series([0.01, 0.04, 0.10])
    corrected = apply_bonferroni(p, threshold=0.05)
    assert abs(corrected.iloc[0] - 0.03) < 1e-10
    assert abs(corrected.iloc[1] - 0.12) < 1e-10
    assert abs(corrected.iloc[2] - 0.30) < 1e-10


def test_bonferroni_clips_at_1():
    p = pd.Series([0.5, 0.8])
    corrected = apply_bonferroni(p)
    assert corrected.iloc[0] == 1.0
    assert corrected.iloc[1] == 1.0


def test_bonferroni_with_nan():
    p = pd.Series([0.01, float("nan"), 0.04])
    corrected = apply_bonferroni(p)
    assert corrected.iloc[0] == 0.02  # 0.01 * 2 (only 2 non-nan)
    assert np.isnan(corrected.iloc[1])


def test_bonferroni_empty():
    p = pd.Series(dtype=float)
    corrected = apply_bonferroni(p)
    assert corrected.empty


# --- halving_era_split ---

def test_halving_era_split():
    idx = pd.date_range("2015-01-01", periods=60, freq="ME", tz="UTC")
    returns = pd.Series(np.random.RandomState(42).normal(0.02, 0.1, 60), index=idx)
    regimes = pd.Series(["EXPANDING"] * 30 + ["CONTRACTING"] * 30, index=idx)
    result = halving_era_split(returns, regimes)
    assert isinstance(result, dict)
    assert len(result) > 0


def test_halving_era_split_empty():
    result = halving_era_split(pd.Series(dtype=float), pd.Series(dtype=str))
    assert result == {}
