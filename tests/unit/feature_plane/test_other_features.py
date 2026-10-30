"""Unit tests for Sentiment, Macro-event, and Fundamental Features (T0.9)."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

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

T0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def make_test_bar(offset_mins: int = 0) -> OHLCVBar:
    ts = T0 + timedelta(minutes=offset_mins)
    return OHLCVBar(
        symbol="BTC/USD",
        timestamp=ts,
        knowable_at=ts + timedelta(seconds=1),
        open=50000.0,
        high=50100.0,
        low=49900.0,
        close=50050.0,
        volume=10.0,
    )


# ---------------------------------------------------------------------------
# Record Validation Tests
# ---------------------------------------------------------------------------


def test_sentiment_record_bounds() -> None:
    # Valid
    s = SentimentRecord(
        symbol="BTC/USD",
        timestamp=T0,
        knowable_at=T0,
        score=0.75,
    )
    assert s.score == 0.75

    # Out of [-1.0, 1.0] bounds
    with pytest.raises(ValidationError):
        SentimentRecord(symbol="BTC/USD", timestamp=T0, knowable_at=T0, score=1.5)

    # Inverted knowable_at < timestamp
    with pytest.raises(ValidationError, match="cannot precede"):
        SentimentRecord(
            symbol="BTC/USD",
            timestamp=T0,
            knowable_at=T0 - timedelta(seconds=1),
            score=0.5,
        )


def test_macro_record_validation() -> None:
    m = MacroRecord(
        event_id="cpi_1",
        event_type="cpi",
        scheduled_time=T0,
        knowable_at=T0 + timedelta(seconds=5),
        actual=3.2,
        consensus=3.0,
        surprise=0.2,
        is_shock=True,
        shock_magnitude=2.5,
    )
    assert m.surprise == 0.2
    assert m.is_shock is True
    assert m.shock_magnitude == 2.5


# ---------------------------------------------------------------------------
# Feature Extraction Unit Tests
# ---------------------------------------------------------------------------


def test_extract_sentiment() -> None:
    t_2h = T0 - timedelta(hours=2)
    s1 = SentimentRecord(symbol="BTC/USD", timestamp=t_2h, knowable_at=t_2h, score=0.2)
    t_1h = T0 - timedelta(hours=1)
    s2 = SentimentRecord(symbol="BTC/USD", timestamp=t_1h, knowable_at=t_1h, score=0.8)

    # Should pick s2 as the latest knowable score as of T0
    score = extract_sentiment([s1, s2], as_of=T0)
    assert score == 0.8

    # Empty records
    assert extract_sentiment([], as_of=T0) is None


def test_extract_macro_features() -> None:
    # CPI event 2 hours ago
    m_cpi = MacroRecord(
        event_id="cpi_1",
        event_type="cpi",
        scheduled_time=T0 - timedelta(hours=2),
        knowable_at=T0 - timedelta(hours=2),
        actual=3.4,
        consensus=3.1,
        surprise=0.3,
        is_shock=False,
    )
    # Geopolitical shock event 30 minutes ago
    m_shock = MacroRecord(
        event_id="shock_1",
        event_type="war_event",
        scheduled_time=T0 - timedelta(minutes=30),
        knowable_at=T0 - timedelta(minutes=30),
        is_shock=True,
        shock_magnitude=3.8,
    )

    cpi_surprise, shock_flag, shock_mag = extract_macro_features([m_cpi, m_shock], as_of=T0)
    assert cpi_surprise == 0.3
    assert shock_flag is True
    assert shock_mag == 3.8

    # No shocks
    cpi_surp_only, no_shock_flag, no_mag = extract_macro_features([m_cpi], as_of=T0)
    assert cpi_surp_only == 0.3
    assert no_shock_flag is False
    assert no_mag == 0.0


def test_extract_fundamentals() -> None:
    f1 = FundamentalRecord(
        symbol="SPY",
        timestamp=T0 - timedelta(days=1),
        knowable_at=T0 - timedelta(days=1),
        metric_name="pe_ratio",
        value=24.5,
    )
    res = extract_fundamentals([f1], as_of=T0)
    assert res == {"pe_ratio": 24.5}


# ---------------------------------------------------------------------------
# Full FeatureEngine Multi-plane Integration
# ---------------------------------------------------------------------------


def test_feature_engine_multi_plane() -> None:
    engine = FeatureEngine()
    bars = [make_test_bar(offset_mins=i) for i in range(30)]
    as_of = bars[-1].knowable_at + timedelta(seconds=1)

    s_rec = SentimentRecord(symbol="BTC/USD", timestamp=T0, knowable_at=T0, score=0.6)
    m_rec = MacroRecord(
        event_id="cpi_test",
        event_type="cpi",
        scheduled_time=T0,
        knowable_at=T0,
        surprise=0.25,
        is_shock=True,
        shock_magnitude=2.0,
    )

    vec = engine.compute_features(
        bars=bars,
        as_of=as_of,
        sentiment_records=[s_rec],
        macro_records=[m_rec],
    )

    assert vec.symbol == "BTC/USD"
    assert vec.get("sentiment_score") == 0.6
    assert vec.get("macro_surprise_cpi") == 0.25
    assert vec.get("macro_shock_flag") is True
    assert vec.get("macro_shock_magnitude") == 2.0
    assert "rsi_14" in vec.values
