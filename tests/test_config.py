"""Tests for config.py — must pass immediately in Phase 0."""

from pathlib import Path

import config


def test_root_dir_exists():
    assert config.ROOT_DIR.exists()


def test_artifacts_dir_defined():
    assert isinstance(config.ARTIFACTS_DIR, Path)


def test_cache_dir_defined():
    assert isinstance(config.CACHE_DIR, Path)


def test_data_start_date():
    assert config.DATA_START_DATE == "2006-01-01"


def test_cache_ttl():
    assert config.CACHE_TTL_DAYS == 7
    assert config.CACHE_TTL_SECONDS == 7 * 86400


def test_signal_stale_after_days():
    assert config.SIGNAL_STALE_AFTER_DAYS == 14


def test_fred_series_ids():
    assert config.FRED_SERIES["us_m2"] == "M2SL"
    assert config.FRED_SERIES["fed_bs"] == "WALCL"
    assert config.FRED_SERIES["pboc_m2"] == "MYAGM2CNM189N"
    assert config.FRED_SERIES["ecb_bs"] == "ECBASSETSW"
    assert config.FRED_SERIES["boj_bs"] == "JPNASSETS"
    assert config.FRED_SERIES["fx_eurusd"] == "DEXUSEU"
    assert config.FRED_SERIES["fx_jpyusd"] == "DEXJPUS"
    assert config.FRED_SERIES["fx_cnyusd"] == "DEXCHUS"


def test_fallback_fx():
    assert config.FALLBACK_FX["EURUSD"] == 1.08
    assert config.FALLBACK_FX["JPYUSD"] == 0.0067
    assert config.FALLBACK_FX["CNYUSD"] == 0.14


def test_regime_thresholds():
    assert config.REGIME_THRESHOLDS["EXPANDING"] == 0.01
    assert config.REGIME_THRESHOLDS["CONTRACTING"] == -0.005


def test_schema_version():
    assert config.SCHEMA_VERSION == "1.0.0"


def test_composite_components():
    assert "us_m2" in config.COMPOSITE_COMPONENTS
    assert "boj_bs" in config.COMPOSITE_COMPONENTS
    assert len(config.COMPOSITE_COMPONENTS) == 5
