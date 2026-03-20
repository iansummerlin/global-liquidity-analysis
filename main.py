"""Main entry point: fetch, process, export artifact, and run evaluation."""

from __future__ import annotations

import json
import logging
import sys

import pandas as pd

from data.pipeline import fetch_and_validate, report_sources
from data.btc import load_btc_monthly_returns
from features.normalisation import normalize_component
from features.aggregation import (
    build_global_m2,
    build_global_balance_sheet,
    build_global_liquidity_composite,
    get_sources_metadata,
)
from features.momentum import compute_momentum_features, classify_regime
from signals.export import build_artifact, export_artifact, validate_artifact_file
from evaluation.reporting import generate_evaluation_report
import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run() -> str:
    # Phase 1: fetch and validate source data
    raw = fetch_and_validate()
    logger.info("Source summary:\n%s", report_sources(raw))

    fx = raw.get("fx_rates")

    component_map = {
        "us_m2": (raw.get("us_m2"), config.SOURCE_COLUMNS["us_m2"]),
        "fed_bs": (raw.get("fed_bs"), config.SOURCE_COLUMNS["fed_bs"]),
        "pboc_m2": (raw.get("pboc_m2"), config.SOURCE_COLUMNS["pboc_m2"]),
        "ecb_bs": (raw.get("ecb_bs"), config.SOURCE_COLUMNS["ecb_bs"]),
        "boj_bs": (raw.get("boj_bs"), config.SOURCE_COLUMNS["boj_bs"]),
    }

    fx_map = {
        "pboc_m2": fx[config.SOURCE_COLUMNS["fx_cnyusd"]] if fx is not None and config.SOURCE_COLUMNS["fx_cnyusd"] in fx.columns else None,
        "ecb_bs": fx[config.SOURCE_COLUMNS["fx_eurusd"]] if fx is not None and config.SOURCE_COLUMNS["fx_eurusd"] in fx.columns else None,
        "boj_bs": fx[config.SOURCE_COLUMNS["fx_jpyusd"]] if fx is not None and config.SOURCE_COLUMNS["fx_jpyusd"] in fx.columns else None,
    }

    # Phase 2: normalize components to USD trillions (weekly series resampled to month-end)
    normalised = {}
    for name, (df, col) in component_map.items():
        if df is not None:
            normalised[name] = normalize_component(df, col, name, fx_series=fx_map.get(name))

    # Build all three aggregates
    global_m2 = build_global_m2(normalised)
    global_bs = build_global_balance_sheet(normalised)
    composite = build_global_liquidity_composite(normalised)

    sources_included, sources_missing = get_sources_metadata(normalised)
    logger.info("Sources included: %s", sources_included)
    logger.info("Sources missing: %s", sources_missing)

    if not composite.empty:
        logger.info("global_m2: %d months, latest=%.2f T USD", len(global_m2), global_m2.iloc[-1] if not global_m2.empty else 0)
        logger.info("global_balance_sheet: %d months, latest=%.2f T USD", len(global_bs), global_bs.iloc[-1] if not global_bs.empty else 0)
        logger.info("global_liquidity_composite: %d months, latest=%.2f T USD", len(composite), composite.iloc[-1])

    # Compute momentum features and regime classification
    momentum = compute_momentum_features(composite)
    regimes = classify_regime(momentum["m2_roc_3m"] if "m2_roc_3m" in momentum.columns else composite)

    if not regimes.empty:
        logger.info("Latest regime: %s", regimes.iloc[-1])

    # Export artifact
    artifact = build_artifact(
        composite=composite,
        momentum=momentum,
        regimes=regimes,
        components=normalised,
        sources_included=sources_included,
        sources_missing=sources_missing,
    )
    path = export_artifact(artifact)
    logger.info("Artifact exported to %s", path)

    # Validate the exported artifact
    errors = validate_artifact_file(path)
    if errors:
        logger.error("Artifact validation failed: %s", "; ".join(errors))
    else:
        logger.info("Artifact validation passed")

    return path


def validate() -> bool:
    """Validate the current artifact file. Returns True if valid."""
    errors = validate_artifact_file()
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    print(f"OK: {config.ARTIFACT_PATH} is valid (schema {config.SCHEMA_VERSION})")
    return True


def evaluate() -> str:
    """Run Phase 4 evaluation and generate report."""
    artifact_path = config.ARTIFACT_PATH
    if not artifact_path.exists():
        logger.error("Artifact not found at %s. Run 'make update' first.", artifact_path)
        return ""

    with open(artifact_path) as f:
        artifact = json.load(f)

    ts = artifact.get("time_series", [])
    sources_included = artifact.get("sources_included", [])
    sources_missing = artifact.get("sources_missing", [])

    if ts:
        ts_df = pd.DataFrame(ts)
        ts_df["date"] = pd.to_datetime(ts_df["date"], utc=True)
        ts_df = ts_df.set_index("date").sort_index()
        m2_roc_3m = ts_df["m2_roc_3m"].astype(float)
        regimes = ts_df["regime"]
    else:
        m2_roc_3m = pd.Series(dtype=float, name="m2_roc_3m")
        regimes = pd.Series(dtype=str, name="regime")

    btc_returns = load_btc_monthly_returns()

    report = generate_evaluation_report(
        m2_roc_3m=m2_roc_3m,
        btc_returns=btc_returns,
        regimes=regimes,
        sources_included=sources_included,
        sources_missing=sources_missing,
    )

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = str(config.EVAL_REPORT_PATH)
    with open(report_path, "w") as f:
        f.write(report)

    logger.info("Evaluation report written to %s", report_path)
    print(report)
    return report_path


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "evaluate":
        evaluate()
    else:
        run()
