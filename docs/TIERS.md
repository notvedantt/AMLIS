# Tier-wise guidelines
A tier is done only when every exit criterion below is demonstrably true (test, CI run or merged document). Then Aditya opens a PR `develop -> main` and tags `tier-N-done`.
General rules for every tier: one task per branch, tests with the code, leakage test for anything touching data, ADR for hard-to-reverse choices.

## Tier 0: Foundations
Data plane, integrity gate, feature plane, config, evaluation harness, leakage protection.

- **Can start when:** Nothing yet. Start here.
- **Workload (points):** Rushikesh 4, Aditya 10, Vedant 9
- **Exit criteria:**
  - [ ] `make check` green on all 3 machines
  - [ ] Point-in-time store returns no future data (test proves it)
  - [ ] Integrity gate rejects stale/bad feeds
  - [ ] Leakage suite fails on a planted look-ahead bug
  - [ ] Harness reproduces a buy-and-hold backtest with costs
  - [ ] ADR-001 (asset class) accepted
- **Watch out:** Never skip the leakage suite. A backtest number without the harness's stated window and cost model is not a result.
- **Tasks:** T0.1, T0.2, T0.3, T0.4, T0.5, T0.6, T0.7, T0.8, T0.9, T0.10, T0.11, T0.12

## Tier 1: Quant baseline
Trained quant ensemble and the first honest, leakage-checked benchmark.

- **Can start when:** Tier 0 exit criteria met.
- **Workload (points):** Rushikesh 3, Aditya 4, Vedant 5
- **Exit criteria:**
  - [ ] Quant ensemble trains on point-in-time features
  - [ ] Calibration error measured
  - [ ] Benchmark report vs buy-and-hold with costs
  - [ ] Models are versioned and immutable
- **Watch out:** Beat the simple baseline honestly or report that it did not. Do not tune on the test window.
- **Tasks:** T1.1, T1.2, T1.3, T1.4, T1.5, T1.6, T1.7

## Tier 2: Multi-LLM research layer
Analyst roles, debate, memory/reflection, OKF knowledge, baseline arms.

- **Can start when:** Tier 1 exit criteria met.
- **Workload (points):** Aditya 8, Vedant 10, Rushikesh 2
- **Exit criteria:**
  - [ ] All analyst roles produce schema-valid reports with tool-call traces
  - [ ] Debate tier and memory/reflection work end-to-end with a mock provider
  - [ ] OKF bundles resolve via KnowledgeRef
  - [ ] Baseline arms (single-LLM, vote, TradingAgents-style) run in the harness
- **Watch out:** Use post-cutoff evaluation windows for LLM arms. Log every LLM call and its cost.
- **Tasks:** T2.1, T2.2, T2.3, T2.4, T2.5, T2.6, T2.7, T2.8, T2.9, T2.10, T2.11, T2.12, T2.13

## Tier 3: Regime detection
Three-state regime detector and event-shock detector, evaluated independently.

- **Can start when:** Tier 1 done. Can run in parallel with Tier 2 after T2.1.
- **Workload (points):** Aditya 4, Vedant 3, Rushikesh 1
- **Exit criteria:**
  - [ ] RegimeState emitted with valid probabilities
  - [ ] Shock detector separates shocks from volatility drift
  - [ ] Both evaluated independently with plots
- **Watch out:** Detector error is an input the RL controller must be robust to, not ground truth.
- **Tasks:** T3.1, T3.2, T3.3, T3.4

## Tier 4: RL regime controller
Bounded RL router; ships only if H7 holds on held-out data (extended objective).

- **Can start when:** Tiers 0-3 stable (spec rule). Extended objective.
- **Workload (points):** Vedant 5, Aditya 5, Rushikesh 1
- **Exit criteria:**
  - [ ] Bounded action space matches risk-gate limits
  - [ ] Overfitting test implemented and rejects bad policies
  - [ ] H7 evaluated on held-out data; negative result reported if it fails
- **Watch out:** The controller can never touch position size or execution. Ship only if H7 holds.
- **Tasks:** T4.1, T4.2, T4.3, T4.4, T4.5

## Tier 5: Risk, compliance, execution, ledger
Deterministic gates, paper execution, router, hash-chained audit ledger.

- **Can start when:** Tier 1 done (gates must exist before any LLM arm is trusted). Build basic versions early.
- **Workload (points):** Aditya 6, Vedant 5, Rushikesh 2
- **Exit criteria:**
  - [ ] No execution path without approved RiskDecision then cleared ComplianceDecision
  - [ ] Paper execution in DEMO mode, LIVE blocked
  - [ ] Ledger verification detects tampering
  - [ ] Router selects all four coordination modes
- **Watch out:** Written as plain code, no model calls inside the gates.
- **Tasks:** T5.1, T5.2, T5.3, T5.4, T5.5, T5.6

## Tier 6: Trust & Assurance
Verifier, stress-test, calibration with abstention, graded escalation, rationales.

- **Can start when:** Tier 5 done.
- **Workload (points):** Aditya 5, Vedant 4, Rushikesh 1
- **Exit criteria:**
  - [ ] Verifier, stress-test, graded escalation implemented
  - [ ] Abstention is a valid output in the decision schema
  - [ ] Ledger entries carry rationales
- **Watch out:** Abstention must be measured (H10), not just allowed.
- **Tasks:** T6.1, T6.2, T6.3, T6.4, T6.5

## Tier 7: System 1 fine-tuning
Fine-tuned decision model heads, serving, and H9 evaluation (showcase tier).

- **Can start when:** Tiers 2, 5 and 6 running, so real logged decisions exist to train on.
- **Workload (points):** Aditya 5, Vedant 7, Rushikesh 1
- **Exit criteria:**
  - [ ] One fine-tuned head per task, point-in-time splits
  - [ ] Local synchronous serving with measured latency
  - [ ] H9 table: accuracy vs latency vs cost against the LLM baseline
- **Watch out:** Fine-tuning showcase tier. Document hyperparameters, seeds and data splits so every run is reproducible.
- **Tasks:** T7.1, T7.2, T7.3, T7.4, T7.5, T7.6

## Tier 8: Hardening
Observability, CI hardening, model cards, ADRs, CLI polish, final report.

- **Can start when:** All earlier tiers done.
- **Workload (points):** Aditya 4, Vedant 4, Rushikesh 3
- **Exit criteria:**
  - [ ] Observability and per-decision cost tracking
  - [ ] CI coverage gate
  - [ ] Model cards and ADR index complete
  - [ ] Final report with a verdict on H1-H10
  - [ ] One-command demo
- **Watch out:** Negative results are results. Report them.
- **Tasks:** T8.1, T8.2, T8.3, T8.4, T8.5, T8.6, T8.7
