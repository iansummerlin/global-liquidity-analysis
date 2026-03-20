# Liquidity Composite Methodology PRD

## Goal

Produce three monthly USD-normalised aggregates and a threshold-based regime signal.

## Outputs

Maintain all three:

1. `global_m2`
   - US M2 + PBoC M2
2. `global_balance_sheet`
   - Fed + ECB + BOJ balance sheets
3. `global_liquidity_composite`
   - all five components summed

`global_liquidity_composite` is the primary signal.

## Aggregation Method

- Normalize each component into USD trillions.
- Sum components directly.
- Do not standardize or weight components.
- Missing components are omitted from the sum and recorded in metadata.
- Never extrapolate or forward-fill beyond the last known source observation.

This intentionally weights by absolute size.

## Frequency Alignment

- `M2SL`, `MABMM301CNM189S`, and BOJ series keep monthly frequency.
- `WALCL` and ECB weekly series are resampled to month-end using the last observation in the month.
- All outputs are aligned to month-end dates.

## Feature Specification

- `m2_roc_1m = composite.pct_change(1)`
- `m2_roc_3m = composite.pct_change(3)`
- `m2_roc_6m = composite.pct_change(6)`
- `m2_acceleration = m2_roc_3m.diff(1)`
- `m2_zscore_12m = (m2_roc_3m - rolling_mean_12) / rolling_std_12`
- `m2_trend = sign(m2_roc_3m.rolling(3).mean())`

The primary regime driver is `m2_roc_3m`.

## Regime Rules

- `EXPANDING` if `m2_roc_3m > 0.01`
- `CONTRACTING` if `m2_roc_3m < -0.005`
- `NEUTRAL` otherwise

These are initial thresholds. Phase 4 evaluation checks their historical stability but does not replace them during initial implementation.

## Missing Data Policy

- compute aggregates from available components
- record `sources_included` and `sources_missing`
- do not invent values for missing components

## Done Criteria

- all three aggregate outputs exist
- monthly alignment is deterministic
- feature columns are implemented exactly as specified
- regime labels are reproducible from the composite series
