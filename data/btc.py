"""BTC monthly return loader for evaluation.

Reads BTCUSD hourly CSV from bitcoin-price-analysis (same source),
resamples to month-end close, and computes monthly returns.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

import config

logger = logging.getLogger(__name__)


def load_btc_monthly_returns(csv_path: str | Path | None = None) -> pd.Series:
    """Load BTC hourly CSV and return month-end monthly returns.

    Returns a Series with DatetimeIndex (month-end) and name 'btc_return'.
    Returns empty Series if data is unavailable.
    """
    path = Path(csv_path) if csv_path else config.BTC_CSV_PATH

    if not path.exists():
        logger.warning("BTC CSV not found at %s — returning empty series", path)
        return pd.Series(dtype=float, name="btc_return")

    try:
        df = pd.read_csv(path, skiprows=1, parse_dates=["date"])
        df = df.set_index("date").sort_index()
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        monthly_close = df["close"].resample("ME").last().dropna()
        returns = monthly_close.pct_change().dropna()
        returns.name = "btc_return"
        logger.info("Loaded BTC monthly returns: %d months (%s to %s)",
                     len(returns), returns.index[0].strftime("%Y-%m"),
                     returns.index[-1].strftime("%Y-%m"))
        return returns
    except Exception as e:
        logger.warning("Failed to load BTC data from %s: %s", path, e)
        return pd.Series(dtype=float, name="btc_return")
