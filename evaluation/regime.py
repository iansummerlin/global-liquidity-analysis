"""Regime-conditional return analysis and lead-lag evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import config


def regime_conditional_stats(
    returns: pd.Series,
    regimes: pd.Series,
) -> pd.DataFrame:
    """Compute per-regime return statistics."""
    if returns.empty or regimes.empty:
        return pd.DataFrame(
            columns=["mean", "median", "std", "sharpe", "hit_rate", "max_drawdown", "n_months"],
        )

    aligned = pd.DataFrame({"ret": returns, "regime": regimes}).dropna()
    results = []
    for regime in ["EXPANDING", "NEUTRAL", "CONTRACTING"]:
        subset = aligned[aligned["regime"] == regime]["ret"]
        if subset.empty:
            continue
        results.append(_compute_stats(subset, regime))
    return pd.DataFrame(results).set_index("regime") if results else pd.DataFrame(
        columns=["mean", "median", "std", "sharpe", "hit_rate", "max_drawdown", "n_months"],
    )


def unconditional_stats(returns: pd.Series) -> dict:
    """Compute unconditional return statistics (baseline)."""
    if returns.empty:
        return {"regime": "UNCONDITIONAL", "mean": 0, "median": 0, "std": 0,
                "sharpe": 0, "hit_rate": 0, "max_drawdown": 0, "n_months": 0}
    return _compute_stats(returns, "UNCONDITIONAL")


def _compute_stats(subset: pd.Series, label: str) -> dict:
    return {
        "regime": label,
        "mean": float(subset.mean()),
        "median": float(subset.median()),
        "std": float(subset.std()),
        "sharpe": float(subset.mean() / subset.std()) if subset.std() > 0 else 0.0,
        "hit_rate": float((subset > 0).mean()),
        "max_drawdown": float((subset.cumsum() - subset.cumsum().cummax()).min()),
        "n_months": len(subset),
    }


def lead_lag_analysis(
    m2_roc_3m: pd.Series,
    btc_returns: pd.Series,
    regimes: pd.Series,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """Evaluate lead-lag relationship between liquidity momentum and BTC returns.

    For each lag:
    - Pearson correlation between m2_roc_3m and BTC returns
    - Mean BTC return by regime (at that lag)
    - t-test p-value for EXPANDING vs CONTRACTING regime returns
    """
    if m2_roc_3m.empty or btc_returns.empty:
        return pd.DataFrame(columns=[
            "lag", "pearson_r", "pearson_p", "mean_expanding", "mean_contracting",
            "ttest_p", "n_overlap",
        ])

    lags = lags if lags is not None else config.EVAL_LAGS
    results = []

    for lag in lags:
        shifted_roc = m2_roc_3m.shift(lag)
        shifted_regimes = regimes.shift(lag)

        # Align
        combined = pd.DataFrame({
            "roc": shifted_roc,
            "regime": shifted_regimes,
            "btc": btc_returns,
        }).dropna(subset=["roc", "btc"])

        n = len(combined)
        if n < 3:
            results.append(_empty_lag_result(lag, n))
            continue

        r, p = stats.pearsonr(combined["roc"], combined["btc"])

        combined_with_regime = combined.dropna(subset=["regime"])
        exp_ret = combined_with_regime[combined_with_regime["regime"] == "EXPANDING"]["btc"]
        con_ret = combined_with_regime[combined_with_regime["regime"] == "CONTRACTING"]["btc"]

        mean_exp = float(exp_ret.mean()) if len(exp_ret) > 0 else float("nan")
        mean_con = float(con_ret.mean()) if len(con_ret) > 0 else float("nan")

        if len(exp_ret) >= 2 and len(con_ret) >= 2:
            _, ttest_p = stats.ttest_ind(exp_ret, con_ret, equal_var=False)
        else:
            ttest_p = float("nan")

        results.append({
            "lag": lag,
            "pearson_r": float(r),
            "pearson_p": float(p),
            "mean_expanding": mean_exp,
            "mean_contracting": mean_con,
            "ttest_p": float(ttest_p),
            "n_overlap": n,
        })

    return pd.DataFrame(results)


def _empty_lag_result(lag: int, n: int) -> dict:
    return {
        "lag": lag,
        "pearson_r": float("nan"),
        "pearson_p": float("nan"),
        "mean_expanding": float("nan"),
        "mean_contracting": float("nan"),
        "ttest_p": float("nan"),
        "n_overlap": n,
    }


def apply_bonferroni(p_values: pd.Series, threshold: float | None = None) -> pd.Series:
    """Apply Bonferroni correction. Returns adjusted p-values."""
    alpha = threshold or config.EVAL_SIGNIFICANCE_THRESHOLD
    n_tests = len(p_values.dropna())
    if n_tests == 0:
        return p_values
    adjusted = p_values * n_tests
    return adjusted.clip(upper=1.0)


def halving_era_split(
    returns: pd.Series,
    regimes: pd.Series,
    halving_dates: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Split regime stats by halving era."""
    dates = [pd.Timestamp(d, tz="UTC") for d in (halving_dates or config.HALVING_DATES)]

    boundaries = [pd.Timestamp("2009-01-01", tz="UTC")] + dates + [pd.Timestamp.now(tz="UTC")]
    era_names = [f"era_{i}" for i in range(len(boundaries) - 1)]

    aligned = pd.DataFrame({"ret": returns, "regime": regimes}).dropna()
    if aligned.empty:
        return {}

    if aligned.index.tz is None:
        aligned.index = aligned.index.tz_localize("UTC")

    results = {}
    for i, name in enumerate(era_names):
        mask = (aligned.index >= boundaries[i]) & (aligned.index < boundaries[i + 1])
        era_data = aligned[mask]
        if era_data.empty:
            continue
        era_stats = regime_conditional_stats(era_data["ret"], era_data["regime"])
        if not era_stats.empty:
            results[name] = era_stats

    return results
