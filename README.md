# AMLIS: Adaptive Multi-LLM Intelligence System

Decision-support system (not an autonomous trader). Quant ensemble + multi-LLM research layer + bounded RL
router, with deterministic risk and compliance gates that no model can override. Paper trading only.

## Team
| Member | Role |
|---|---|
| Vedant | Core builder (GPU work, fine-tuning lead) |
| Aditya | Core builder (data, contracts, gates, ledger) |
| Rushikesh | Supporting builder (docs, loaders, simple features, CLI, reports) |

## Quickstart
```bash
git clone <repo-url> && cd amlis
make setup      # venv, dev dependencies, pre-commit hooks
make check      # lint + types + service boundaries + tests (same as CI)
```

## Structure
```
amlis/
├── apps/cli/                 # command-line entry point (DEMO mode only)
├── services/                 # one folder per plane/component, see services/<name>/README.md
│   ├── data_plane/
│   ├── feature_plane/
│   ├── evaluation/
│   ├── quant_ensemble/
│   ├── llm_research/
│   ├── knowledge/
│   ├── regime/
│   ├── rl_controller/
│   ├── router/
│   ├── risk_gate/
│   ├── compliance_gate/
│   ├── execution/
│   ├── ledger/
│   ├── trust_assurance/
│   ├── calibration/
│   ├── system1/
│   ├── observability/
├── libs/
│   ├── contracts/            # typed models shared by all services
│   ├── config/               # feature schema, asset config, regime definitions (YAML + loader)
│   └── common/               # point-in-time helpers, model registry
├── knowledge/okf/            # curated OKF Markdown bundles
├── tests/{unit,integration,leakage}/
├── infra/   data/   docs/{adr,guides,model_cards}/
└── .github/                  # CI, CODEOWNERS, PR and issue templates
```

## Read next
1. `CONTRIBUTING.md`: branches, commits, PR and review rules
2. `docs/TIERS.md`: what each tier must deliver before the next starts
3. `docs/TASKS.md`: who owns which task
