"""Tests for data/boj.py — BOJ total assets via FRED JPNASSETS."""

from unittest.mock import patch, MagicMock

import pandas as pd

from data.boj import fetch_boj_balance_sheet
import config


def test_fetch_boj_returns_dataframe(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "FRED_API_KEY", "test_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "observations": [
            {"date": "2024-01-01", "value": "6800000"},
            {"date": "2024-02-01", "value": "6850000"},
        ]
    }

    with patch("data.fred.requests.get", return_value=mock_resp):
        df = fetch_boj_balance_sheet()
    assert isinstance(df, pd.DataFrame)
    assert config.SOURCE_COLUMNS["boj_bs"] in df.columns
    assert len(df) == 2
    assert isinstance(df.index, pd.DatetimeIndex)


def test_fetch_boj_fallback_on_failure(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", side_effect=Exception("network error")):
        df = fetch_boj_balance_sheet()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert config.SOURCE_COLUMNS["boj_bs"] in df.columns


def test_fetch_boj_no_api_key_returns_empty(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "FRED_API_KEY", "")

    df = fetch_boj_balance_sheet()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
