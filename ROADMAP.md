# Global Liquidity Analysis Roadmap

## Document Status

- **Purpose:** Turn this repository into a reliable global liquidity data-product and evaluation repo for downstream Bitcoin research.
- **Audience:** A fresh engineering agent with zero prior context.
- **Primary constraint:** Build the artifact honestly, test it honestly, and do not overclaim macro signal quality.
- **Last updated:** March 20, 2026. Source hardening and downstream integration results incorporated.

---

## Start Here

If you are a fresh agent with no other context:

1. Read this roadmap fully once.
2. Read `CLAUDE.md` for architecture, commands, and non-negotiable constraints.
3. Read `README.md` to confirm it matches the roadmap.
4. Phases 0-4 are complete. Do not rebuild the scaffolding.
5. The repo already exports a validated artifact and already has downstream consumption in `bitcoin-price-analysis`.
6. The current conclusion is not “breakthrough signal.” It is “useful as context only.”

**Default next task:** maintain source quality, documentation, and artifact reliability. Do not reopen ML or autoresearch work unless there is a specific new hypothesis.

---

## Mission

This repository should answer, with evidence:

1. Can we build a point-in-time global liquidity composite from free macro sources?
2. Can we export it cleanly for downstream consumption?
3. Does it add enough incremental value to matter for Bitcoin research?

If the evidence says “context only” or “not useful enough,” the correct outcome is to document that clearly.

---

## Current Judgment

Current status: `research-only`.

What is complete:

- source loaders, cache, and validation
- USD normalisation and monthly aggregation
- regime artifact export and schema validation
- BTC evaluation harness and markdown reporting
- downstream JSON consumption by `bitcoin-price-analysis`

What the repo currently supports:

- `make fetch-all`
- `make update`
- `make validate`
- `make evaluate`

Current result:

- evaluation conclusion in this repo: `useful as context only`
- downstream result in `bitcoin-price-analysis`: additive liquidity features were mixed; liquidity regime worked better as optional context/gating than as a direct additive feature family

---

## Working Principles

1. **Point-in-time correctness is mandatory.**
2. **Reuse `bitcoin-price-analysis` structure where it improves familiarity.**
3. **Simple regime logic comes before ML.**
4. **Shared-trend correlation is not enough; usefulness must be tested out of sample.**
5. **The repo must fail honestly.**
6. **Do not relabel a partial composite as something cleaner than it is.**

---

## Naming Guardrails

- `global_m2` = money-supply-only aggregate
- `global_balance_sheet` = balance-sheet-only aggregate
- `global_liquidity_composite` = combined signal

Regime classification is based on `global_liquidity_composite`.

---

## Completed Phases

### Phase 0: Scaffold

Completed.

- repo structure created in the style of `bitcoin-price-analysis`
- core docs, Makefile, config, and tests established
- `make test` passed

### Phase 1: Source Layer

Completed.

- FRED-based source loaders
- cache-first / stale-fallback behavior
- source validation
- fetch pipeline
- `make fetch-all` passed

### Phase 2: Composite Construction

Completed.

- USD normalisation
- monthly alignment
- aggregate construction:
  - `global_m2`
  - `global_balance_sheet`
  - `global_liquidity_composite`
- momentum features and regime classification
- artifact export
- `make update` passed

### Phase 3: Artifact Contract

Completed.

- stable JSON schema
- artifact validation helpers
- `make validate` enforcement
- consumer-facing documentation

### Phase 4: Evaluation

Completed.

- BTC monthly return loader
- lead-lag analysis
- regime-conditional return stats
- baselines and halving-era splits
- markdown report generation
- `make evaluate` passed

Conclusion:

- `useful as context only`

---

## Source Hardening Outcome

The source layer evolved beyond the initial PRDs:

- ECB balance sheet now comes from FRED `ECBASSETSW`
- BOJ balance sheet now comes from FRED `JPNASSETS`
- PBoC M2 uses FRED `MYAGM2CNM189N`

Current component set:

| Component | Series | Status |
|---|---|---|
| US M2 | `M2SL` | Current |
| Fed balance sheet | `WALCL` | Current |
| ECB balance sheet | `ECBASSETSW` | Current |
| BOJ balance sheet | `JPNASSETS` | Current |
| PBoC M2 | `MYAGM2CNM189N` | Ends 2019-08 |

Remaining limitation:

- after August 2019, the composite is effectively 4-of-5 components because free FRED Chinese M2 coverage ends

---

## Downstream Outcome

The artifact is already consumed by [`bitcoin-price-analysis`](/home/ixn/Documents/code/crypto/bitcoin-price-analysis).

Downstream findings:

- additive liquidity features: mixed tradeoff
- 4h additive use: effectively neutral
- simpler liquidity representations: cleaner than the full additive family
- liquidity regime: useful as context
- optional directional liquidity gate: modest classification improvement, operationally weak in trading terms

Interpretation:

- liquidity is worth keeping as macro context
- liquidity is not strong enough to rescue the downstream BTC signal economically

---

## Decision Gates

| Gate | Question | Status |
|---|---|---|
| G1 | Can the repo scaffold run and test cleanly? | Passed |
| G2 | Can the source layer fetch and validate committed components? | Passed |
| G3 | Can the repo export a stable, validated artifact? | Passed |
| G4 | Can the repo produce a written out-of-sample evaluation? | Passed |
| G5 | Is the signal strong enough to justify strong standalone predictive claims? | No |
| G6 | Is the signal useful enough to keep as research context and downstream optional input? | Yes |

---

## What Not To Reopen Casually

- broad ML exploration
- broad autoresearch loops
- additive liquidity feature tuning
- threshold fiddling without a new hypothesis

Those are not the bottleneck right now.

---

## Future Work

Only pursue with a concrete hypothesis:

1. source maintenance if free-series coverage changes
2. artifact stability / consumer ergonomics
3. narrow downstream regime-context experiments
4. new macro or flow data families beyond the current liquidity composite

Not justified by current evidence:

- treating this repo as a production dependency
- claiming standalone tradable edge
- broad search over liquidity feature weighting schemes

---

## Success Criteria

Any of these counts as success:

1. The repo produces a clean, reusable liquidity artifact for downstream research.
2. The repo proves liquidity is useful as macro context even if not a strong standalone signal.
3. The repo documents a weak or mixed result honestly enough to prevent wasted downstream effort.
