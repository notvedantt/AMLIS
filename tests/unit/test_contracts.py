"""Comprehensive unit tests for libs/contracts/models.py (T0.3).

Every contract is frozen, rejects unknown fields, and validates its invariants.
Adding a field to any contract is a breaking change — bump CONTRACT_VERSION.
"""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from libs.contracts import (
    AnalystReport,
    ComplianceDecision,
    CoordinationMode,
    Direction,
    EscalationAction,
    EscalationLevel,
    KnowledgeRef,
    LedgerEntry,
    ModelPrediction,
    OHLCVBar,
    RegimeState,
    RiskDecision,
    RoutingAction,
    VerifierResult,
)
from libs.contracts.models import CONTRACT_VERSION

NOW = datetime(2026, 1, 5, 12, tzinfo=UTC)
LATER = NOW + timedelta(minutes=1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ohlcv(**kwargs: object) -> OHLCVBar:
    defaults: dict[str, object] = dict(
        symbol="BTC/USD",
        timestamp=NOW,
        knowable_at=LATER,
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=1000.0,
    )
    defaults.update(kwargs)
    return OHLCVBar(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------


def test_contract_version_is_semver() -> None:
    parts = CONTRACT_VERSION.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# OHLCVBar
# ---------------------------------------------------------------------------


class TestOHLCVBar:
    def test_valid_bar(self) -> None:
        bar = _ohlcv()
        assert bar.symbol == "BTC/USD"
        assert bar.high >= bar.low

    def test_knowable_at_must_not_precede_timestamp(self) -> None:
        with pytest.raises(ValidationError, match="knowable_at"):
            _ohlcv(knowable_at=NOW - timedelta(seconds=1))

    def test_knowable_at_equal_to_timestamp_is_allowed(self) -> None:
        _ohlcv(knowable_at=NOW)  # same instant is fine

    def test_high_less_than_low_fails(self) -> None:
        with pytest.raises(ValidationError, match="high"):
            _ohlcv(high=94.0, low=95.0)

    def test_high_less_than_open_fails(self) -> None:
        with pytest.raises(ValidationError, match="high"):
            _ohlcv(open=115.0, high=110.0, low=95.0, close=105.0)

    def test_high_less_than_close_fails(self) -> None:
        with pytest.raises(ValidationError, match="high"):
            _ohlcv(open=100.0, high=110.0, low=95.0, close=115.0)

    def test_low_greater_than_open_fails(self) -> None:
        with pytest.raises(ValidationError, match="low"):
            _ohlcv(open=90.0, high=110.0, low=95.0, close=105.0)

    def test_negative_open_fails(self) -> None:
        with pytest.raises(ValidationError):
            _ohlcv(open=-1.0)

    def test_volume_zero_is_allowed(self) -> None:
        _ohlcv(volume=0.0)

    def test_frozen(self) -> None:
        bar = _ohlcv()
        with pytest.raises(ValidationError):
            bar.close = 200.0  # type: ignore[misc]

    def test_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            OHLCVBar(  # type: ignore[call-arg]
                symbol="X",
                timestamp=NOW,
                knowable_at=LATER,
                open=1.0,
                high=2.0,
                low=0.5,
                close=1.5,
                volume=100.0,
                extra_field="bad",
            )


# ---------------------------------------------------------------------------
# RegimeState
# ---------------------------------------------------------------------------


class TestRegimeState:
    def test_valid_regime(self) -> None:
        r = RegimeState(timestamp=NOW, regime_probs=(0.5, 0.3, 0.2), shock_flag=False, shock_magnitude=0.0)
        assert sum(r.regime_probs) == pytest.approx(1.0)

    def test_probs_not_summing_to_one(self) -> None:
        with pytest.raises(ValidationError, match="regime_probs"):
            RegimeState(timestamp=NOW, regime_probs=(0.5, 0.5, 0.5), shock_flag=False, shock_magnitude=0.0)

    def test_negative_prob_rejected(self) -> None:
        with pytest.raises(ValidationError, match="regime_probs"):
            RegimeState(timestamp=NOW, regime_probs=(-0.1, 0.6, 0.5), shock_flag=False, shock_magnitude=0.0)

    def test_negative_shock_magnitude_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RegimeState(timestamp=NOW, regime_probs=(1.0, 0.0, 0.0), shock_flag=True, shock_magnitude=-0.1)

    def test_frozen(self) -> None:
        r = RegimeState(timestamp=NOW, regime_probs=(1.0, 0.0, 0.0), shock_flag=False, shock_magnitude=0.0)
        with pytest.raises(ValidationError):
            r.shock_flag = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ModelPrediction
# ---------------------------------------------------------------------------


class TestModelPrediction:
    def test_valid_prediction(self) -> None:
        p = ModelPrediction(
            source="gbt",
            timestamp=NOW,
            direction=Direction.LONG,
            confidence=0.75,
            features_used=("rsi", "macd"),
        )
        assert p.abstain is False

    def test_abstain_flag(self) -> None:
        p = ModelPrediction(
            source="gbt",
            timestamp=NOW,
            direction=Direction.FLAT,
            confidence=0.0,
            features_used=(),
            abstain=True,
        )
        assert p.abstain is True

    def test_confidence_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ModelPrediction(
                source="x", timestamp=NOW, direction=Direction.LONG, confidence=1.1, features_used=()
            )

    def test_confidence_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ModelPrediction(
                source="x", timestamp=NOW, direction=Direction.LONG, confidence=-0.1, features_used=()
            )

    def test_frozen_and_rejects_unknown(self) -> None:
        p = ModelPrediction(
            source="gbt", timestamp=NOW, direction=Direction.SHORT, confidence=0.6, features_used=("rsi",)
        )
        with pytest.raises(ValidationError):
            p.confidence = 0.9  # type: ignore[misc]
        with pytest.raises(ValidationError):
            ModelPrediction(  # type: ignore[call-arg]
                source="x",
                timestamp=NOW,
                direction=Direction.FLAT,
                confidence=0.5,
                features_used=(),
                surprise=1,
            )


# ---------------------------------------------------------------------------
# AnalystReport
# ---------------------------------------------------------------------------


class TestAnalystReport:
    def test_valid_report(self) -> None:
        r = AnalystReport(
            analyst_role="technical",
            timestamp=NOW,
            symbol="BTC/USD",
            direction=Direction.LONG,
            conviction=0.8,
            rationale="RSI oversold, MACD crossover imminent.",
        )
        assert r.tool_call_trace == ()

    def test_tool_call_trace_stored(self) -> None:
        r = AnalystReport(
            analyst_role="news",
            timestamp=NOW,
            symbol="ETH/USD",
            direction=Direction.SHORT,
            conviction=0.6,
            rationale="Negative sentiment spike.",
            tool_call_trace=({"tool": "fetch_news", "result": "negative"},),
        )
        assert len(r.tool_call_trace) == 1

    def test_conviction_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AnalystReport(
                analyst_role="x",
                timestamp=NOW,
                symbol="X",
                direction=Direction.FLAT,
                conviction=1.5,
                rationale="x",
            )

    def test_frozen(self) -> None:
        r = AnalystReport(
            analyst_role="fundamental",
            timestamp=NOW,
            symbol="SPY",
            direction=Direction.LONG,
            conviction=0.5,
            rationale="ok",
        )
        with pytest.raises(ValidationError):
            r.conviction = 0.9  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RoutingAction
# ---------------------------------------------------------------------------


class TestRoutingAction:
    def test_valid_routing(self) -> None:
        ra = RoutingAction(
            regime_state_ref="rs-001",
            coordination_mode=CoordinationMode.QUANT_ONLY,
            signal_weights={"gbt": 0.6, "lstm": 0.4},
            threshold_adjustments={"entry": 0.05},
            policy_version="v1.0",
        )
        assert ra.coordination_mode == CoordinationMode.QUANT_ONLY

    def test_all_coordination_modes_accepted(self) -> None:
        for mode in CoordinationMode:
            RoutingAction(
                regime_state_ref="r",
                coordination_mode=mode,
                signal_weights={},
                threshold_adjustments={},
                policy_version="v0",
            )


# ---------------------------------------------------------------------------
# KnowledgeRef
# ---------------------------------------------------------------------------


def test_knowledge_ref() -> None:
    ref = KnowledgeRef(
        bundle_id="okf-001",
        type="central_bank_gold",
        version="1.0",
        path="knowledge/okf/entities/sample-central-bank-gold.md",
    )
    assert ref.bundle_id == "okf-001"


# ---------------------------------------------------------------------------
# VerifierResult
# ---------------------------------------------------------------------------


def test_verifier_result_valid() -> None:
    vr = VerifierResult(prediction_ref="p-001", grounded=True, confidence=0.9)
    assert vr.grounded is True


def test_verifier_result_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        VerifierResult(prediction_ref="p", grounded=False, confidence=1.1)


# ---------------------------------------------------------------------------
# EscalationAction & EscalationLevel
# ---------------------------------------------------------------------------


class TestEscalation:
    def test_all_levels_accepted(self) -> None:
        for level in EscalationLevel:
            EscalationAction(prediction_ref="p-001", level=level, trigger="test trigger")

    def test_halt_level(self) -> None:
        ea = EscalationAction(
            prediction_ref="p-002", level=EscalationLevel.HALT, trigger="confidence collapse"
        )
        assert ea.level == EscalationLevel.HALT

    def test_frozen(self) -> None:
        ea = EscalationAction(prediction_ref="p", level=EscalationLevel.NONE, trigger="ok")
        with pytest.raises(ValidationError):
            ea.level = EscalationLevel.HALT  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RiskDecision
# ---------------------------------------------------------------------------


class TestRiskDecision:
    def test_approved(self) -> None:
        rd = RiskDecision(
            prediction_ref="p-001",
            routing_ref="r-001",
            position_size=0.02,
            approved=True,
            reason="within limits",
            limits_checked=("max_position", "correlation"),
        )
        assert rd.approved is True

    def test_rejected(self) -> None:
        rd = RiskDecision(
            prediction_ref="p-002",
            routing_ref="r-002",
            position_size=0.0,
            approved=False,
            reason="drawdown limit hit",
            limits_checked=("max_drawdown",),
        )
        assert rd.approved is False

    def test_negative_position_size_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RiskDecision(
                prediction_ref="p",
                routing_ref="r",
                position_size=-0.01,
                approved=True,
                reason="x",
                limits_checked=(),
            )


# ---------------------------------------------------------------------------
# ComplianceDecision
# ---------------------------------------------------------------------------


def test_compliance_decision_cleared() -> None:
    cd = ComplianceDecision(
        risk_decision_ref="rd-001",
        cleared=True,
        reason="all rules passed",
        rules_checked=("wash_sale", "position_limit"),
    )
    assert cd.cleared is True


def test_compliance_decision_blocked() -> None:
    cd = ComplianceDecision(
        risk_decision_ref="rd-002",
        cleared=False,
        reason="wash sale rule violated",
        rules_checked=("wash_sale",),
    )
    assert cd.cleared is False


# ---------------------------------------------------------------------------
# LedgerEntry
# ---------------------------------------------------------------------------


class TestLedgerEntry:
    def test_valid_entry_no_outcome(self) -> None:
        le = LedgerEntry(
            decision_hash="abc123",
            inputs_hash="def456",
            timestamp=NOW,
            rationale="Long BTC/USD: RSI oversold, regime low-vol.",
        )
        assert le.outcome is None

    def test_outcome_set(self) -> None:
        le = LedgerEntry(
            decision_hash="abc123",
            inputs_hash="def456",
            timestamp=NOW,
            rationale="Short ETH/USD: news shock.",
            outcome="profit: +1.2%",
        )
        assert le.outcome == "profit: +1.2%"

    def test_frozen(self) -> None:
        le = LedgerEntry(
            decision_hash="h1",
            inputs_hash="h2",
            timestamp=NOW,
            rationale="test",
        )
        with pytest.raises(ValidationError):
            le.rationale = "tampered"  # type: ignore[misc]
