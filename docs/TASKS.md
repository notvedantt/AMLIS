# Task board

Points: Easy = 1, Medium = 2, Hard = 3. Vedant and Aditya carry the Medium/Hard work and are balanced within 1 point. Rushikesh owns Easy tasks only.

| Member | Tasks | Points |
|---|---|---|
| Vedant | 22 | 52 |
| Aditya | 21 | 51 |
| Rushikesh | 18 | 18 |

Branch for each task: `feat/<ID>-<slug>` (or `docs/` for documents). Reviewer is the service's second reviewer in CODEOWNERS.

Notes: GPU-heavy work (sequence model, RL training, System 1 fine-tuning) sits with Vedant. Tier 3 can overlap Tier 2 after T2.1. Build basic versions of the Tier 5 gates early so every later tier runs behind them.


## Tier 0: Foundations

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T0.1 | Dev environment, Makefile, README quickstart verified on all 3 machines | Rushikesh | E | `feat/T0.1-dev-env` | Fresh clone to green `make check` on every member's machine |

| T0.2 | Branch protection, CODEOWNERS wiring, CI green on empty repo | Aditya | M | `feat/T0.2-repo-protection` | Rules from CONTRIBUTING.md active on GitHub; a test PR is blocked until CI passes |

| T0.3 | Contracts library: finalise typed models and tests | Aditya | M | `feat/T0.3-contracts` | All spec data contracts typed, frozen, validated, unit-tested |

| T0.4 | Config and schema single source of truth (feature schema, asset config, regime definitions) | Vedant | M | `feat/T0.4-config-schema` | YAML configs + validating loader; no duplicated constants in code |

| T0.5 | Point-in-time market data adapter and store (knowable_at stamps) | Aditya | H | `feat/T0.5-pit-store` | Every record carries knowable_at; queries cannot return future data |

| T0.6 | Data-integrity gate (staleness, range sanity, cross-source agreement) | Vedant | M | `feat/T0.6-integrity-gate` | Bad/stale feeds rejected with reasons; tests for each failure mode |

| T0.7 | Macro calendar loader (CPI, NFP, rate decisions) | Rushikesh | E | `feat/T0.7-macro-calendar` | Calendar CSV/API loaded into the point-in-time store |

| T0.8 | Technical indicator features (RSI, MACD, moving averages, volatility) | Rushikesh | E | `feat/T0.8-tech-features` | Features match the schema and pass leakage tests |

| T0.9 | Fundamental, sentiment and macro-event features | Vedant | M | `feat/T0.9-other-features` | Surprise-vs-consensus and shock flags produced per timestamp |

| T0.10 | Evaluation harness: rolling backtest, cost model, Sharpe/Sortino/drawdown | Vedant | H | `feat/T0.10-eval-harness` | Reproducible backtest with stated window, cost model, OOS boundary |

| T0.11 | Permanent leakage-regression suite (fails the build on any look-ahead) | Aditya | H | `feat/T0.11-leakage-suite` | Planted look-ahead bug is caught by CI |

| T0.12 | Data-source comparison and ADR-001 (asset class for first version) | Rushikesh | E | `docs/T0.12-adr-asset-class` | ADR merged after team review |


## Tier 1: Quant baseline

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T1.1 | Baselines: buy-and-hold and simple momentum inside the harness | Rushikesh | E | `feat/T1.1-baselines` | Both baselines run through the same harness and cost model |

| T1.2 | Gradient-boosted tree model and training pipeline | Aditya | M | `feat/T1.2-gbt-model` | Trains on point-in-time features, outputs ModelPrediction |

| T1.3 | Sequence model (LSTM/TCN) on GPU | Vedant | H | `feat/T1.3-seq-model` | Trains and evaluates on held-out windows |

| T1.4 | Stacking meta-learner and calibrated probabilities | Aditya | M | `feat/T1.4-stacking` | Calibration error reported; abstain flag supported |

