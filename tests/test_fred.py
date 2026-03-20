"""Tests for data/fred.py — Phase 1 tests with mocked API."""

from unittest.mock import patch, MagicMock

import pandas as pd

import config
from data.fred import (
    fetch_us_m2, fetch_fed_balance_sheet, fetch_pboc_m2, fetch_fx_rates,
    _empty_frame, _fetch_fred_series,
)


def _mock_fred_response(values):
    obs = [{"date": f"2024-{i+1:02d}-01", "value": str(v)} for i, v in enumerate(values)]
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"observations": obs}
    resp.raise_for_status = MagicMock()
    return resp


def test_empty_frame_schema():
    df = _empty_frame("us_m2")
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert "us_m2" in df.columns
    assert df.index.tz is not None


def test_fetch_us_m2_returns_correct_column(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", return_value=_mock_fred_response([21000, 21100, 21200])):
        df = fetch_us_m2()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "us_m2" in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None


def test_fetch_fed_bs_returns_correct_column(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", return_value=_mock_fred_response([7400000, 7500000])):
        df = fetch_fed_balance_sheet()
    assert "fed_total_assets" in df.columns
    assert len(df) == 2


def test_fetch_pboc_m2_returns_correct_column(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", return_value=_mock_fred_response([290000, 295000])):
        df = fetch_pboc_m2()
    assert "pboc_m2" in df.columns
    assert len(df) == 2


def test_fetch_us_m2_fallback_on_failure(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", side_effect=Exception("network error")):
        df = fetch_us_m2()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert "us_m2" in df.columns


def test_stale_cache_fallback(tmp_path, monkeypatch):
    import data.cache as cm
    import json
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    # First: populate cache via successful fetch
    with patch("data.fred.requests.get", return_value=_mock_fred_response([21000, 21100])):
        df1 = fetch_us_m2()
    assert len(df1) == 2

    # Expire the cache
    meta_path = tmp_path / "fred" / "M2SL.meta"
    meta = json.loads(meta_path.read_text())
    meta["written_at"] = 0
    meta_path.write_text(json.dumps(meta))

    # Second: fetch fails, should fall back to stale
    with patch("data.fred.requests.get", side_effect=Exception("network error")):
        df2 = fetch_us_m2()
    assert len(df2) == 2
    assert "us_m2" in df2.columns


def test_fred_skips_dot_values(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    obs = [
        {"date": "2024-01-01", "value": "21000"},
        {"date": "2024-02-01", "value": "."},
        {"date": "2024-03-01", "value": "21200"},
    ]
    resp = MagicMock()
    resp.json.return_value = {"observations": obs}
    resp.raise_for_status = MagicMock()

    with patch("data.fred.requests.get", return_value=resp):
        df = fetch_us_m2()
    assert len(df) == 2


def test_fetch_fx_rates_returns_named_columns(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", return_value=_mock_fred_response([1.08, 1.09])):
        df = fetch_fx_rates()
    assert isinstance(df, pd.DataFrame)
    # At least one FX column present
    fx_cols = {"eurusd", "jpyusd", "cnyusd"}
    assert len(fx_cols & set(df.columns)) > 0


def test_no_api_key_returns_empty(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr("data.fred.config.FRED_API_KEY", "")

    df = fetch_us_m2()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
