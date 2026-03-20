# Signal Export And Consumer Integration PRD

## Goal

Export a stable JSON artifact and define how downstream consumers read it.

## Artifact

Primary export path:

- `artifacts/liquidity_regime.json`

Schema:

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-03-20T12:00:00Z",
  "last_data_date": "2026-01-31",
  "data_lag_days": 48,
  "regime": "EXPANDING",
  "m2_momentum_3m": 0.023,
  "m2_momentum_1m": 0.008,
  "m2_acceleration": 0.002,
  "global_liquidity_latest_usd_trillions": 108.5,
  "components": {
    "us_m2_usd_trillions": 21.2,
    "fed_bs_usd_trillions": 7.4,
    "ecb_bs_usd_trillions": 6.8,
    "boj_bs_usd_trillions": 4.9,
    "pboc_m2_usd_trillions": 42.1
  },
  "sources_included": ["us_m2", "fed_bs", "ecb_bs", "boj_bs", "pboc_m2"],
  "sources_missing": [],
  "time_series": [
    {"date": "2020-01-31", "global_liquidity_usd_t": 85.2, "m2_roc_3m": 0.012, "regime": "EXPANDING"}
  ],
  "is_stale": false,
  "stale_after_days": 14
}
```

## Validation Rules

- required fields must exist
- `schema_version` must equal expected version
- `generated_at` must be valid ISO 8601 UTC
- `data_lag_days >= 0`
- `regime` must be one of `EXPANDING`, `NEUTRAL`, `CONTRACTING`
- `sources_included` must be non-empty
- `sources_missing` may be empty
- `time_series` entries must contain `date`, `global_liquidity_usd_t`, `m2_roc_3m`, `regime`

## Staleness Policy

- `stale_after_days = 14`
- `is_stale = data_lag_days > stale_after_days`
- consumers must check `is_stale` explicitly

## Consumer Pattern

Downstream consumers should read the JSON artifact, not import this repo directly.

For `bitcoin-price-analysis`:

- add `data/liquidity.py`
- read `artifacts/liquidity_regime.json`
- extract time-series data into feature columns
- add `LIQUIDITY_COLUMNS` in config
- add `include_liquidity` flag in `build_dataset()`

## Done Criteria

- artifact is exported at the fixed path
- validation exists
- staleness is computed consistently
- downstream integration contract is documented