| T1.5 | Model registry: immutable versioned artifacts and model card template | Vedant | M | `feat/T1.5-model-registry` | Artifacts hashed and immutable; ledger can reference a version |

| T1.6 | Quant benchmark report command (first honest benchmark) | Rushikesh | E | `feat/T1.6-quant-report` | `amlis report quant` prints metrics table with window and costs |

| T1.7 | ADR-002: benchmark protocol (windows, costs, splits) | Rushikesh | E | `docs/T1.7-adr-benchmark` | ADR merged after team review |


## Tier 2: Multi-LLM research layer

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T2.1 | LangGraph skeleton, multi-provider LLM abstraction, per-call cost tracking | Aditya | H | `feat/T2.1-graph-skeleton` | One graph runs end-to-end with a mock provider; token cost logged |

| T2.2 | Analysts: technical and fundamental | Aditya | M | `feat/T2.2-analysts-a` | Structured reports with tool-call traces |

| T2.3 | Analysts: news, economic calendar, event/shock, cross-asset | Vedant | H | `feat/T2.3-analysts-b` | Calendar vs shock paths kept separate |

| T2.4 | Analysts: sentiment and company news (using the prompt template) | Rushikesh | E | `feat/T2.4-analysts-c` | Both agents produce schema-valid reports |

| T2.5 | Debate tier: bull, bear, base-case researchers and facilitator | Vedant | H | `feat/T2.5-debate-tier` | Facilitator output recorded structurally |

| T2.6 | Layered memory (short/mid/long) and reflection step | Aditya | H | `feat/T2.6-memory-reflection` | Reflection reviews recent misses before next decision |

| T2.7 | OKF curated bundles, loader and RAG store | Vedant | M | `feat/T2.7-okf-rag` | KnowledgeRef resolves to versioned Markdown bundles |

| T2.8 | Prompt library and LLM call logging | Rushikesh | E | `feat/T2.8-prompt-lib` | All prompts versioned in files; every call logged |

| T2.9 | Baseline arms: single-LLM, majority-vote, TradingAgents-style | Vedant | M | `feat/T2.9-llm-baselines` | Three arms selectable in the harness |


## Tier 3: Regime detection

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T3.1 | Three-state regime detector (HMM) and evaluation | Aditya | M | `feat/T3.1-hmm-regime` | RegimeState emitted with probabilities summing to 1 |

| T3.2 | Event-shock anomaly detector (autoencoder) | Vedant | H | `feat/T3.2-shock-detector` | Flags shocks distinct from ordinary volatility drift |

| T3.3 | Detector evaluation plots and notebook | Rushikesh | E | `docs/T3.3-detector-eval` | Plots committed with a short findings note |

| T3.4 | Wire scheduled-vs-unscheduled event flags into detectors | Aditya | M | `feat/T3.4-event-wiring` | Calendar drift and shocks are separate inputs |


## Tier 4: RL regime controller

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T4.1 | RL environment (historical replay) | Vedant | H | `feat/T4.1-rl-env` | Gym-style env with bounded action space owned by risk gate |

| T4.2 | Composite reward and overfitting hypothesis test | Aditya | H | `feat/T4.2-reward-overfit` | Policy failing the test is rejected automatically |

| T4.3 | Training pipeline and policy versioning (GPU) | Vedant | M | `feat/T4.3-rl-train` | Immutable versioned policies referenced by RoutingAction |

| T4.4 | Static-router baseline and H7 evaluation | Aditya | M | `feat/T4.4-h7-eval` | Held-out comparison table, negative result reported if H7 fails |

| T4.5 | RL ADR and reward-hacking checklist | Rushikesh | E | `docs/T4.5-adr-rl` | ADR merged after team review |


## Tier 5: Risk, compliance, execution, ledger

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T5.1 | Deterministic risk gate (sizing, limits, correlation, kill-switch) | Aditya | H | `feat/T5.1-risk-gate` | No code path places an order without RiskDecision.approved |

