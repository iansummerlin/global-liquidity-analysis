# Data Sources And Point-In-Time PRD

## Goal

Implement cache-first loaders for all committed sources with explicit publication-lag assumptions.

## Committed Sources

| Source | Series | Frequency | Typical Lag | Units |
|---|---|---|---|---|
| US M2 | `M2SL` | Monthly | 30-45 days | Billions USD |
| Fed balance sheet | `WALCL` | Weekly | 3 days | Millions USD |
| PBoC M2 | `MABMM301CNM189S` | Monthly | 45-60 days | Billions CNY |
| ECB balance sheet | ECB BSI total-assets series | Weekly | 7 days | Millions EUR |
| BOJ balance sheet | BOJ total-assets series | Monthly | 14 days | Billions JPY |
| EUR/USD | `DEXUSEU` | Daily | 1 day | Rate |
| JPY/USD | `DEXJPUS` | Daily | 1 day | Rate |
| CNY/USD | `DEXCHUS` | Daily | 1 day | Rate |

## Endpoints

- FRED observations endpoint:
  - `https://api.stlouisfed.org/fred/series/observations`
  - params: `api_key`, `series_id`, `observation_start`, `file_type=json`
- ECB SDMX endpoint base:
  - `https://data-api.ecb.europa.eu/service/data/BSI/`
- BOJ endpoint:
  - use BOJ time-series source for total-assets balance-sheet data
  - if implementation friction is high, ship a stub loader with the expected schema and a clear TODO

## Loader Contract

Each loader must:

1. check cache first
2. fetch on cache miss or expired cache
3. fall back to stale cache on fetch failure
4. return a `pd.DataFrame` with a UTC `DatetimeIndex`
5. return a single named value column plus source metadata where needed
6. return empty schema-valid frames if no data is available

Preferred pattern: mirror `bitcoin-price-analysis/data/crossasset.py`.

## Config Defaults

- data start date: `2006-01-01`
- cache TTL: `7` days for all sources
- env var for FRED key: `FRED_API_KEY`
- fallback FX rates:
  - EUR/USD `1.08`
  - JPY/USD `0.0067`
  - CNY/USD `0.14`

## FX Policy

- Monthly and monthly-aligned series use month-end spot FX.
- Weekly series are resampled to month-end first, then converted.
- If FX data is missing for a required date, use the configured fallback rate and record that fallback was used.

## Validation Rules

All source frames must satisfy:

- positive numeric values
- monotonic increasing index
- no duplicate timestamps
- no future dates
- expected column name present

## Expected Loader Functions

- `fetch_us_m2()`
- `fetch_fed_balance_sheet()`
- `fetch_pboc_m2()`
- `fetch_fx_rates()`
- `fetch_ecb_balance_sheet()`
- `fetch_boj_balance_sheet()`

## Done Criteria

- all committed sources have loader modules
- FRED key handling is wired via environment variable
- publication lag assumptions are documented in code/config
- `make fetch-all` produces schema-valid frames for every included source
