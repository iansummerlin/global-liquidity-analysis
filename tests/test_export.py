"""Tests for signals/export.py — Phase 3 schema validation and export tests."""

import json
import copy

import pandas as pd

from signals.export import (
    build_artifact,
    _empty_artifact,
    export_artifact,
    validate_artifact,
    validate_artifact_strict,
    validate_artifact_file,
    ArtifactValidationError,
    REQUIRED_FIELDS,
    VALID_REGIMES,
    TIME_SERIES_REQUIRED_FIELDS,
)
import config


def _make_test_data():
    idx = pd.date_range("2024-01-01", periods=6, freq="ME", tz="UTC")
    composite = pd.Series([80.0, 80.5, 81.0, 81.5, 82.0, 82.5], index=idx, name="global_liquidity_composite")
    momentum = pd.DataFrame({
        "m2_roc_1m": composite.pct_change(1),
        "m2_roc_3m": composite.pct_change(3),
        "m2_acceleration": composite.pct_change(3).diff(1),
    }, index=idx)
    regimes = pd.Series(["NEUTRAL"] * 6, index=idx, name="regime")
    components = {
        "us_m2": pd.Series([21.0] * 6, index=idx, name="us_m2"),
        "fed_bs": pd.Series([7.0] * 6, index=idx, name="fed_bs"),
    }
    return composite, momentum, regimes, components


def _valid_artifact():
    composite, momentum, regimes, components = _make_test_data()
    return build_artifact(
        composite=composite,
        momentum=momentum,
        regimes=regimes,
        components=components,
        sources_included=["us_m2", "fed_bs"],
        sources_missing=["ecb_bs", "boj_bs", "pboc_m2"],
    )


# --- build_artifact ---

def test_build_artifact_with_data():
    artifact = _valid_artifact()
    for field in REQUIRED_FIELDS:
        assert field in artifact, f"Missing field: {field}"
    assert artifact["schema_version"] == "1.0.0"
    assert artifact["regime"] == "NEUTRAL"
    assert isinstance(artifact["data_lag_days"], int)
    assert isinstance(artifact["components"], dict)
    assert "us_m2_usd_trillions" in artifact["components"]
    assert artifact["sources_included"] == ["us_m2", "fed_bs"]
    assert "boj_bs" in artifact["sources_missing"]


def test_build_artifact_time_series_entries():
    artifact = _valid_artifact()
    ts = artifact["time_series"]
    assert len(ts) > 0
    for entry in ts:
        for field in TIME_SERIES_REQUIRED_FIELDS:
            assert field in entry, f"time_series entry missing: {field}"
        assert entry["regime"] in VALID_REGIMES


def test_build_artifact_empty_composite():
    empty = pd.Series(dtype=float, name="global_liquidity_composite")
    artifact = build_artifact(
        composite=empty,
        momentum=pd.DataFrame(),
        regimes=pd.Series(dtype=str),
        components={},
        sources_included=[],
        sources_missing=config.COMPOSITE_COMPONENTS,
    )
    for field in REQUIRED_FIELDS:
        assert field in artifact
    assert artifact["is_stale"] is True
    assert artifact["time_series"] == []


def test_build_artifact_staleness():
    artifact = _valid_artifact()
    # Data from 2024 is stale relative to now (2026)
    assert artifact["is_stale"] is True
    assert artifact["stale_after_days"] == config.SIGNAL_STALE_AFTER_DAYS


# --- _empty_artifact ---

def test_empty_artifact_schema():
    artifact = _empty_artifact()
    assert artifact["schema_version"] == "1.0.0"
    assert artifact["regime"] == "NEUTRAL"
    assert artifact["is_stale"] is True
    assert isinstance(artifact["sources_included"], list)
    assert isinstance(artifact["sources_missing"], list)
    assert isinstance(artifact["time_series"], list)
    for field in REQUIRED_FIELDS:
        assert field in artifact, f"Missing field: {field}"


def test_empty_artifact_validates():
    artifact = _empty_artifact()
    errors = validate_artifact(artifact)
    assert errors == [], f"Empty artifact should validate cleanly: {errors}"


# --- validate_artifact ---

def test_validate_valid_artifact():
    artifact = _valid_artifact()
    errors = validate_artifact(artifact)
    assert errors == []


def test_validate_missing_field():
    artifact = _valid_artifact()
    del artifact["regime"]
    errors = validate_artifact(artifact)
    assert any("missing required field" in e for e in errors)


def test_validate_wrong_schema_version():
    artifact = _valid_artifact()
    artifact["schema_version"] = "2.0.0"
    errors = validate_artifact(artifact)
    assert any("schema_version" in e for e in errors)


def test_validate_bad_generated_at():
    artifact = _valid_artifact()
    artifact["generated_at"] = "not-a-date"
    errors = validate_artifact(artifact)
    assert any("generated_at" in e for e in errors)


