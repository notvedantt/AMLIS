"""Leakage regression tests for Sentiment, Macro, and Fundamental Features (T0.9 / T0.11).

Guarantees that no sentiment, fundamental, or macro data can leak into decisions
before its explicit point-in-time knowability timestamp.
"""

from datetime import UTC, datetime, timedelta

import pytest

from libs.common.pit import LookAheadError
from libs.contracts.models import OHLCVBar
from services.feature_plane import (
    FeatureEngine,
    FundamentalRecord,
    MacroRecord,
    SentimentRecord,
    extract_fundamentals,
    extract_macro_features,
    extract_sentiment,
)

DECISION_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def _sample_bar() -> OHLCVBar:
    return OHLCVBar(
        symbol="BTC/USD",
        timestamp=DECISION_TIME - timedelta(minutes=1),
        knowable_at=DECISION_TIME - timedelta(minutes=1),
        open=50000.0,
        high=50100.0,
        low=49900.0,
        close=50050.0,
        volume=1.0,
    )


def test_future_sentiment_triggers_lookahead_error() -> None:
    future_sentiment = SentimentRecord(
        symbol="BTC/USD",
        timestamp=DECISION_TIME + timedelta(minutes=5),
        knowable_at=DECISION_TIME + timedelta(minutes=5),
        score=0.9,
    )
    with pytest.raises(LookAheadError):
        extract_sentiment([future_sentiment], as_of=DECISION_TIME)


def test_future_macro_event_triggers_lookahead_error() -> None:
    future_macro = MacroRecord(
        event_id="future_cpi",
        event_type="cpi",
        scheduled_time=DECISION_TIME + timedelta(hours=1),
        knowable_at=DECISION_TIME + timedelta(hours=1),
        surprise=0.5,
    )
    with pytest.raises(LookAheadError):
        extract_macro_features([future_macro], as_of=DECISION_TIME)


def test_future_fundamental_triggers_lookahead_error() -> None:
    future_fund = FundamentalRecord(
        symbol="BTC/USD",
        timestamp=DECISION_TIME + timedelta(days=1),
        knowable_at=DECISION_TIME + timedelta(days=1),
        metric_name="pe_ratio",
        value=15.0,
    )
    with pytest.raises(LookAheadError):
        extract_fundamentals([future_fund], as_of=DECISION_TIME)


def test_feature_engine_rejects_future_sentiment_or_macro() -> None:
    engine = FeatureEngine()
    bars = [_sample_bar()]

    future_macro = MacroRecord(
        event_id="future_shock",
        event_type="fomc",
        scheduled_time=DECISION_TIME + timedelta(seconds=10),
        knowable_at=DECISION_TIME + timedelta(seconds=10),
        is_shock=True,
    )

    with pytest.raises(LookAheadError):
        engine.compute_features(
            bars=bars,
            as_of=DECISION_TIME,
            macro_records=[future_macro],
        )
