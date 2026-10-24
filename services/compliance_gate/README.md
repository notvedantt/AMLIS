# compliance_gate

Deterministic rule engine, rules loaded from OKF.

| | |
|---|---|
| Tier | 5 (Risk, compliance, execution, ledger) |
| Owner | Vedant |
| Second reviewer | Aditya |

## Rules
- Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
- Keep one public entry point in `__init__.py`.

## Tasks
- T5.2 (Vedant): Compliance gate rule engine (rules from OKF)
