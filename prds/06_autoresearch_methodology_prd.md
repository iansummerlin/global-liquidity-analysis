# Autoresearch Methodology PRD

## Status

Deferred. Do not execute until Phases 0-4 are complete and baseline evaluation results exist.

## Goal

Reuse the experiment-loop discipline from `bitcoin-price-analysis` for narrow, predefined research questions in this repo.

## Required Reuse

- predefined experiment lists
- held-out isolation
- checkpointing
- append-only results logging
- generated run report
- no automatic source mutation

## Scope Rule

Define the exact search dimensions only when the evaluation harness exists and there is a clear question worth automating.

If this loop does not improve research clarity over manual testing, do not build it.
