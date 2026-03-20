"""Integration test for the Phase 2 pipeline path using synthetic data."""

import pandas as pd
import numpy as np

from features.normalisation import normalize_component
from features.aggregation import (
    build_global_m2,
    build_global_balance_sheet,
    build_global_liquidity_composite,
    get_sources_metadata,
)
from features.momentum import compute_momentum_features, classify_regime
from signals.export import build_artifact
import config


def _synthetic_sources():
    """Build synthetic source data mimicking real structure."""
    n = 24
    idx_monthly = pd.date_range("2022-01-01", periods=n, freq="ME", tz="UTC")
    idx_weekly = pd.date_range("2022-01-07", periods=n * 4, freq="W", tz="UTC")

    return {
        "us_m2": pd.DataFrame({"us_m2": np.linspace(20000, 21500, n)}, index=idx_monthly),
        "fed_bs": pd.DataFrame({"fed_total_assets": np.linspace(7_000_000, 7_500_000, n * 4)}, index=idx_weekly),
        "pboc_m2": pd.DataFrame({"pboc_m2": np.linspace(180e12, 195e12, n)}, index=idx_monthly),
        "ecb_bs": pd.DataFrame({"ecb_total_assets": np.linspace(6_000_000, 6_200_000, n * 4)}, index=idx_weekly),
        "boj_bs": pd.DataFrame({"boj_total_assets": np.linspace(6_700_000, 6_900_000, n)}, index=idx_monthly),
        "fx_rates": pd.DataFrame({
            "eurusd": [1.08] * n,
            "jpyusd": [0.0067] * n,
            "cnyusd": [0.14] * n,
        }, index=idx_monthly),
    }


def test_full_pipeline_synthetic():
    raw = _synthetic_sources()
    fx = raw["fx_rates"]

    component_map = {
        "us_m2": (raw["us_m2"], "us_m2"),
        "fed_bs": (raw["fed_bs"], "fed_total_assets"),
        "pboc_m2": (raw["pboc_m2"], "pboc_m2"),
        "ecb_bs": (raw["ecb_bs"], "ecb_total_assets"),
        "boj_bs": (raw["boj_bs"], "boj_total_assets"),
    }
    fx_map = {
        "pboc_m2": fx["cnyusd"],
        "ecb_bs": fx["eurusd"],
        "boj_bs": fx["jpyusd"],
    }

    normalised = {}
    for name, (df, col) in component_map.items():
        normalised[name] = normalize_component(df, col, name, fx_series=fx_map.get(name))

    # Check all non-empty components are in USD trillions range
    for name in ["us_m2", "fed_bs", "pboc_m2", "ecb_bs", "boj_bs"]:
        s = normalised[name]
        assert not s.empty, f"{name} should not be empty"
        assert s.iloc[0] > 0.1, f"{name} value too small: {s.iloc[0]}"
        assert s.iloc[0] < 100, f"{name} value too large: {s.iloc[0]}"

    # Build aggregates
    global_m2 = build_global_m2(normalised)
    global_bs = build_global_balance_sheet(normalised)
    composite = build_global_liquidity_composite(normalised)

    assert not global_m2.empty
    assert not global_bs.empty
    assert not composite.empty

    # Composite should be sum of available components
    assert composite.iloc[0] > global_m2.iloc[0]
    assert composite.iloc[0] > global_bs.iloc[0]

    # Metadata
    included, missing = get_sources_metadata(normalised)
    assert len(included) == 5
    assert len(missing) == 0

    # Momentum features
    momentum = compute_momentum_features(composite)
    assert "m2_roc_3m" in momentum.columns
    assert len(momentum) == len(composite)

    # Regime classification
    regimes = classify_regime(momentum["m2_roc_3m"])
    assert len(regimes) == len(composite)
    valid_regimes = {"EXPANDING", "NEUTRAL", "CONTRACTING"}
    for r in regimes.dropna():
        assert r in valid_regimes

    # Artifact
    artifact = build_artifact(
        composite=composite,
        momentum=momentum,
        regimes=regimes,
        components=normalised,
        sources_included=included,
        sources_missing=missing,
    )
    assert artifact["schema_version"] == "1.0.0"
    assert artifact["global_liquidity_latest_usd_trillions"] > 0
    assert len(artifact["time_series"]) > 0
    assert artifact["sources_missing"] == []


def test_pipeline_all_empty():
    """Pipeline should handle all-empty source data gracefully."""
    normalised = {k: pd.Series(dtype=float, name=k) for k in config.COMPOSITE_COMPONENTS}
    composite = build_global_liquidity_composite(normalised)
    assert composite.empty

    momentum = compute_momentum_features(composite)
    assert momentum.empty

    included, missing = get_sources_metadata(normalised)
    assert len(included) == 0
    assert len(missing) == 5

    artifact = build_artifact(
        composite=composite,
        momentum=momentum,
        regimes=pd.Series(dtype=str),
        components=normalised,
        sources_included=included,
        sources_missing=missing,
    )
    assert artifact["is_stale"] is True
    assert artifact["time_series"] == []
