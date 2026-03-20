"""Halving-era interaction with liquidity regimes."""

from __future__ import annotations

import json
import logging
import sys

import pandas as pd

import config
from data.btc import load_btc_monthly_returns
from evaluation.regime import halving_era_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    artifact_path = config.ARTIFACT_PATH
    if not artifact_path.exists():
        print(f"Artifact not found at {artifact_path}. Run 'make update' first.")
        sys.exit(1)

    with open(artifact_path) as f:
        artifact = json.load(f)

    ts = artifact.get("time_series", [])
    if not ts:
        print("No time series data in artifact.")
        sys.exit(1)

    ts_df = pd.DataFrame(ts)
    ts_df["date"] = pd.to_datetime(ts_df["date"], utc=True)
    ts_df = ts_df.set_index("date").sort_index()
    regimes = ts_df["regime"]

    btc_returns = load_btc_monthly_returns()
    if btc_returns.empty:
        print("No BTC data available.")
        sys.exit(1)

    combined = pd.DataFrame({"btc": btc_returns, "regime": regimes}).dropna()
    if combined.empty:
        print("No overlapping data.")
        sys.exit(1)

    era_results = halving_era_split(combined["btc"], combined["regime"])
    era_labels = ["Pre-2012", "2012-2016", "2016-2020", "2020-2024", "Post-2024"]

    print("Halving-Era Regime Analysis")
    print("=" * 60)

    for i, (era_key, era_stats) in enumerate(era_results.items()):
        label = era_labels[i] if i < len(era_labels) else era_key
        print(f"\n{label}")
        print("-" * 40)
        if not era_stats.empty:
            print(era_stats.to_string())
        else:
            print("No data in this era.")

    if not era_results:
        print("No halving-era data available.")


if __name__ == "__main__":
    main()
