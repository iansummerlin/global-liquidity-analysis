# Project Guidelines

## What This Repo Is

A global liquidity data-product and research repo. It builds a point-in-time global liquidity dataset and regime artifact that can be tested for incremental value in Bitcoin research and trading systems. The canonical plan and progress live in `ROADMAP.md`.

**Current status:** Core build-out complete, all sources hardened. All 5 components fetch via FRED, though free PBoC coverage ends in 2019-08. `make update` produces and validates `artifacts/liquidity_regime.json`. `make evaluate` runs lead-lag, regime, halving analysis and writes `artifacts/evaluation_report.md`. Current conclusion: useful as context only. The artifact is already consumed downstream by `bitcoin-price-analysis`.

## Architecture

```text
.
├── data/         # source loaders (all via FRED), cache, validation, pipeline
├── features/     # normalisation, aggregation, momentum/regime features
├── evaluation/   # regime analysis, backtesting, reporting
├── signals/      # artifact export (liquidity_regime.json)
├── scripts/      # research scripts (lead-lag, regime stability, halving interaction)
├── tests/        # pytest suite
└── artifacts/    # exported JSON artifacts (gitignored except .gitkeep)
```

## Commands

```bash
make setup         # create venv + install deps
make test          # run full test suite
make fetch-all     # fetch all source data
make update        # full pipeline: fetch, process, export artifact
make evaluate      # run Phase 4 evaluation, write artifacts/evaluation_report.md
make validate      # validate current artifact against PRD schema
make clean-cache   # remove cached data
```

All commands use `.venv/bin/python`.

## Non-Negotiable Rules

1. **Point-in-time correctness is mandatory.** Never use data that would not have been available at the time of observation. No lookahead.
2. **Cache-first, stale-fallback.** All remote API calls go through `data/cache.py`. On fetch failure, prefer stale cache over no data.
3. **Honest naming.** `global_m2` = money supply only. `global_balance_sheet` = balance sheet only. `global_liquidity_composite` = combined five-component signal. Never mislabel.
4. **Threshold-based regime baseline before ML.** The initial regime classifier uses simple thresholds on `m2_roc_3m`. No ML until Phase 4 evaluation is complete.
5. **Tests must pass.** Run `make test` after every change.
6. **The repo must fail honestly.** If the signal is stale, weak, or not useful, say so explicitly. Never overstate signal quality.
7. **Do not treat this as a proven standalone signal repo.** The best current use is macro context and downstream research support.

## Naming Guardrails

- `global_m2` = US M2 + PBoC M2
- `global_balance_sheet` = Fed + ECB + BOJ balance sheets
- `global_liquidity_composite` = all five components summed

## Key Config

- Data starts: `2006-01-01`
- Cache TTL: 7 days
- Staleness: 14 days
- Regime: EXPANDING (>1%), NEUTRAL, CONTRACTING (<-0.5%) based on 3-month rate of change
