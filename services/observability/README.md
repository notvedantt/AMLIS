# observability

Structured logging, drift monitoring, per-decision cost tracking.

| | |
|---|---|
| Tier | 8 (Hardening) |
| Owner | Aditya |
| Second reviewer | Vedant |

## Rules
- Import only from `libs.*`. Never import another service's internals; talk through `libs.contracts` types.
- Keep one public entry point in `__init__.py`.

## Tasks
- T8.1 (Aditya): Observability: structured logging, drift monitoring, cost tracking
