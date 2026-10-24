# execution

Paper-trading gateway with explicit DEMO/LIVE flag; no fabricated fills.

| | |
|---|---|
| Tier | 5 (Risk, compliance, execution, ledger) |
| Owner | Rushikesh |
| Second reviewer | Aditya |

## Rules
- Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
- Keep one public entry point in `__init__.py`.

## Tasks
- T5.3 (Rushikesh): Paper execution gateway with DEMO/LIVE flag
