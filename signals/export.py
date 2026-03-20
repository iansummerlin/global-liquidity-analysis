"""Export liquidity regime artifact as JSON and validate against the PRD schema."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

import config


# --- Schema constants ---

REQUIRED_FIELDS = [
    "schema_version", "generated_at", "last_data_date", "data_lag_days",
    "regime", "m2_momentum_3m", "m2_momentum_1m", "m2_acceleration",
    "global_liquidity_latest_usd_trillions", "components",
    "sources_included", "sources_missing", "time_series",
    "is_stale", "stale_after_days",
]

VALID_REGIMES = {"EXPANDING", "NEUTRAL", "CONTRACTING"}

TIME_SERIES_REQUIRED_FIELDS = {"date", "global_liquidity_usd_t", "m2_roc_3m", "regime"}


# --- Validation ---

class ArtifactValidationError(Exception):
    """Raised when an artifact fails schema validation."""


def validate_artifact(artifact: dict) -> list[str]:
    """Validate an artifact dict against the PRD schema.

    Returns a list of error strings. Empty list means valid.
    """
    errors = []

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in artifact:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors  # remaining checks need fields to exist

    # schema_version
    if artifact["schema_version"] != config.SCHEMA_VERSION:
        errors.append(f"schema_version must be {config.SCHEMA_VERSION}, got {artifact['schema_version']}")

    # generated_at — must be valid ISO 8601 UTC
    try:
        dt = datetime.fromisoformat(artifact["generated_at"].replace("Z", "+00:00"))
        if dt.tzinfo is None:
            errors.append("generated_at must include UTC timezone")
    except (ValueError, TypeError, AttributeError):
        errors.append(f"generated_at is not valid ISO 8601: {artifact.get('generated_at')}")

    # data_lag_days — must be >= 0 or None (empty artifact)
    lag = artifact["data_lag_days"]
    if lag is not None and (not isinstance(lag, (int, float)) or lag < 0):
        errors.append(f"data_lag_days must be >= 0 or null, got {lag}")

    # regime
    if artifact["regime"] not in VALID_REGIMES:
        errors.append(f"regime must be one of {VALID_REGIMES}, got {artifact['regime']}")

    # numeric fields
    for field in ("m2_momentum_3m", "m2_momentum_1m", "m2_acceleration", "global_liquidity_latest_usd_trillions"):
        if not isinstance(artifact[field], (int, float)):
            errors.append(f"{field} must be numeric, got {type(artifact[field]).__name__}")

    # components
    if not isinstance(artifact["components"], dict):
        errors.append("components must be a dict")

    # sources_included / sources_missing
    if not isinstance(artifact["sources_included"], list):
        errors.append("sources_included must be a list")
    if not isinstance(artifact["sources_missing"], list):
        errors.append("sources_missing must be a list")

    # time_series entries
    if not isinstance(artifact["time_series"], list):
        errors.append("time_series must be a list")
    else:
        for i, entry in enumerate(artifact["time_series"]):
            missing = TIME_SERIES_REQUIRED_FIELDS - set(entry.keys())
            if missing:
                errors.append(f"time_series[{i}] missing fields: {missing}")
                break  # one example is enough
            if entry.get("regime") not in VALID_REGIMES:
                errors.append(f"time_series[{i}] invalid regime: {entry.get('regime')}")
                break

    # is_stale / stale_after_days
    if not isinstance(artifact["is_stale"], bool):
        errors.append(f"is_stale must be bool, got {type(artifact['is_stale']).__name__}")
    if not isinstance(artifact["stale_after_days"], (int, float)):
        errors.append(f"stale_after_days must be numeric, got {type(artifact['stale_after_days']).__name__}")

    return errors


def validate_artifact_strict(artifact: dict) -> None:
    """Validate and raise ArtifactValidationError if invalid."""
    errors = validate_artifact(artifact)
    if errors:
        raise ArtifactValidationError("; ".join(errors))


def validate_artifact_file(path: str | None = None) -> list[str]:
    """Load and validate an artifact JSON file. Returns list of errors."""
    fpath = path or str(config.ARTIFACT_PATH)
    try:
        with open(fpath) as f:
            artifact = json.load(f)
    except FileNotFoundError:
        return [f"artifact file not found: {fpath}"]
    except json.JSONDecodeError as e:
        return [f"artifact file is not valid JSON: {e}"]
    return validate_artifact(artifact)


# --- Build ---

def build_artifact(
    composite: pd.Series,
    momentum: pd.DataFrame,
    regimes: pd.Series,
    components: dict[str, pd.Series],
    sources_included: list[str],
    sources_missing: list[str],
) -> dict:
    if composite.empty:
        return _empty_artifact(sources_missing=config.COMPOSITE_COMPONENTS)

    last_date = composite.index[-1]
    now = datetime.now(timezone.utc)
    last_dt = last_date.to_pydatetime().replace(tzinfo=timezone.utc)
    lag_days = max(0, (now - last_dt).days)

    latest_regime = regimes.iloc[-1] if not regimes.empty else "NEUTRAL"
    m2_roc_3m = momentum["m2_roc_3m"].iloc[-1] if "m2_roc_3m" in momentum.columns and not momentum["m2_roc_3m"].dropna().empty else 0.0
    m2_roc_1m = momentum["m2_roc_1m"].iloc[-1] if "m2_roc_1m" in momentum.columns and not momentum["m2_roc_1m"].dropna().empty else 0.0
    m2_accel = momentum["m2_acceleration"].iloc[-1] if "m2_acceleration" in momentum.columns and not momentum["m2_acceleration"].dropna().empty else 0.0

    component_values = {}
    for name, series in components.items():
        if not series.empty:
            component_values[f"{name}_usd_trillions"] = round(float(series.iloc[-1]), 2)

    ts_data = []
    ts_df = pd.DataFrame({"global_liquidity_usd_t": composite})
    if "m2_roc_3m" in momentum.columns:
        ts_df["m2_roc_3m"] = momentum["m2_roc_3m"]
    ts_df["regime"] = regimes
    for dt, row in ts_df.dropna().iterrows():
        ts_data.append({
            "date": dt.strftime("%Y-%m-%d"),
            "global_liquidity_usd_t": round(float(row["global_liquidity_usd_t"]), 2),
            "m2_roc_3m": round(float(row.get("m2_roc_3m", 0)), 6),
            "regime": row["regime"],
        })

    is_stale = lag_days > config.SIGNAL_STALE_AFTER_DAYS

    return {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_data_date": last_date.strftime("%Y-%m-%d"),
        "data_lag_days": lag_days,
        "regime": latest_regime,
        "m2_momentum_3m": round(float(m2_roc_3m), 6),
        "m2_momentum_1m": round(float(m2_roc_1m), 6),
        "m2_acceleration": round(float(m2_accel), 6),
        "global_liquidity_latest_usd_trillions": round(float(composite.iloc[-1]), 2),
        "components": component_values,
        "sources_included": sources_included,
        "sources_missing": sources_missing,
        "time_series": ts_data,
        "is_stale": is_stale,
        "stale_after_days": config.SIGNAL_STALE_AFTER_DAYS,
    }


def _empty_artifact(sources_missing: list[str] | None = None) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_data_date": None,
        "data_lag_days": None,
        "regime": "NEUTRAL",
        "m2_momentum_3m": 0.0,
        "m2_momentum_1m": 0.0,
        "m2_acceleration": 0.0,
        "global_liquidity_latest_usd_trillions": 0.0,
        "components": {},
        "sources_included": [],
        "sources_missing": sources_missing or [],
        "time_series": [],
        "is_stale": True,
        "stale_after_days": config.SIGNAL_STALE_AFTER_DAYS,
    }


def export_artifact(artifact: dict, path: str | None = None) -> str:
    out = path or str(config.ARTIFACT_PATH)
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(artifact, f, indent=2)
    return out