def test_validate_negative_data_lag():
    artifact = _valid_artifact()
    artifact["data_lag_days"] = -5
    errors = validate_artifact(artifact)
    assert any("data_lag_days" in e for e in errors)


def test_validate_null_data_lag_allowed():
    artifact = _empty_artifact()
    assert artifact["data_lag_days"] is None
    errors = validate_artifact(artifact)
    assert not any("data_lag_days" in e for e in errors)


def test_validate_invalid_regime():
    artifact = _valid_artifact()
    artifact["regime"] = "BULLISH"
    errors = validate_artifact(artifact)
    assert any("regime" in e for e in errors)


def test_validate_non_numeric_momentum():
    artifact = _valid_artifact()
    artifact["m2_momentum_3m"] = "high"
    errors = validate_artifact(artifact)
    assert any("m2_momentum_3m" in e for e in errors)


def test_validate_bad_time_series_entry():
    artifact = _valid_artifact()
    artifact["time_series"] = [{"date": "2024-01-31"}]  # missing fields
    errors = validate_artifact(artifact)
    assert any("time_series" in e for e in errors)


def test_validate_invalid_regime_in_time_series():
    artifact = _valid_artifact()
    if artifact["time_series"]:
        artifact["time_series"][0]["regime"] = "INVALID"
        errors = validate_artifact(artifact)
        assert any("time_series" in e for e in errors)


def test_validate_is_stale_not_bool():
    artifact = _valid_artifact()
    artifact["is_stale"] = 1
    errors = validate_artifact(artifact)
    assert any("is_stale" in e for e in errors)


def test_validate_components_not_dict():
    artifact = _valid_artifact()
    artifact["components"] = [1, 2, 3]
    errors = validate_artifact(artifact)
    assert any("components" in e for e in errors)


# --- validate_artifact_strict ---

def test_validate_strict_raises():
    artifact = _valid_artifact()
    del artifact["regime"]
    try:
        validate_artifact_strict(artifact)
        assert False, "Should have raised"
    except ArtifactValidationError:
        pass


def test_validate_strict_passes():
    artifact = _valid_artifact()
    validate_artifact_strict(artifact)  # should not raise


# --- validate_artifact_file ---

def test_validate_file_success(tmp_path):
    artifact = _valid_artifact()
    path = str(tmp_path / "test.json")
    with open(path, "w") as f:
        json.dump(artifact, f)
    errors = validate_artifact_file(path)
    assert errors == []


def test_validate_file_not_found(tmp_path):
    errors = validate_artifact_file(str(tmp_path / "nonexistent.json"))
    assert any("not found" in e for e in errors)


def test_validate_file_invalid_json(tmp_path):
    path = str(tmp_path / "bad.json")
    with open(path, "w") as f:
        f.write("{broken json")
    errors = validate_artifact_file(path)
    assert any("not valid JSON" in e for e in errors)


def test_validate_file_malformed_content(tmp_path):
    path = str(tmp_path / "bad_schema.json")
    with open(path, "w") as f:
        json.dump({"schema_version": "wrong"}, f)
    errors = validate_artifact_file(path)
    assert len(errors) > 0


# --- export_artifact ---

def test_export_artifact_writes_file(tmp_path):
    artifact = _empty_artifact()
    path = str(tmp_path / "test_artifact.json")
    result = export_artifact(artifact, path=path)
    assert result == path
    with open(path) as f:
        loaded = json.load(f)
    assert loaded["schema_version"] == "1.0.0"


def test_export_artifact_roundtrip_validates(tmp_path):
    artifact = _valid_artifact()
    path = str(tmp_path / "full_artifact.json")
    export_artifact(artifact, path=path)
    errors = validate_artifact_file(path)
    assert errors == []


# --- field types ---

def test_artifact_field_types():
    """Verify consumer-facing field types match expectations."""
    artifact = _valid_artifact()
    assert isinstance(artifact["schema_version"], str)
    assert isinstance(artifact["generated_at"], str)
    assert isinstance(artifact["last_data_date"], str)
    assert isinstance(artifact["data_lag_days"], int)
    assert isinstance(artifact["regime"], str)
    assert isinstance(artifact["m2_momentum_3m"], float)
    assert isinstance(artifact["m2_momentum_1m"], float)
    assert isinstance(artifact["m2_acceleration"], float)
    assert isinstance(artifact["global_liquidity_latest_usd_trillions"], float)
    assert isinstance(artifact["components"], dict)
    assert isinstance(artifact["sources_included"], list)
    assert isinstance(artifact["sources_missing"], list)
    assert isinstance(artifact["time_series"], list)
    assert isinstance(artifact["is_stale"], bool)
    assert isinstance(artifact["stale_after_days"], int)