| T5.2 | Compliance gate rule engine (rules from OKF) | Vedant | M | `feat/T5.2-compliance-gate` | ComplianceDecision produced after risk, independent of it |

| T5.3 | Paper execution gateway with DEMO/LIVE flag | Rushikesh | E | `feat/T5.3-paper-exec` | No fabricated ticket IDs; LIVE blocked in this repo |

| T5.4 | Audit ledger: hash-chained, append-only, rationale field | Aditya | H | `feat/T5.4-audit-ledger` | Tampering with any entry fails verification |

| T5.5 | Ledger verification CLI command | Rushikesh | E | `feat/T5.5-ledger-verify` | `amlis ledger verify` reports first broken link |

| T5.6 | Router: coordination modes and proactive pre-fetch | Vedant | H | `feat/T5.6-router` | quant-only / one LLM / full debate / escalate selectable |


## Tier 6: Trust & Assurance

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T6.1 | Verifier pass (rule-based first, System 1 later) | Aditya | M | `feat/T6.1-verifier` | Ungrounded reasoning flagged via VerifierResult |

| T6.2 | Stress-test agent | Vedant | M | `feat/T6.2-stress-test` | Scenario that breaks the winning view is recorded |

| T6.3 | Calibration blender with confidence interval and abstention | Aditya | H | `feat/T6.3-calibration` | Abstain is a first-class output in the decision schema |

| T6.4 | Graded escalation (flag / reduce size / halt) | Vedant | M | `feat/T6.4-graded-escalation` | Each level tied to a documented trigger |

| T6.5 | Explainable ledger rationale generator | Rushikesh | E | `feat/T6.5-rationale` | Every ledger entry carries a short rationale |


## Tier 7: System 1 fine-tuning

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T7.1 | Dataset builder from ledger logs (point-in-time labels, per-task splits) | Aditya | H | `feat/T7.1-s1-dataset` | No label uses information unknown at decision time |

| T7.2 | Fine-tuning pipeline for the decision model (full fine-tune on GPU) | Vedant | H | `feat/T7.2-s1-finetune` | Reproducible run, versioned weights, training log |

| T7.3 | Task heads: router escalation and event severity | Vedant | M | `feat/T7.3-s1-heads-a` | Per-head accuracy on held-out split |

| T7.4 | Task heads: verifier grounding and compliance check | Aditya | M | `feat/T7.4-s1-heads-b` | Per-head accuracy on held-out split |

| T7.5 | Local microservice serving and latency benchmark | Vedant | M | `feat/T7.5-s1-serve` | Synchronous local call, latency measured |

| T7.6 | H9 results table: accuracy vs latency vs cost against LLM baseline | Rushikesh | E | `docs/T7.6-h9-table` | Table committed with raw numbers attached |


## Tier 8: Hardening

| ID | Task | Owner | Size | Branch | Done when |
|---|---|---|---|---|---|

| T8.1 | Observability: structured logging, drift monitoring, cost tracking | Aditya | M | `feat/T8.1-observability` | Health check reflects real component status |

| T8.2 | CI hardening and coverage gates | Vedant | M | `feat/T8.2-ci-hardening` | Coverage threshold enforced in CI |

| T8.3 | Model cards and ADR index completed | Rushikesh | E | `docs/T8.3-model-cards` | Every shipped model has a card; ADR index current |

| T8.4 | CLI polish and demo script | Rushikesh | E | `feat/T8.4-cli-polish` | One command runs a full paper-trading demo |

| T8.5 | Final report: results for H1-H5 | Vedant | M | `docs/T8.5-report-a` | Each hypothesis has a stated verdict |

| T8.6 | Final report: results for H6-H10 | Aditya | M | `docs/T8.6-report-b` | Each hypothesis has a stated verdict |

| T8.7 | Final report formatting, figures and references | Rushikesh | E | `docs/T8.7-report-format` | Report compiled in the department format |
