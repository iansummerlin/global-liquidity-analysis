"""Lead-lag analysis between liquidity momentum and BTC returns."""

from __future__ import annotations

import json
import logging
import sys

import pandas as pd

import config
from data.btc import load_btc_monthly_returns
from evaluation.regime import lead_lag_analysis, apply_bonferroni

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
        print("No time series data in artifact. Cannot run lead-lag analysis.")
        sys.exit(1)

    ts_df = pd.DataFrame(ts)
    ts_df["date"] = pd.to_datetime(ts_df["date"], utc=True)
    ts_df = ts_df.set_index("date").sort_index()

    m2_roc_3m = ts_df["m2_roc_3m"]
    regimes = ts_df["regime"]

    btc_returns = load_btc_monthly_returns()
    if btc_returns.empty:
        print("No BTC data available.")
        sys.exit(1)

    result = lead_lag_analysis(m2_roc_3m, btc_returns, regimes)
    if result.empty:
        print("No overlapping data for lead-lag analysis.")
        sys.exit(1)

    corrected = apply_bonferroni(result["ttest_p"])
    result["ttest_p_bonf"] = corrected

    print("Lead-Lag Analysis Results")
    print("=" * 60)
    print(result.to_string(index=False))
    print()
    print(f"Bonferroni correction: {len(config.EVAL_LAGS)} tests")


if __name__ == "__main__":
    main()
