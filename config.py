"""Shared configuration for global-liquidity-analysis."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
CACHE_DIR = ROOT_DIR / "data" / "cache"

DATA_START_DATE = "2006-01-01"
CACHE_TTL_DAYS = 7
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 86400
SIGNAL_STALE_AFTER_DAYS = 14

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES = {
    "us_m2": "M2SL",
    "fed_bs": "WALCL",
    "pboc_m2": "MYAGM2CNM189N",
    "ecb_bs": "ECBASSETSW",
    "boj_bs": "JPNASSETS",
    "fx_eurusd": "DEXUSEU",
    "fx_jpyusd": "DEXJPUS",
    "fx_cnyusd": "DEXCHUS",
}

# Human-readable column names returned by each loader.
SOURCE_COLUMNS = {
    "us_m2": "us_m2",
    "fed_bs": "fed_total_assets",
    "pboc_m2": "pboc_m2",
    "fx_eurusd": "eurusd",
    "fx_jpyusd": "jpyusd",
    "fx_cnyusd": "cnyusd",
    "ecb_bs": "ecb_total_assets",
    "boj_bs": "boj_total_assets",
}

ECB_BASE_URL = "https://data-api.ecb.europa.eu/service/data/BSI/"
BOJ_BASE_URL = "https://www.stat-search.boj.or.jp/ssi/mtshtml/bs01_m_1.html"

FALLBACK_FX = {
    "EURUSD": 1.08,
    "JPYUSD": 0.0067,
    "CNYUSD": 0.14,
}

# Publication lag assumptions (days) per PRD.
PUBLICATION_LAG = {
    "us_m2": {"typical_min": 30, "typical_max": 45, "frequency": "monthly", "units": "Billions USD"},
    "fed_bs": {"typical_min": 3, "typical_max": 3, "frequency": "weekly", "units": "Millions USD"},
    "pboc_m2": {"typical_min": 45, "typical_max": 60, "frequency": "monthly", "units": "CNY (raw units via FRED MYAGM2CNM189N, ends 2019-08)"},
    "ecb_bs": {"typical_min": 7, "typical_max": 7, "frequency": "weekly", "units": "Millions EUR (FRED ECBASSETSW)"},
    "boj_bs": {"typical_min": 14, "typical_max": 14, "frequency": "monthly", "units": "100 Million JPY (FRED JPNASSETS)"},
    "fx_eurusd": {"typical_min": 1, "typical_max": 1, "frequency": "daily", "units": "Rate"},
    "fx_jpyusd": {"typical_min": 1, "typical_max": 1, "frequency": "daily", "units": "Rate"},
    "fx_cnyusd": {"typical_min": 1, "typical_max": 1, "frequency": "daily", "units": "Rate"},
}

REGIME_THRESHOLDS = {
    "EXPANDING": 0.01,
    "CONTRACTING": -0.005,
}

SCHEMA_VERSION = "1.0.0"

ARTIFACT_PATH = ARTIFACTS_DIR / "liquidity_regime.json"

COMPOSITE_COMPONENTS = ["us_m2", "fed_bs", "ecb_bs", "boj_bs", "pboc_m2"]

HALVING_DATES = [
    "2012-11-28",
    "2016-07-09",
    "2020-05-11",
    "2024-04-19",
]

# BTC price data — reuse bitcoin-price-analysis CSV if available locally.
BTC_CSV_PATH = Path(os.environ.get(
    "BTC_CSV_PATH",
    str(ROOT_DIR.parent / "bitcoin-price-analysis" / "BTCUSD_1H.csv"),
))

# Evaluation config
EVAL_LAGS = list(range(-6, 4))  # -6 to +3 inclusive
EVAL_SIGNIFICANCE_THRESHOLD = 0.05
EVAL_REPORT_PATH = ARTIFACTS_DIR / "evaluation_report.md"
EVAL_MIN_MONTHS = 12  # minimum months of overlapping data required
