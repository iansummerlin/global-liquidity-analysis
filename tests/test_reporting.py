"""Tests for evaluation/reporting.py — Phase 4 conclusion and report tests."""

import numpy as np
import pandas as pd

from evaluation.reporting import (
    classify_conclusion,
    generate_evaluation_report,
    CONCLUSION_USEFUL,
    CONCLUSION_CONTEXT,
    CONCLUSION_NOT_USEFUL,
    CONCLUSION_INSUFFICIENT,
)
import config


def _make_idx(n=36, start="2020-01-01"):
    return pd.date_range(start, periods=n, freq="ME", tz="UTC")


def _make_data(n=36, seed=42):
    rng = np.random.RandomState(seed)
    idx = _make_idx(n)
    roc = pd.Series(rng.normal(0.005, 0.01, n), index=idx, name="m2_roc_3m")
    btc = pd.Series(rng.normal(0.02, 0.10, n), index=idx, name="btc_return")
    cycle = ["EXPANDING", "EXPANDING", "NEUTRAL", "CONTRACTING"] * (n // 4 + 1)
    regimes = pd.Series(cycle[:n], index=idx, name="regime")
    return roc, btc, regimes


# --- classify_conclusion ---

def test_conclusion_insufficient_data():
    ll = pd.DataFrame(columns=["lag", "ttest_p", "mean_expanding", "mean_contracting"])
    rs = pd.DataFrame(columns=["mean", "n_months"])
    result = classify_conclusion(ll, rs, n_overlap=5)
    assert result == CONCLUSION_INSUFFICIENT


def test_conclusion_significant_useful():
    """Significant Bonferroni-corrected result with correct direction."""
    # Create a lead-lag df with very low p-value (will survive correction)
    ll = pd.DataFrame([{
        "lag": 0,
        "pearson_r": 0.3,
        "pearson_p": 0.001,
        "mean_expanding": 0.05,
        "mean_contracting": -0.02,
        "ttest_p": 0.001,  # 0.001 * 10 lags = 0.01 < 0.05
        "n_overlap": 50,
    }])
    rs = pd.DataFrame({
        "mean": [0.05, 0.01, -0.02],
    }, index=pd.Index(["EXPANDING", "NEUTRAL", "CONTRACTING"], name="regime"))
    result = classify_conclusion(ll, rs, n_overlap=50)
    assert result == CONCLUSION_USEFUL


def test_conclusion_context_only():
    """Directionally consistent but not significant after Bonferroni."""
    ll = pd.DataFrame([{
        "lag": 0,
        "pearson_r": 0.1,
        "pearson_p": 0.3,
        "mean_expanding": 0.03,
        "mean_contracting": 0.01,
        "ttest_p": 0.08,  # 0.08 * 10 = 0.80, not significant
        "n_overlap": 30,
    }])
    rs = pd.DataFrame({
        "mean": [0.03, 0.02, 0.01],
    }, index=pd.Index(["EXPANDING", "NEUTRAL", "CONTRACTING"], name="regime"))
    result = classify_conclusion(ll, rs, n_overlap=30)
    assert result == CONCLUSION_CONTEXT


def test_conclusion_not_useful():
    """No directional consistency."""
    ll = pd.DataFrame([{
        "lag": 0,
        "pearson_r": -0.05,
        "pearson_p": 0.7,
        "mean_expanding": -0.01,
        "mean_contracting": 0.03,
        "ttest_p": 0.5,
        "n_overlap": 30,
    }])
    rs = pd.DataFrame({
        "mean": [-0.01, 0.02, 0.03],
    }, index=pd.Index(["EXPANDING", "NEUTRAL", "CONTRACTING"], name="regime"))
    result = classify_conclusion(ll, rs, n_overlap=30)
    assert result == CONCLUSION_NOT_USEFUL


def test_conclusion_not_useful_no_regimes():
    """No regime stats at all."""
    ll = pd.DataFrame(columns=["lag", "ttest_p", "mean_expanding", "mean_contracting"])
    rs = pd.DataFrame(columns=["mean", "n_months"])
    result = classify_conclusion(ll, rs, n_overlap=20)
    assert result == CONCLUSION_NOT_USEFUL


# --- generate_evaluation_report ---

def test_report_generation():
    roc, btc, regimes = _make_data()
    report = generate_evaluation_report(
        m2_roc_3m=roc,
        btc_returns=btc,
        regimes=regimes,
        sources_included=["us_m2", "fed_bs"],
        sources_missing=["boj_bs"],
    )
    assert "# Global Liquidity Evaluation Report" in report
    assert "## Conclusion" in report
    assert any(c in report for c in [
        CONCLUSION_USEFUL, CONCLUSION_CONTEXT,
        CONCLUSION_NOT_USEFUL, CONCLUSION_INSUFFICIENT,
    ])


def test_report_with_insufficient_data():
    roc = pd.Series(dtype=float, name="m2_roc_3m")
    btc = pd.Series(dtype=float, name="btc_return")
    regimes = pd.Series(dtype=str, name="regime")
    report = generate_evaluation_report(
        m2_roc_3m=roc,
        btc_returns=btc,
        regimes=regimes,
        sources_included=[],
        sources_missing=config.COMPOSITE_COMPONENTS,
    )
    assert CONCLUSION_INSUFFICIENT in report


def test_report_contains_sections():
    roc, btc, regimes = _make_data()
    report = generate_evaluation_report(
        m2_roc_3m=roc,
        btc_returns=btc,
        regimes=regimes,
        sources_included=["us_m2"],
        sources_missing=["boj_bs"],
    )
    assert "## Data Overview" in report
    assert "## Regime-Conditional BTC Returns" in report
    assert "## Lead-Lag Analysis" in report
    assert "## Halving-Era Analysis" in report
    assert "## Conclusion" in report


def test_report_mentions_missing_sources():
    roc, btc, regimes = _make_data()
    report = generate_evaluation_report(
        m2_roc_3m=roc,
        btc_returns=btc,
        regimes=regimes,
        sources_included=["us_m2"],
        sources_missing=["boj_bs", "ecb_bs"],
    )
    assert "boj_bs" in report
    assert "Data limitation" in report
