"""Published, versioned contracts between services (see docs/guides/contracts.md).

All models are frozen and reject unknown fields. Changing a field is a breaking
change: bump CONTRACT_VERSION and get both Vedant and Aditya to approve.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION = "0.1.0"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class CoordinationMode(StrEnum):
    QUANT_ONLY = "quant_only"
    QUANT_PLUS_ONE_LLM = "quant_plus_one_llm"
    FULL_DEBATE = "full_debate"
    FRONTIER_REVIEW = "frontier_review"


class EscalationLevel(StrEnum):
    """Graded escalation levels emitted by the trust-assurance layer (T6.4)."""

    NONE = "none"
    FLAG = "flag"
    REDUCE_SIZE = "reduce_size"
    HALT = "halt"


# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------


class OHLCVBar(Frozen):
    """A single OHLCV bar with a point-in-time knowability stamp (T0.5).

    ``knowable_at`` is the timestamp at which this bar became available to a
    decision system — always >= ``timestamp`` due to publication lag.
    """

    symbol: str
    timestamp: datetime  # bar close time
    knowable_at: datetime  # when this bar was actually receivable
    open: float = Field(gt=0.0)
    high: float = Field(gt=0.0)
    low: float = Field(gt=0.0)
    close: float = Field(gt=0.0)
    volume: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _ohlcv_sane(self) -> OHLCVBar:
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.high < self.open or self.high < self.close:
            raise ValueError("high must be >= open and close")
        if self.low > self.open or self.low > self.close:
            raise ValueError("low must be <= open and close")
        if self.knowable_at < self.timestamp:
            raise ValueError("knowable_at must be >= timestamp (no future knowledge)")
        return self


# ---------------------------------------------------------------------------
# Regime
# ---------------------------------------------------------------------------


class RegimeState(Frozen):
    timestamp: datetime
    regime_probs: tuple[float, float, float]  # low_vol, transitional, high_vol
    shock_flag: bool
    shock_magnitude: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _probs_sum_to_one(self) -> RegimeState:
        if abs(sum(self.regime_probs) - 1.0) > 1e-6 or min(self.regime_probs) < 0:
            raise ValueError("regime_probs must be non-negative and sum to 1")
        return self


# ---------------------------------------------------------------------------
# Quant / LLM predictions
# ---------------------------------------------------------------------------


class ModelPrediction(Frozen):
    source: str
    timestamp: datetime
    direction: Direction
    confidence: float = Field(ge=0.0, le=1.0)
    features_used: tuple[str, ...]
    abstain: bool = False


class AnalystReport(Frozen):
    """Structured output from one LLM analyst role (T2.2, T2.3, T2.4).

    ``tool_call_trace`` is a tuple of opaque serialisable records so callers
    can log what tools were invoked without importing LLM provider types.
    """

    analyst_role: str  # e.g. "technical", "fundamental", "news"
    timestamp: datetime
    symbol: str
    direction: Direction
    conviction: float = Field(ge=0.0, le=1.0)
    rationale: str
    tool_call_trace: tuple[Any, ...] = ()


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class RoutingAction(Frozen):
    regime_state_ref: str
    coordination_mode: CoordinationMode
    signal_weights: dict[str, float]
    threshold_adjustments: dict[str, float]
    policy_version: str


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------


class KnowledgeRef(Frozen):
    bundle_id: str
    type: str
    version: str
    path: str


# ---------------------------------------------------------------------------
# Trust & assurance
# ---------------------------------------------------------------------------


class VerifierResult(Frozen):
    prediction_ref: str
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)


class EscalationAction(Frozen):
    """Decision emitted by the graded-escalation layer (T6.4)."""

    prediction_ref: str
    level: EscalationLevel
    trigger: str  # human-readable reason, logged to ledger


# ---------------------------------------------------------------------------
# Risk & compliance gates
# ---------------------------------------------------------------------------


class RiskDecision(Frozen):
    prediction_ref: str
    routing_ref: str
    position_size: float = Field(ge=0.0)
    approved: bool
    reason: str
    limits_checked: tuple[str, ...]


class ComplianceDecision(Frozen):
    risk_decision_ref: str
    cleared: bool
    reason: str
    rules_checked: tuple[str, ...]


# ---------------------------------------------------------------------------
# Audit ledger
# ---------------------------------------------------------------------------


class LedgerEntry(Frozen):
    decision_hash: str
    inputs_hash: str
    timestamp: datetime
    rationale: str
    outcome: str | None = None  # nullable until resolved
