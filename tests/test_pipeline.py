"""Tests for data/pipeline.py — Phase 1 contract tests."""

from unittest.mock import patch

import pandas as pd

import config
from data.pipeline import fetch_all, fetch_and_validate, report_sources


def _make_frame(col, n=3):
    idx = pd.date_range("2024-01-01", periods=n, freq="ME", tz="UTC")
    return pd.DataFrame({col: [1000.0 + i for i in range(n)]}, index=idx)


def _mock_fetchers():
    return {
        "us_m2": _make_frame(config.SOURCE_COLUMNS["us_m2"]),
        "fed_bs": _make_frame(config.SOURCE_COLUMNS["fed_bs"]),
        "pboc_m2": _make_frame(config.SOURCE_COLUMNS["pboc_m2"]),
        "fx_rates": _make_fx_frame(),
        "ecb_bs": _make_frame(config.SOURCE_COLUMNS["ecb_bs"]),
        "boj_bs": _make_empty("boj_total_assets"),
    }


def _make_fx_frame():
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    return pd.DataFrame({
        "eurusd": [1.08, 1.09, 1.07],
        "jpyusd": [0.0067, 0.0068, 0.0066],
        "cnyusd": [0.14, 0.14, 0.14],
    }, index=idx)


def _make_empty(col):
    df = pd.DataFrame(columns=[col])
    df.index = pd.DatetimeIndex([], name="date", tz="UTC")
    return df


def _patch_all(mocks):
    return [
        patch("data.pipeline.fetch_us_m2", return_value=mocks["us_m2"]),
        patch("data.pipeline.fetch_fed_balance_sheet", return_value=mocks["fed_bs"]),
        patch("data.pipeline.fetch_pboc_m2", return_value=mocks["pboc_m2"]),
        patch("data.pipeline.fetch_fx_rates", return_value=mocks["fx_rates"]),
        patch("data.pipeline.fetch_ecb_balance_sheet", return_value=mocks["ecb_bs"]),
        patch("data.pipeline.fetch_boj_balance_sheet", return_value=mocks["boj_bs"]),
    ]


def test_fetch_all_returns_all_sources():
    mocks = _mock_fetchers()
    patches = _patch_all(mocks)
    for p in patches:
        p.start()
    try:
        result = fetch_all()
    finally:
        for p in patches:
            p.stop()

    assert isinstance(result, dict)
    for key in ("us_m2", "fed_bs", "ecb_bs", "boj_bs", "pboc_m2", "fx_rates"):
        assert key in result
        assert isinstance(result[key], pd.DataFrame)


def test_fetch_and_validate_validates_all():
    mocks = _mock_fetchers()
    patches = _patch_all(mocks)
    for p in patches:
        p.start()
    try:
        result = fetch_and_validate()
    finally:
        for p in patches:
            p.stop()

    assert isinstance(result, dict)
    assert len(result["us_m2"]) == 3
    assert config.SOURCE_COLUMNS["us_m2"] in result["us_m2"].columns
    assert result["boj_bs"].empty


def test_fetch_and_validate_with_empty_sources():
    empty = {
        "us_m2": _make_empty("us_m2"),
        "fed_bs": _make_empty("fed_total_assets"),
        "pboc_m2": _make_empty("pboc_m2"),
        "fx_rates": _make_empty_fx(),
        "ecb_bs": _make_empty("ecb_total_assets"),
        "boj_bs": _make_empty("boj_total_assets"),
    }
    patches = _patch_all(empty)
    for p in patches:
        p.start()
    try:
        result = fetch_and_validate()
    finally:
        for p in patches:
            p.stop()

    for key in ("us_m2", "fed_bs", "ecb_bs", "boj_bs", "pboc_m2"):
        assert isinstance(result[key], pd.DataFrame)
        assert result[key].empty


def _make_empty_fx():
    df = pd.DataFrame(columns=["eurusd", "jpyusd", "cnyusd"])
    df.index = pd.DatetimeIndex([], name="date", tz="UTC")
    return df


def test_report_sources_output():
    mocks = _mock_fetchers()
    report = report_sources(mocks)
    assert "us_m2" in report
    assert "boj_bs" in report
    assert "EMPTY" in report  # BOJ should show as empty
