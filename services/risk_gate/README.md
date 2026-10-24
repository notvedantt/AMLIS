# risk_gate

Deterministic sizing, exposure limits, correlation checks, kill-switch (veto power).

| | |
|---|---|
| Tier | 5 (Risk, compliance, execution, ledger) |
| Owner | Aditya |
| Second reviewer | Vedant |

## Rules
- Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
- Keep one public entry point in `__init__.py`.

## Tasks
- T5.1 (Aditya): Deterministic risk gate (sizing, limits, correlation, kill-switch)
