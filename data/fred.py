"""FRED data loaders for M2, balance sheet, and FX series.

Cache-first with stale-fallback. Returns DataFrames with UTC DatetimeIndex
and human-readable column names (us_m2, fed_total_assets, pboc_m2, eurusd,
jpyusd, cnyusd).
"""

from __future__ import annotations

import io
import logging

import pandas as pd
import requests

import config
from data.cache import cache_get, cache_get_stale, cache_put

logger = logging.getLogger(__name__)

NAMESPACE = "fred"


def _fetch_fred_series(series_id: str, column_name: str, start_date: str | None = None) -> pd.DataFrame:
    start = start_date or config.DATA_START_DATE
    cached = cache_get(NAMESPACE, series_id, config.CACHE_TTL_SECONDS)
    if cached is not None:
        logger.debug("Cache hit for %s", series_id)
        return _deserialize(cached, column_name)

    if not config.FRED_API_KEY:
        logger.warning("FRED_API_KEY not set — trying stale cache for %s", series_id)
        return _stale_or_empty(series_id, column_name)

    params = {
        "series_id": series_id,
        "api_key": config.FRED_API_KEY,
        "observation_start": start,
        "file_type": "json",
    }
    try:
        resp = requests.get(config.FRED_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
    except Exception as e:
        logger.warning("FRED fetch failed for %s: %s — trying stale cache", series_id, e)
        return _stale_or_empty(series_id, column_name)

    rows = []
    for o in obs:
        val = o.get("value", ".")
        if val in (".", "", None):
            continue
        try:
            rows.append({"date": pd.Timestamp(o["date"], tz="UTC"), column_name: float(val)})
        except (ValueError, TypeError):
            continue

    if not rows:
        logger.warning("No valid observations for %s", series_id)
        return _empty_frame(column_name)

    df = pd.DataFrame(rows).set_index("date").sort_index()
    cache_put(NAMESPACE, series_id, _serialize(df))
    logger.info("Fetched and cached %s (%d rows)", series_id, len(df))
    return df


def _serialize(df: pd.DataFrame) -> bytes:
    return df.reset_index().to_json(orient="records", date_format="iso").encode()


def _deserialize(data: bytes, column_name: str) -> pd.DataFrame:
    df = pd.read_json(io.BytesIO(data), orient="records", convert_dates=["date"])
    df = df.set_index("date")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    # Rename columns to expected name if needed (handles cached data from before rename)
    if column_name not in df.columns and len(df.columns) == 1:
        df.columns = [column_name]
    return df


def _stale_or_empty(series_id: str, column_name: str) -> pd.DataFrame:
    stale = cache_get_stale(NAMESPACE, series_id)
    if stale is not None:
        logger.info("Using stale cache for %s", series_id)
        return _deserialize(stale, column_name)
    return _empty_frame(column_name)


def _empty_frame(column_name: str) -> pd.DataFrame:
    df = pd.DataFrame(columns=[column_name])
    df.index = pd.DatetimeIndex([], name="date", tz="UTC")
    return df


def fetch_us_m2() -> pd.DataFrame:
    return _fetch_fred_series(config.FRED_SERIES["us_m2"], config.SOURCE_COLUMNS["us_m2"])


def fetch_fed_balance_sheet() -> pd.DataFrame:
    return _fetch_fred_series(config.FRED_SERIES["fed_bs"], config.SOURCE_COLUMNS["fed_bs"])


def fetch_pboc_m2() -> pd.DataFrame:
    return _fetch_fred_series(config.FRED_SERIES["pboc_m2"], config.SOURCE_COLUMNS["pboc_m2"])


def fetch_fx_rates() -> pd.DataFrame:
    fx_keys = [("fx_eurusd", "eurusd"), ("fx_jpyusd", "jpyusd"), ("fx_cnyusd", "cnyusd")]
    frames = {}
    for cfg_key, col_name in fx_keys:
        sid = config.FRED_SERIES[cfg_key]
        col = config.SOURCE_COLUMNS[cfg_key]
        df = _fetch_fred_series(sid, col)
        if not df.empty:
            frames[col] = df[col]
    if not frames:
        return _empty_fx_frame()
    result = pd.DataFrame(frames)
    result.index.name = "date"
    return result


def _empty_fx_frame() -> pd.DataFrame:
    cols = [config.SOURCE_COLUMNS[k] for k in ("fx_eurusd", "fx_jpyusd", "fx_cnyusd")]
    df = pd.DataFrame(columns=cols)
    df.index = pd.DatetimeIndex([], name="date", tz="UTC")
    return df
