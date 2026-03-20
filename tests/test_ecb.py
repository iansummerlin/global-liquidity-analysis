"""Tests for data/ecb.py — ECB balance sheet via FRED ECBASSETSW."""

from unittest.mock import patch, MagicMock

import pandas as pd

from data.ecb import fetch_ecb_balance_sheet
import config


def test_fetch_ecb_returns_dataframe(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "FRED_API_KEY", "test_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "observations": [
            {"date": "2024-01-05", "value": "6000000"},
            {"date": "2024-01-12", "value": "6050000"},
        ]
    }

    with patch("data.fred.requests.get", return_value=mock_resp):
        df = fetch_ecb_balance_sheet()
    assert isinstance(df, pd.DataFrame)
    assert config.SOURCE_COLUMNS["ecb_bs"] in df.columns
    assert len(df) == 2
    assert isinstance(df.index, pd.DatetimeIndex)


def test_fetch_ecb_fallback_on_failure(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "FRED_API_KEY", "test_key")

    with patch("data.fred.requests.get", side_effect=Exception("network error")):
        df = fetch_ecb_balance_sheet()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert config.SOURCE_COLUMNS["ecb_bs"] in df.columns


def test_fetch_ecb_no_api_key_returns_empty(tmp_path, monkeypatch):
    import data.cache as cm
    monkeypatch.setattr(cm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "FRED_API_KEY", "")

    df = fetch_ecb_balance_sheet()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
