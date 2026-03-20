"""Regime stability analysis across time."""

from __future__ import annotations

import json
import logging
import sys

import pandas as pd

import config
from data.btc import load_btc_monthly_returns
from evaluation.regime import regime_conditional_stats, unconditional_stats

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

    print("Regime-Conditional BTC Return Statistics")
    print("=" * 60)

    stats = regime_conditional_stats(combined["btc"], combined["regime"])
    print(stats.to_string())
    print()

    unc = unconditional_stats(combined["btc"])
    print(f"Unconditional: mean={unc['mean']:.4f}, sharpe={unc['sharpe']:.4f}, n={unc['n_months']}")
    print()

    # Regime transition counts
    regime_changes = (regimes != regimes.shift(1)).sum() - 1
    print(f"Regime transitions: {regime_changes}")
    print(f"Total months: {len(regimes)}")
    print(f"Regime distribution:")
    for regime in ["EXPANDING", "NEUTRAL", "CONTRACTING"]:
        count = (regimes == regime).sum()
        pct = count / len(regimes) * 100 if len(regimes) > 0 else 0
        print(f"  {regime}: {count} months ({pct:.1f}%)")


if __name__ == "__main__":
    main()
