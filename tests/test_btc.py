"""Tests for data/btc.py — BTC data loader."""

import pandas as pd

from data.btc import load_btc_monthly_returns


def test_load_nonexistent_path():
    result = load_btc_monthly_returns("/nonexistent/path.csv")
    assert result.empty
    assert result.name == "btc_return"


def test_load_from_csv(tmp_path):
    """Test loading from a synthetic CSV."""
    csv = tmp_path / "test_btc.csv"
    csv.write_text(
        "https://www.CryptoDataDownload.com\n"
        "unix,date,symbol,open,high,low,close,Volume BTC,Volume USD\n"
        "1,2020-01-15 00:00:00,BTC/USD,8000,8100,7900,8050,1.0,8050\n"
        "2,2020-01-16 00:00:00,BTC/USD,8050,8200,8000,8100,1.0,8100\n"
        "3,2020-02-15 00:00:00,BTC/USD,8100,8300,8000,9000,1.0,9000\n"
        "4,2020-02-16 00:00:00,BTC/USD,9000,9100,8900,9050,1.0,9050\n"
        "5,2020-03-15 00:00:00,BTC/USD,9050,9200,9000,8500,1.0,8500\n"
        "6,2020-03-16 00:00:00,BTC/USD,8500,8600,8400,8400,1.0,8400\n"
    )
    result = load_btc_monthly_returns(str(csv))
    assert not result.empty
    assert result.name == "btc_return"
    # Should have monthly returns
    assert len(result) >= 1
