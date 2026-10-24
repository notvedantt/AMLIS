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

# Linux / macOS:
make setup      # venv, dev dependencies, pre-commit hooks
make check      # lint + types + service boundaries + tests (same as CI)

# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\pre-commit install
.\check.ps1     # runs ruff, mypy, import-linter, pytest, leakage
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

## Branching Model & Workflow

AMLIS uses a two-tier release workflow ([ADR-0001](docs/adr/0001-branching-and-tier-workflow.md), [CONTRIBUTING.md](CONTRIBUTING.md)):

```text
[main]      ──(tier-0-done)──────────────────────────► (tier-1-done)
                 ▲                                         ▲
                 │ (Release PR when all criteria pass)     │
[develop]   ─────┴──────●─────────●─────────●──────────────┴────►
                        ▲         ▲         ▲
  (Squash PRs)          │         │         │
                 feat/T0.3     feat/T0.4   feat/T0.5
                 (Aditya)      (Vedant)    (Aditya)
```

- **`main`**: Tier releases only. Always green. Tagged `tier-N-done`. Nobody commits directly.
- **`develop`**: Integration branch. Always green. All feature/task branches originate from and merge into `develop`.
- **`<type>/<task-id>-<slug>`**: Short-lived task branch (e.g. `feat/T0.4-config-schema`).

### Daily Task Workflow
1. Switch to `develop` and pull latest: `git switch develop && git pull`
2. Create your task branch: `git switch -c <branch-name>`
3. Build, test, and run checks: `.\check.ps1` (or `make check`)
4. Open PR into **`develop`** (requires 1 approval + green CI)
5. Squash-merge and delete your task branch

---

## Tier & Task Branch Directory

Full details, points, and exit criteria are tracked in [docs/TASKS.md](docs/TASKS.md) and [docs/TIERS.md](docs/TIERS.md).

### Tier 0: Foundations (Target Milestone: `tier-0-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T0.1 | Dev environment, Makefile/PowerShell, README | Rushikesh | `feat/T0.1-dev-env` | Fresh clone to green checks on all machines |
| T0.2 | Branch protection, CODEOWNERS, CI green | Aditya | `feat/T0.2-repo-protection` | Branch rules active; CI green on empty repo |
| T0.3 | Contracts library: typed models and tests | Aditya | `feat/T0.3-contracts` | Spec contracts typed, frozen, unit-tested |
| T0.4 | Config & schema single source of truth | Vedant | `feat/T0.4-config-schema` | YAML configs + validating loader |
| T0.5 | Point-in-time market data adapter & store | Aditya | `feat/T0.5-pit-store` | Every record carries `knowable_at`; no future data |
| T0.6 | Data-integrity gate (staleness, range sanity) | Vedant | `feat/T0.6-integrity-gate` | Stale/corrupt feeds rejected with reasons |
| T0.7 | Macro calendar loader (CPI, NFP, rates) | Rushikesh | `feat/T0.7-macro-calendar` | Calendar loaded into point-in-time store |
| T0.8 | Technical indicator features (RSI, MACD) | Rushikesh | `feat/T0.8-tech-features` | Features match schema, pass leakage tests |
| T0.9 | Fundamental, sentiment & macro features | Vedant | `feat/T0.9-other-features` | Surprise vs consensus & shock flags per ts |
| T0.10 | Evaluation harness: backtest, cost model | Vedant | `feat/T0.10-eval-harness` | Reproducible backtest with stated window/costs |
| T0.11 | Permanent leakage-regression suite | Aditya | `feat/T0.11-leakage-suite` | Planted look-ahead bug caught by CI |
| T0.12 | Data-source comparison and ADR-001 | Rushikesh | `docs/T0.12-adr-asset-class` | ADR merged after team review |

