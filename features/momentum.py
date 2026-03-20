"""Momentum and regime features derived from the liquidity composite."""

from __future__ import annotations

import numpy as np
import pandas as pd

import config


def compute_momentum_features(composite: pd.Series) -> pd.DataFrame:
    if composite.empty:
        return pd.DataFrame(columns=[
            "m2_roc_1m", "m2_roc_3m", "m2_roc_6m",
            "m2_acceleration", "m2_zscore_12m", "m2_trend",
        ])

    df = pd.DataFrame(index=composite.index)
    df["m2_roc_1m"] = composite.pct_change(1)
    df["m2_roc_3m"] = composite.pct_change(3)
    df["m2_roc_6m"] = composite.pct_change(6)
    df["m2_acceleration"] = df["m2_roc_3m"].diff(1)
    rolling_mean = df["m2_roc_3m"].rolling(12).mean()
    rolling_std = df["m2_roc_3m"].rolling(12).std()
    df["m2_zscore_12m"] = (df["m2_roc_3m"] - rolling_mean) / rolling_std
    df["m2_trend"] = np.sign(df["m2_roc_3m"].rolling(3).mean())
    return df


def classify_regime(m2_roc_3m: pd.Series) -> pd.Series:
    if m2_roc_3m.empty:
        return pd.Series(dtype=str, name="regime")

    expanding = config.REGIME_THRESHOLDS["EXPANDING"]
    contracting = config.REGIME_THRESHOLDS["CONTRACTING"]

    conditions = [
        m2_roc_3m > expanding,
        m2_roc_3m < contracting,
    ]
    choices = ["EXPANDING", "CONTRACTING"]
    result = pd.Series(
        np.select(conditions, choices, default="NEUTRAL"),
        index=m2_roc_3m.index,
        name="regime",
    )
    return result
