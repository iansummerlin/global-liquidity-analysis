# Global Liquidity Analysis

This repository is a global liquidity data-product and research repo for Bitcoin analysis.

It does not trade. It exists to answer one question honestly: does a point-in-time liquidity composite add enough incremental value to be worth consuming downstream?

The canonical execution plan and progress tracker live in [ROADMAP.md](/home/ixn/Documents/code/crypto/global-liquidity-analysis/ROADMAP.md).

## Current Judgment

As of March 20, 2026, this repo is `research-only`, not a justified standalone trading dependency.

Core build-out is complete:

- source ingestion and cache-first validation
- USD normalisation and monthly aggregation
- regime artifact export and schema validation
- BTC evaluation harness and written report generation
- downstream JSON consumption by [`bitcoin-price-analysis`](/home/ixn/Documents/code/crypto/bitcoin-price-analysis)

Current conclusion: the liquidity composite is **useful as context only**.

What that means in practice:

- in this repo, the macro relationship is directionally interesting but not statistically strong enough to claim standalone predictive power
- in `bitcoin-price-analysis`, additive liquidity features were a tradeoff, not an improvement
- the best downstream use so far is an optional regime/context filter, not a promoted model feature family

This is still good research output. The repo built and falsified the idea honestly.

## Architecture

```text
.
├── data/         # source loaders, BTC loader, cache, validation, fetch pipeline
├── evaluation/   # regime stats, lead-lag analysis, baselines, report generation
├── features/     # normalisation, aggregation, momentum, regime features
├── signals/      # liquidity_regime.json export and validation
├── scripts/      # narrow research helpers
├── tests/        # unit + integration coverage
├── config.py     # source ids, thresholds, paths, evaluation constants
├── main.py       # update / validate / evaluate entrypoint
├── README.md
└── ROADMAP.md
```

## Source Policy

All remote series go through the shared cache in [data/cache.py](/home/ixn/Documents/code/crypto/global-liquidity-analysis/data/cache.py).

- cache-first
- stale cache over repeated retries
- schema-correct empty frames on hard failure
- point-in-time handling over convenience

Current component set:

| Component | Source | Series | Units | Frequency | Status |
|---|---|---|---|---|---|
| US M2 | FRED | `M2SL` | Billions USD | Monthly | Current |
| Fed balance sheet | FRED | `WALCL` | Millions USD | Weekly | Current |
| ECB balance sheet | FRED | `ECBASSETSW` | Millions EUR | Weekly | Current |
| BOJ balance sheet | FRED | `JPNASSETS` | 100M JPY | Monthly | Current |
| PBoC M2 | FRED | `MYAGM2CNM189N` | Raw CNY | Monthly | Ends 2019-08 |
| FX rates | FRED | `DEXUSEU`, `DEXJPUS`, `DEXCHUS` | FX rate | Daily | Current |

Known limitation: the free FRED PBoC M2 series ends in August 2019, so recent composite values are effectively 4-of-5 components.

## Naming Contract

- `global_m2` = US M2 + PBoC M2
- `global_balance_sheet` = Fed + ECB + BOJ balance sheets
- `global_liquidity_composite` = all five components summed

The primary regime signal is derived from `global_liquidity_composite`.

## Core Workflow

Setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
make test       # run full test suite
make fetch-all  # fetch and validate source frames
make update     # build and export liquidity_regime.json
make validate   # validate the current artifact
make evaluate   # write artifacts/evaluation_report.md
```

Requires a FRED API key in `.env`:

```bash
FRED_API_KEY=your_key_here
```

## Artifact Contract

The downstream API is a versioned JSON file written by [signals/export.py](/home/ixn/Documents/code/crypto/global-liquidity-analysis/signals/export.py).

Path:

```text
artifacts/liquidity_regime.json
```

Key fields:

- `schema_version`
- `generated_at`
- `last_data_date`
- `data_lag_days`
- `regime`
- `m2_momentum_3m`
- `m2_momentum_1m`
- `m2_acceleration`
- `global_liquidity_latest_usd_trillions`
- `components`
- `sources_included`
- `sources_missing`
- `time_series`
- `is_stale`
- `stale_after_days`

Validation is enforced by:

- [signals/export.py](/home/ixn/Documents/code/crypto/global-liquidity-analysis/signals/export.py)
- `make validate`

### Staleness

- artifact staleness threshold: `14` days
- consumers must inspect `is_stale`
- a schema-valid artifact may still be partial or stale

### Consumer rule

Downstream repos should read the JSON file directly.

Do **not** import this repo as a Python dependency.

## Evaluation Contract

[main.py](/home/ixn/Documents/code/crypto/global-liquidity-analysis/main.py) exposes:

- `make update` -> fetch, normalise, aggregate, classify, export
- `make validate` -> validate artifact schema
- `make evaluate` -> produce [artifacts/evaluation_report.md](/home/ixn/Documents/code/crypto/global-liquidity-analysis/artifacts/evaluation_report.md)

The evaluation path includes:

- lead-lag analysis across lags `-6` to `+3`
- regime-conditional BTC return stats
- unconditional baseline
- buy-and-hold baseline
- 3-month BTC momentum baseline
- Bonferroni correction
- halving-era splits
- explicit conclusion classification

BTC returns are loaded from the sibling [`bitcoin-price-analysis`](/home/ixn/Documents/code/crypto/bitcoin-price-analysis) repo by default via [data/btc.py](/home/ixn/Documents/code/crypto/global-liquidity-analysis/data/btc.py).

## Current Results

Current written evaluation result:

- conclusion: `useful as context only`

Interpretation:

- the repo found a plausible macro context signal
- it did not find evidence strong enough to support strong standalone predictive claims
- downstream testing showed the signal is more useful for regime awareness than as an additive feature family

## Downstream Integration

This repo is already consumed downstream by [`bitcoin-price-analysis`](/home/ixn/Documents/code/crypto/bitcoin-price-analysis) via [data/liquidity.py](/home/ixn/Documents/code/crypto/bitcoin-price-analysis/data/liquidity.py).

The initial downstream feature set is intentionally small:

- `liquidity_global_usd_t`
- `liquidity_m2_roc_3m`
- `liquidity_regime_expanding`
- `liquidity_regime_neutral`
- `liquidity_regime_contracting`

Downstream result so far:

- additive liquidity features were mixed
- liquidity regime worked better as optional context/gating than as a direct additive family

## What This Repo Proved

1. A global liquidity composite can be built cleanly from free macro sources with a point-in-time artifact contract.
2. The signal is worth keeping as macro research context.
3. The signal is not strong enough, in its current form, to justify strong standalone trading claims.

## Roadmap

See [ROADMAP.md](/home/ixn/Documents/code/crypto/global-liquidity-analysis/ROADMAP.md) for the full phase history, current status, and future-work boundaries.