### Tier 1: Quant Baseline (Target Milestone: `tier-1-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T1.1 | Baselines: buy-and-hold & simple momentum | Rushikesh | `feat/T1.1-baselines` | Runs in harness with cost model |
| T1.2 | Gradient-boosted tree model & training | Aditya | `feat/T1.2-gbt-model` | Trains on PIT features, outputs ModelPrediction |
| T1.3 | Sequence model (LSTM/TCN) on GPU | Vedant | `feat/T1.3-seq-model` | Trains and evaluates on held-out windows |
| T1.4 | Stacking meta-learner & calibrated probs | Aditya | `feat/T1.4-stacking` | Calibration error reported; abstain flag supported |
| T1.5 | Model registry: immutable versioned artifacts | Vedant | `feat/T1.5-model-registry` | Artifacts hashed/immutable; ledger references hash |
| T1.6 | Quant benchmark report command | Rushikesh | `feat/T1.6-quant-report` | `amlis report quant` prints metrics table |
| T1.7 | ADR-002: benchmark protocol | Rushikesh | `docs/T1.7-adr-benchmark` | ADR merged after team review |

### Tier 2: Multi-LLM Research Layer (Target Milestone: `tier-2-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T2.1 | LangGraph skeleton & cost tracking | Aditya | `feat/T2.1-graph-skeleton` | Graph runs end-to-end with mock provider |
| T2.2 | Analysts: technical and fundamental | Aditya | `feat/T2.2-analysts-a` | Structured reports with tool traces |
| T2.3 | Analysts: news, calendar, event/shock | Vedant | `feat/T2.3-analysts-b` | Calendar vs shock paths kept separate |
| T2.4 | Analysts: sentiment and company news | Rushikesh | `feat/T2.4-analysts-c` | Both agents produce schema-valid reports |
| T2.5 | Debate tier: bull, bear, base & facilitator | Vedant | `feat/T2.5-debate-tier` | Facilitator output recorded structurally |
| T2.6 | Layered memory & reflection step | Aditya | `feat/T2.6-memory-reflection` | Reflection reviews misses before next decision |
| T2.7 | OKF curated bundles & RAG store | Vedant | `feat/T2.7-okf-rag` | KnowledgeRef resolves to versioned Markdown |
| T2.8 | Prompt library and call logging | Rushikesh | `feat/T2.8-prompt-lib` | Prompts versioned in files; calls logged |
| T2.9 | Baseline arms: single-LLM, vote, TradingAgents | Vedant | `feat/T2.9-llm-baselines` | Three arms selectable in harness |

### Tier 3: Regime Detection (Target Milestone: `tier-3-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T3.1 | Three-state regime detector (HMM) | Aditya | `feat/T3.1-hmm-regime` | RegimeState emitted with valid probabilities |
| T3.2 | Event-shock anomaly detector (autoencoder) | Vedant | `feat/T3.2-shock-detector` | Flags shocks distinct from volatility drift |
| T3.3 | Detector evaluation plots and notebook | Rushikesh | `docs/T3.3-detector-eval` | Plots committed with findings note |
| T3.4 | Wire event flags into detectors | Aditya | `feat/T3.4-event-wiring` | Calendar drift & shocks are separate inputs |

### Tier 4: RL Regime Controller (Target Milestone: `tier-4-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T4.1 | RL environment (historical replay) | Vedant | `feat/T4.1-rl-env` | Gym env with bounded action space |
| T4.2 | Composite reward & overfit hypothesis test | Aditya | `feat/T4.2-reward-overfit` | Policies failing test rejected automatically |
| T4.3 | Training pipeline & policy versioning | Vedant | `feat/T4.3-rl-train` | Immutable versioned policies in RoutingAction |
| T4.4 | Static-router baseline & H7 evaluation | Aditya | `feat/T4.4-h7-eval` | Held-out comparison table reported |
| T4.5 | RL ADR and reward-hacking checklist | Rushikesh | `docs/T4.5-adr-rl` | ADR merged after team review |

