# Research And Evaluation PRD

## Goal

Determine whether the liquidity signal is useful for Bitcoin analysis after respecting publication lag and out-of-sample discipline.

## BTC Data

Use the same BTCUSD price data source used by [`bitcoin-price-analysis`](/home/ixn/Documents/code/crypto/bitcoin-price-analysis).

## Lead-Lag Method

- evaluate lags from `-6` to `+3` months in `1` month steps
- for each lag:
  - compute Pearson correlation between `m2_roc_3m` and BTC forward returns
  - compute mean BTC monthly return by regime
  - run a t-test for the difference between `EXPANDING` and `CONTRACTING` regime returns

## Regime-Conditional Report

For each regime report:

- `mean`
- `median`
- `std`
- `Sharpe`
- `hit_rate`
- `max_drawdown`
- `n_months`

Compare against:

- unconditional BTC returns
- simple 3-month BTC momentum
- buy-and-hold

## Significance Rule

- default threshold: `p < 0.05`
- apply Bonferroni correction across lag tests

## Halving-Era Split

Evaluate regime behavior separately across eras defined by:

- `2012-11-28`
- `2016-07-09`
- `2020-05-11`
- `2024-04-19`

## Decision Output

Phase 4 ends with a written conclusion in one of three forms:

1. incrementally useful
2. useful as context only
3. not useful enough to integrate

## Done Criteria

- lead-lag analysis is implemented
- regime-conditional return tables exist
- baseline comparisons exist
- halving-era checks exist
- final conclusion is explicit
