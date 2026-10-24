"""Published, versioned contracts between services (see docs/guides/contracts.md).

All models are frozen and reject unknown fields. Changing a field is a breaking
change: bump CONTRACT_VERSION and get both Vedant and Aditya to approve.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION = "0.1.0"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class CoordinationMode(StrEnum):
    QUANT_ONLY = "quant_only"
    QUANT_PLUS_ONE_LLM = "quant_plus_one_llm"
    FULL_DEBATE = "full_debate"
    FRONTIER_REVIEW = "frontier_review"


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


class ModelPrediction(Frozen):
    source: str
    timestamp: datetime
    direction: Direction
    confidence: float = Field(ge=0.0, le=1.0)
    features_used: tuple[str, ...]
    abstain: bool = False


class RoutingAction(Frozen):
    regime_state_ref: str
    coordination_mode: CoordinationMode
    signal_weights: dict[str, float]
    threshold_adjustments: dict[str, float]
    policy_version: str


class KnowledgeRef(Frozen):
    bundle_id: str
    type: str
    version: str
    path: str


class VerifierResult(Frozen):
    prediction_ref: str
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)


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


class LedgerEntry(Frozen):
    decision_hash: str
    inputs_hash: str
    timestamp: datetime
    rationale: str
    outcome: str | None = None  # nullable until resolved
