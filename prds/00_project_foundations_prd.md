# Project Foundations PRD

## Goal

Create the repo scaffold so `global-liquidity-analysis` feels like `bitcoin-price-analysis` and `make test` passes on day one.

## Deliverables

```text
global-liquidity-analysis/
├── .gitignore
├── .env.example
├── CLAUDE.md
├── README.md
├── ROADMAP.md
├── Makefile
├── requirements.txt
├── config.py
├── main.py
├── data/
│   ├── __init__.py
│   ├── cache.py
│   ├── fred.py
│   ├── ecb.py
│   ├── boj.py
│   ├── pipeline.py
│   └── validation.py
├── features/
│   ├── __init__.py
│   ├── normalisation.py
│   ├── aggregation.py
│   └── momentum.py
├── evaluation/
│   ├── __init__.py
│   ├── regime.py
│   ├── backtest.py
│   └── reporting.py
├── signals/
│   ├── __init__.py
│   └── export.py
├── scripts/
│   ├── explore_lead_lag.py
│   ├── regime_stability.py
│   └── halving_interaction.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_fred.py
│   ├── test_ecb.py
│   ├── test_boj.py
│   ├── test_pipeline.py
│   ├── test_normalisation.py
│   ├── test_aggregation.py
│   ├── test_momentum.py
│   ├── test_regime.py
│   ├── test_export.py
│   └── test_backtest.py
└── artifacts/
    └── .gitkeep
```

## `config.py`

Must define:

- `ROOT_DIR`, `ARTIFACTS_DIR`, `CACHE_DIR`
- `DATA_START_DATE = "2006-01-01"`
- `CACHE_TTL_DAYS = 7`
- `SIGNAL_STALE_AFTER_DAYS = 14`
- FRED series ids:
  - `M2SL`
  - `WALCL`
  - `MABMM301CNM189S`
  - `DEXUSEU`
  - `DEXJPUS`
  - `DEXCHUS`
- API endpoints for FRED, ECB, BOJ
- fallback FX rates:
  - `EURUSD = 1.08`
  - `JPYUSD = 0.0067`
  - `CNYUSD = 0.14`
- regime thresholds:
  - `EXPANDING = 0.01`
  - `CONTRACTING = -0.005`

## `Makefile`

Must include:

- `setup`
- `test`
- `fetch-all`
- `update`
- `evaluate`
- `validate`
- `clean-cache`

## `requirements.txt`

Must include:

- `pandas`
- `numpy`
- `requests`
- `pytest`

Add other packages only if required by implementation.

## `.gitignore`

Must ignore:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.env`
- `artifacts/*.json`
- `data/cache/`

Keep `artifacts/.gitkeep`.

## `.env.example`

Must contain:

```text
FRED_API_KEY=your_key_here
```

## `CLAUDE.md`

Must include:

- repo mission
- architecture summary
- commands to run
- non-negotiable rules:
  - point-in-time correctness
  - cache-first, stale-fallback behavior
  - no mislabeled `global_m2`
  - threshold-based regime baseline before ML

## `README.md`

Must include:

- repo purpose
- current status
- architecture overview
- quick start
- artifact contract summary
- roadmap pointer

## Scaffold Code Rules

- Stub modules are required so imports resolve.
- Stubs may return empty `DataFrame`s or raise `NotImplementedError` only where tests expect it.
- `data/cache.py` should be adapted from `bitcoin-price-analysis/data/cache.py` with root-path changes only where needed.

## Test Skeleton

Phase-0 tests that should pass immediately:

- `test_config.py`
- `test_cache.py`

The remaining tests should exist with scaffold expectations:

- loader tests use mocked APIs
- feature tests assert shape/column contracts
- export tests assert schema shape
- backtest tests may use synthetic data

## Done Criteria

- repo layout exists
- all imports resolve
- `make test` passes
- scaffold matches `bitcoin-price-analysis` conventions closely