### Tier 5: Risk, Compliance, Execution, Ledger (Target Milestone: `tier-5-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T5.1 | Deterministic risk gate | Aditya | `feat/T5.1-risk-gate` | No order placed without RiskDecision.approved |
| T5.2 | Compliance gate rule engine | Vedant | `feat/T5.2-compliance-gate` | ComplianceDecision produced independently |
| T5.3 | Paper execution gateway | Rushikesh | `feat/T5.3-paper-exec` | Paper execution in DEMO; LIVE blocked |
| T5.4 | Audit ledger (hash-chained, tamper-evident) | Aditya | `feat/T5.4-audit-ledger` | Tampering with entry fails verification |
| T5.5 | Ledger verification CLI command | Rushikesh | `feat/T5.5-ledger-verify` | `amlis ledger verify` reports broken links |
| T5.6 | Router coordination modes & pre-fetch | Vedant | `feat/T5.6-router` | All 4 coordination modes selectable |

### Tier 6: Trust & Assurance (Target Milestone: `tier-6-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T6.1 | Verifier pass (grounding check) | Aditya | `feat/T6.1-verifier` | Ungrounded reasoning flagged via VerifierResult |
| T6.2 | Stress-test agent | Vedant | `feat/T6.2-stress-test` | Breaking scenarios recorded |
| T6.3 | Calibration blender with abstention | Aditya | `feat/T6.3-calibration` | Abstain is a first-class output schema |
| T6.4 | Graded escalation (flag / reduce / halt) | Vedant | `feat/T6.4-graded-escalation` | Levels tied to documented triggers |
| T6.5 | Explainable ledger rationale generator | Rushikesh | `feat/T6.5-rationale` | Every ledger entry carries rationale |

### Tier 7: System 1 Fine-Tuning (Target Milestone: `tier-7-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T7.1 | Dataset builder from ledger logs | Aditya | `feat/T7.1-s1-dataset` | PIT labels, per-task splits |
| T7.2 | Fine-tuning pipeline (GPU) | Vedant | `feat/T7.2-s1-finetune` | Reproducible run, versioned weights |
| T7.3 | Task heads: escalation & shock severity | Vedant | `feat/T7.3-s1-heads-a` | Per-head accuracy on held-out split |
| T7.4 | Task heads: grounding & compliance | Aditya | `feat/T7.4-s1-heads-b` | Per-head accuracy on held-out split |
| T7.5 | Local serving & latency benchmark | Vedant | `feat/T7.5-s1-serve` | Synchronous local serving with latency stats |
| T7.6 | H9 results table: accuracy/latency/cost | Rushikesh | `docs/T7.6-h9-table` | Table committed with raw metrics |

### Tier 8: Hardening & Final Evaluation (Target Milestone: `tier-8-done`)
| ID | Task | Owner | Branch Name | Done When |
|---|---|---|---|---|
| T8.1 | Observability, health monitoring, drift | Aditya | `feat/T8.1-observability` | Health check reflects component status |
| T8.2 | CI hardening & coverage gates | Vedant | `feat/T8.2-ci-hardening` | Coverage threshold enforced in CI |
| T8.3 | Model cards and ADR index | Rushikesh | `docs/T8.3-model-cards` | Shipped models have cards; ADR index done |
| T8.4 | CLI polish and demo script | Rushikesh | `feat/T8.4-cli-polish` | One command runs full paper-trading demo |
| T8.5 | Final report: H1-H5 findings | Vedant | `docs/T8.5-report-a` | Verdicts for hypotheses H1-H5 |
| T8.6 | Final report: H6-H10 findings | Aditya | `docs/T8.6-report-b` | Verdicts for hypotheses H6-H10 |
| T8.7 | Final report compilation & formatting | Rushikesh | `docs/T8.7-report-format` | Formatted report compiled with figures |

---

## Read next
1. `CONTRIBUTING.md`: branches, commits, PR and review rules
2. `docs/TIERS.md`: what each tier must deliver before the next starts
3. `docs/TASKS.md`: detailed task definitions and point distributions
