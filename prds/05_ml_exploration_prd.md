# Future ML Exploration PRD

## Status

Deferred. Do not execute unless Phase 4 shows the signal is incrementally useful.

## Goal

Test whether liquidity features improve downstream forecasting beyond simple non-ML baselines.

## Guardrails

1. Use strict walk-forward validation.
2. Compare against trivial and non-ML baselines.
3. Keep the feature set interpretable.
4. Reject models that improve fit but not decision usefulness.
5. Archive this PRD if Phase 4 concludes the signal is not incrementally useful.
