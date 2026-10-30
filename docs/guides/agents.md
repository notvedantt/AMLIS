# AMLIS Agent Roster & Component Architecture (T2.12)

AMLIS uses a multi-LLM research and debate layer coordinated via LangGraph orchestration.
All LLM agents are strictly **advisory**: they produce structured research reports and theses, but have **zero execution authority**.
Deterministic risk and compliance gates, statistical quant models, and cryptographic ledgers sit outside the LLM layer.

---

## The 16 LLM Agents (+1 Optional for Crypto)

AMLIS defines a total roster of 16 core LLM agents (17 if cryptocurrency is selected as the asset class):

### 1. Domain Analyst Agents (Sub-graph / Tier 2)
1. **Technical Analyst** (`T2.2`): Analyzes price action, moving averages, momentum indicators (RSI, MACD), and volatility bands.
2. **Fundamental Analyst** (`T2.2`): Examines financial health, valuation ratios, cash flows, and macro industry positioning.
3. **Economic Calendar Analyst** (`T2.3`): Analyzes scheduled economic events (CPI, NFP, FOMC interest rate announcements) against consensus expectations.
4. **Event / Shock Analyst** (`T2.3`): Evaluates unscheduled market-moving events, geopolitical disruptions, and unexpected macroeconomic shocks.
5. **Cross-Asset Analyst** (`T2.3`): Analyzes inter-market relationships across equities, sovereign bond yields, currency indices (DXY), and commodities.
6. **Sentiment Analyst** (`T2.4`): Evaluates news and social sentiment scores and crowd positioning indicators.
7. **Company / Sector News Analyst** (`T2.4`): Synthesizes corporate announcements, earnings call narratives, and sector-specific news developments.
8. *(Optional 17th)* **On-Chain Analyst**: Evaluates wallet flows, exchange net inflows/outflows, network hash rate, and contract interactions (enabled only if crypto is selected).

### 2. Debate & Synthesis Tier (Adversarial Research / Tier 2)
9. **Bull Researcher** (`T2.5`): Formulates and defends the strongest possible long thesis, upside asymmetry, and growth catalysts.
10. **Bear Researcher** (`T2.5`): Formulates and defends the strongest possible short or defensive thesis, downside risks, and fragility points.
11. **Base-Case Researcher** (`T2.5`): Evaluates the most probable median outcome, mean-reversion expectations, and realistic consolidation ranges.
12. **Debate Facilitator** (`T2.5`): Moderates structured multi-turn debates between Bull, Bear, and Base researchers, producing an objective, balanced synthesis report.

### 3. Trader Advisory Agent (Tier 2)
13. **Trader Agent** (`T2.10`): Synthesizes the debate findings, quant signals, and market state into a unified advisory trade proposal.
    - **Advisory only**: Never sizes positions, never submits orders, and holds zero execution credentials.

### 4. Risk-Perspective Agents (Tier 2)
14. **Risky Perspective Agent** (`T2.11`): Analyzes proposals from an aggressive, high-upside/convexity perspective.
15. **Neutral Perspective Agent** (`T2.11`): Analyzes proposals from a benchmark-tracking, balanced risk-return perspective.
16. **Safe Perspective Agent** (`T2.11`): Analyzes proposals from a strict capital-preservation, maximum-drawdown-minimization perspective.

### 5. Adversarial Assurance Agent (Tier 6)
17. **Stress-Test Agent** (`T6.2`): Red-teams the winning thesis by generating counter-factual scenarios and stress conditions that would invalidate the trade.

---

## Components That Are NOT LLM Agents

In AMLIS, safety-critical, numerical, and regulatory decisions are strictly separated from LLM generation. The following components are **NOT** LLM agents:

1. **Quant Ensemble (`services/quant_ensemble/`)**:
   - Machine learning models (Gradient-Boosted Trees, GPU-trained LSTM/TCN sequence models, and stacking meta-learners).
   - Operates strictly on numerical, point-in-time feature matrices and produces calibrated probability distributions.

2. **Verifier (`services/trust_assurance/`)**:
   - Deterministic grounding engine that verifies LLM claims against factual figures in the point-in-time store.
   - Flags ungrounded reasoning or hallucinations without using generative LLM loops.

3. **Event-Severity Scorer (`services/system1/` or `services/regime/`)**:
   - Statistical anomaly detector and autoencoder that quantifies event shocks numerically into `shock_magnitude` values.

4. **Fine-Tuned Decision Model / System 1 (`services/system1/`)**:
   - Low-latency local Small Language Model (SLM) task heads (e.g. fine-tuned classification heads) used for synchronous classification, escalation flags, and latency-critical screening.

5. **Deterministic Risk Gate (`services/risk_gate/`)**:
   - Pure mathematical rule engine enforcing maximum drawdown limits, position sizing bounds, volatility scaling, and the emergency kill-switch. No LLM or model can override this gate.

6. **Compliance Gate (`services/compliance_gate/`)**:
   - Deterministic rule engine enforcing regulatory constraints, wash-sale rules, and mandate bounds derived from OKF knowledge bundles.

7. **RL Regime Controller (`services/rl_controller/`)**:
   - Bounded reinforcement learning policy or state machine that selects the orchestration coordination mode.

8. **Audit Ledger (`services/ledger/`)**:
   - Cryptographically hash-chained, append-only ledger recording all inputs, predictions, decisions, and rationales with tamper-evident verification.
