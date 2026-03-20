"""Evaluation report generation for Phase 4."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
from evaluation.regime import (
    regime_conditional_stats,
    unconditional_stats,
    lead_lag_analysis,
    apply_bonferroni,
    halving_era_split,
)
from evaluation.backtest import buy_and_hold, momentum_3m_strategy


# --- Conclusion logic ---

CONCLUSION_USEFUL = "incrementally useful"
CONCLUSION_CONTEXT = "useful as context only"
CONCLUSION_NOT_USEFUL = "not useful enough to integrate"
CONCLUSION_INSUFFICIENT = "insufficient data to evaluate"


def classify_conclusion(
    lead_lag_df: pd.DataFrame,
    regime_stats: pd.DataFrame,
    n_overlap: int,
) -> str:
    """Determine the evaluation conclusion from the evidence.

    Rules (applied honestly, never overclaiming):
    - If fewer than EVAL_MIN_MONTHS of overlap, return insufficient.
    - If any lag has Bonferroni-corrected t-test p < 0.05 AND expanding mean >
      contracting mean, return incrementally useful.
    - If regime stats show directionally consistent separation (expanding mean >
      contracting mean) but not statistically significant, return context only.
    - Otherwise, not useful.
    """
    if n_overlap < config.EVAL_MIN_MONTHS:
        return CONCLUSION_INSUFFICIENT

    # Check significance with Bonferroni correction
    if not lead_lag_df.empty and "ttest_p" in lead_lag_df.columns:
        raw_p = lead_lag_df["ttest_p"]
        corrected = apply_bonferroni(raw_p)
        significant = corrected < config.EVAL_SIGNIFICANCE_THRESHOLD

        for i, is_sig in significant.items():
            if is_sig:
                row = lead_lag_df.iloc[i]
                if (not np.isnan(row["mean_expanding"]) and
                    not np.isnan(row["mean_contracting"]) and
                    row["mean_expanding"] > row["mean_contracting"]):
                    return CONCLUSION_USEFUL

    # Check directional consistency without significance
    if not regime_stats.empty:
        has_exp = "EXPANDING" in regime_stats.index
        has_con = "CONTRACTING" in regime_stats.index
        if has_exp and has_con:
            if regime_stats.loc["EXPANDING", "mean"] > regime_stats.loc["CONTRACTING", "mean"]:
                return CONCLUSION_CONTEXT

    return CONCLUSION_NOT_USEFUL


# --- Report generation ---

def generate_evaluation_report(
    m2_roc_3m: pd.Series,
    btc_returns: pd.Series,
    regimes: pd.Series,
    sources_included: list[str],
    sources_missing: list[str],
) -> str:
    """Generate the full Phase 4 evaluation report as markdown."""
    lines = []
    lines.append("# Global Liquidity Evaluation Report")
    lines.append(f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    # Data overview
    lines.append("## Data Overview")
    lines.append("")
    lines.append(f"- Liquidity sources included: {sources_included}")
    lines.append(f"- Liquidity sources missing: {sources_missing}")
    lines.append(f"- Liquidity months: {len(m2_roc_3m.dropna())}")
    lines.append(f"- BTC return months: {len(btc_returns)}")

    # Align
    combined = pd.DataFrame({
        "m2_roc_3m": m2_roc_3m,
        "btc_return": btc_returns,
        "regime": regimes,
    }).dropna(subset=["m2_roc_3m", "btc_return"])
    n_overlap = len(combined)
    lines.append(f"- Overlapping months: {n_overlap}")

    if n_overlap > 0:
        lines.append(f"- Overlap period: {combined.index[0].strftime('%Y-%m')} to {combined.index[-1].strftime('%Y-%m')}")
    lines.append("")

    if n_overlap < config.EVAL_MIN_MONTHS:
        lines.append("## Conclusion")
        lines.append("")
        lines.append(f"**{CONCLUSION_INSUFFICIENT}**")
        lines.append("")
        lines.append(f"Only {n_overlap} months of overlapping data available "
                      f"(minimum required: {config.EVAL_MIN_MONTHS}). "
                      "Cannot produce a meaningful evaluation.")
        if sources_missing:
            lines.append(f"Missing sources ({sources_missing}) likely contribute to data gap.")
        return "\n".join(lines)

    btc_aligned = combined["btc_return"]
    roc_aligned = combined["m2_roc_3m"]
    reg_aligned = combined["regime"]

    # Regime-conditional stats
    lines.append("## Regime-Conditional BTC Returns")
    lines.append("")
    regime_stats = regime_conditional_stats(btc_aligned, reg_aligned)
    unc = unconditional_stats(btc_aligned)
    if not regime_stats.empty:
        lines.append(regime_stats.to_string())
    else:
        lines.append("No regime data available.")
    lines.append("")
    lines.append(f"Unconditional: mean={unc['mean']:.4f}, std={unc['std']:.4f}, "
                  f"sharpe={unc['sharpe']:.4f}, n={unc['n_months']}")
    lines.append("")

    # Baselines
    lines.append("## Baseline Comparisons")
    lines.append("")
    bh = buy_and_hold(btc_aligned)
    mom = momentum_3m_strategy(btc_aligned)
    if not bh.empty:
        lines.append(f"- Buy-and-hold final cumulative: {bh.iloc[-1]:.4f}")
    if not mom.empty:
        mom_total = (1 + mom).cumprod()
        lines.append(f"- 3-month momentum strategy final cumulative: {mom_total.iloc[-1]:.4f}")
    lines.append("")

    # Lead-lag analysis
    lines.append("## Lead-Lag Analysis")
    lines.append("")
    ll_df = lead_lag_analysis(roc_aligned, btc_aligned, reg_aligned)
    if not ll_df.empty:
        corrected_p = apply_bonferroni(ll_df["ttest_p"])
        ll_df["ttest_p_bonf"] = corrected_p
        display_cols = ["lag", "pearson_r", "pearson_p", "mean_expanding",
                        "mean_contracting", "ttest_p", "ttest_p_bonf", "n_overlap"]
        fmt = ll_df[display_cols].copy()
        for col in ["pearson_r", "pearson_p", "mean_expanding", "mean_contracting", "ttest_p", "ttest_p_bonf"]:
            fmt[col] = fmt[col].map(lambda x: f"{x:.4f}" if not np.isnan(x) else "N/A")
        lines.append(fmt.to_string(index=False))
    else:
        lines.append("No lead-lag data available.")
    lines.append("")

    n_lags = len(config.EVAL_LAGS)
    lines.append(f"Bonferroni correction applied: {n_lags} tests, "
                  f"adjusted threshold = {config.EVAL_SIGNIFICANCE_THRESHOLD / n_lags:.4f}")
    lines.append("")

    # Halving-era split
    lines.append("## Halving-Era Analysis")
    lines.append("")
    era_results = halving_era_split(btc_aligned, reg_aligned)
    era_labels = ["Pre-2012", "2012-2016", "2016-2020", "2020-2024", "Post-2024"]
    for i, (era_key, era_stats) in enumerate(era_results.items()):
        label = era_labels[i] if i < len(era_labels) else era_key
        lines.append(f"### {label}")
        lines.append("")
        if not era_stats.empty:
            lines.append(era_stats.to_string())
        else:
            lines.append("No data in this era.")
        lines.append("")

    if not era_results:
        lines.append("No halving-era data available.")
        lines.append("")

    # Conclusion
    conclusion = classify_conclusion(ll_df, regime_stats, n_overlap)
    lines.append("## Conclusion")
    lines.append("")
    lines.append(f"**{conclusion}**")
    lines.append("")

    if conclusion == CONCLUSION_USEFUL:
        lines.append("At least one lag shows statistically significant (Bonferroni-corrected) "
                      "separation between EXPANDING and CONTRACTING regime returns, "
                      "with EXPANDING outperforming as expected.")
    elif conclusion == CONCLUSION_CONTEXT:
        lines.append("Regime classification shows directionally consistent return separation "
                      "(EXPANDING > CONTRACTING) but the difference is not statistically "
                      "significant after Bonferroni correction. The signal may be useful as "
                      "qualitative context but should not be relied upon for trading decisions.")
    elif conclusion == CONCLUSION_NOT_USEFUL:
        lines.append("No consistent or significant relationship found between liquidity "
                      "regime and BTC returns. The signal does not appear incrementally useful.")

    if sources_missing:
        lines.append("")
        lines.append(f"**Data limitation:** sources missing: {sources_missing}. "
                      "Results may differ with complete source data.")

    return "\n".join(lines)
