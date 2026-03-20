"""BOJ balance sheet loader.

Fetches BOJ total assets via FRED series JPNASSETS (monthly, 100 million JPY).
Cache-first with stale-fallback. Returns DataFrame with UTC DatetimeIndex
and column 'boj_total_assets'.

Previously a stub because BOJ's own site requires HTML scraping. FRED
mirrors the series reliably as JPNASSETS.
"""

from __future__ import annotations

import logging

import pandas as pd

import config
from data.fred import _fetch_fred_series

logger = logging.getLogger(__name__)

COLUMN = config.SOURCE_COLUMNS["boj_bs"]


def fetch_boj_balance_sheet() -> pd.DataFrame:
    return _fetch_fred_series(
        config.FRED_SERIES["boj_bs"],
        COLUMN,
    )
