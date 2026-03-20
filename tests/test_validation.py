"""Tests for data/validation.py — Phase 1 validation tests."""

import pytest
import pandas as pd

from data.validation import validate_frame, ValidationError


def _make_frame(col, values, dates=None):
    if dates is None:
        dates = pd.date_range("2024-01-01", periods=len(values), freq="ME", tz="UTC")
    return pd.DataFrame({col: values}, index=dates)


def test_validate_valid_frame():
    df = _make_frame("us_m2", [21000, 21100, 21200])
    result = validate_frame(df, "us_m2")
    assert len(result) == 3


def test_validate_empty_frame_passes():
    df = pd.DataFrame(columns=["us_m2"])
    df.index = pd.DatetimeIndex([], name="date", tz="UTC")
    result = validate_frame(df, "us_m2")
    assert result.empty


def test_validate_rejects_missing_column():
    df = pd.DataFrame(columns=["wrong_col"])
    df.index = pd.DatetimeIndex([], name="date", tz="UTC")
    with pytest.raises(ValidationError, match="missing expected column"):
        validate_frame(df, "us_m2")


def test_validate_rejects_negative_values():
    df = _make_frame("us_m2", [21000, -100, 21200])
    with pytest.raises(ValidationError, match="negative values"):
        validate_frame(df, "us_m2")


def test_validate_rejects_duplicate_timestamps():
    dates = pd.DatetimeIndex(["2024-01-31", "2024-01-31", "2024-02-29"], tz="UTC")
    df = pd.DataFrame({"us_m2": [21000, 21100, 21200]}, index=dates)
    with pytest.raises(ValidationError, match="duplicate timestamps"):
        validate_frame(df, "us_m2")


def test_validate_rejects_future_dates():
    dates = pd.DatetimeIndex(["2024-01-31", "2099-12-31"], tz="UTC")
    df = pd.DataFrame({"us_m2": [21000, 21100]}, index=dates)
    with pytest.raises(ValidationError, match="future dates"):
        validate_frame(df, "us_m2")


def test_validate_sorts_unsorted_index():
    dates = pd.DatetimeIndex(["2024-03-31", "2024-01-31", "2024-02-29"], tz="UTC")
    df = pd.DataFrame({"us_m2": [21200, 21000, 21100]}, index=dates)
    result = validate_frame(df, "us_m2")
    assert result.index.is_monotonic_increasing


def test_validate_rejects_non_datetime_index():
    df = pd.DataFrame({"us_m2": [21000]}, index=[0])
    with pytest.raises(ValidationError, match="DatetimeIndex"):
        validate_frame(df, "us_m2")


def test_validate_fx_rates_schema():
    dates = pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC")
    df = pd.DataFrame({
        "eurusd": [1.08, 1.09],
        "jpyusd": [0.0067, 0.0068],
        "cnyusd": [0.14, 0.14],
    }, index=dates)
    result = validate_frame(df, "fx_rates")
    assert len(result) == 2
