"""ECB balance sheet loader.

Fetches ECB total assets via FRED series ECBASSETSW (weekly, millions EUR).
Cache-first with stale-fallback. Returns DataFrame with UTC DatetimeIndex
and column 'ecb_total_assets'.

Previously used the ECB SDMX BSI endpoint directly, but that returns 404
for the configured series key. FRED mirrors the same data reliably.
"""

from __future__ import annotations

import logging

import pandas as pd

import config
from data.fred import _fetch_fred_series

logger = logging.getLogger(__name__)

COLUMN = config.SOURCE_COLUMNS["ecb_bs"]


def fetch_ecb_balance_sheet() -> pd.DataFrame:
    return _fetch_fred_series(
        config.FRED_SERIES["ecb_bs"],
        COLUMN,
    )
