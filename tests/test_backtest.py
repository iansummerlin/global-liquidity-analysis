"""Tests for evaluation/backtest.py — Phase 4 tests."""

import numpy as np
import pandas as pd

from evaluation.backtest import simple_regime_backtest, buy_and_hold, momentum_3m_strategy


def test_backtest_with_data():
    returns = pd.Series([0.05, -0.02, 0.03, -0.01])
    regimes = pd.Series(["EXPANDING", "CONTRACTING", "EXPANDING", "NEUTRAL"])
    result = simple_regime_backtest(returns, regimes)
    assert isinstance(result, pd.DataFrame)
    assert "cumulative" in result.columns
    assert "regime" in result.columns
    assert len(result) == 4


def test_backtest_empty():
    returns = pd.Series(dtype=float)
    regimes = pd.Series(dtype=str)
    result = simple_regime_backtest(returns, regimes)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_buy_and_hold():
    returns = pd.Series([0.10, -0.05, 0.03])
    result = buy_and_hold(returns)
    assert result.name == "buy_and_hold"
    assert len(result) == 3
    expected = (1 + returns).cumprod()
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_buy_and_hold_empty():
    result = buy_and_hold(pd.Series(dtype=float))
    assert result.empty


def test_momentum_3m_strategy():
    idx = pd.date_range("2020-01-01", periods=6, freq="ME")
    returns = pd.Series([0.10, 0.05, -0.02, 0.08, 0.03, -0.01], index=idx)
    result = momentum_3m_strategy(returns)
    assert result.name == "momentum_3m"
    assert len(result) == 6
    # First few should be 0 (no trailing 3m data yet)
    assert result.iloc[0] == 0.0


def test_momentum_3m_empty():
    result = momentum_3m_strategy(pd.Series(dtype=float))
    assert result.empty
