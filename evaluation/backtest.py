"""Backtest framework for regime-based strategies and baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simple_regime_backtest(
    returns: pd.Series,
    regimes: pd.Series,
) -> pd.DataFrame:
    """Backtest: hold during EXPANDING, flat otherwise."""
    if returns.empty or regimes.empty:
        return pd.DataFrame(columns=["date", "regime", "return", "cumulative"])

    aligned = pd.DataFrame({"return": returns, "regime": regimes}).dropna()
    aligned["cumulative"] = (1 + aligned["return"]).cumprod()
    return aligned.reset_index().rename(columns={"index": "date"})


def buy_and_hold(returns: pd.Series) -> pd.Series:
    """Buy-and-hold cumulative return."""
    if returns.empty:
        return pd.Series(dtype=float, name="buy_and_hold")
    result = (1 + returns).cumprod()
    result.name = "buy_and_hold"
    return result


def momentum_3m_strategy(returns: pd.Series) -> pd.Series:
    """Simple 3-month BTC momentum: hold when trailing 3m return > 0."""
    if returns.empty:
        return pd.Series(dtype=float, name="momentum_3m")
    trailing = returns.rolling(3).sum().shift(1)
    signal = (trailing > 0).astype(float)
    result = returns * signal
    result.name = "momentum_3m"
    return result
