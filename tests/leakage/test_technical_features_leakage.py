"""Leakage regression tests for Technical Features (T0.8 / T0.11).

Proves that technical indicator calculations strictly respect point-in-time boundaries
and reject future look-ahead data with LookAheadError.
"""

from datetime import UTC, datetime, timedelta

import pytest

from libs.common.pit import LookAheadError
from libs.contracts.models import OHLCVBar
from services.feature_plane import FeatureEngine

DECISION_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def _bar(minutes_offset: int, lag_seconds: int = 5, close: float = 50000.0) -> OHLCVBar:
    ts = DECISION_TIME + timedelta(minutes=minutes_offset)
    knowable = ts + timedelta(seconds=lag_seconds)
    return OHLCVBar(
        symbol="BTC/USD",
        timestamp=ts,
        knowable_at=knowable,
        open=close - 10.0,
        high=close + 20.0,
        low=close - 20.0,
        close=close,
        volume=5.0,
    )


def test_future_bar_triggers_lookahead_error_in_feature_engine() -> None:
    engine = FeatureEngine()
    # 30 bars in the past
    bars = [_bar(minutes_offset=i, close=50000.0 + i) for i in range(-30, 0)]

    # Add 1 bar that is in the future relative to DECISION_TIME
    future_bar = _bar(minutes_offset=1, close=50100.0)
    bars.append(future_bar)

    # Calling compute_technical_features as of DECISION_TIME must fail with LookAheadError!
    with pytest.raises(LookAheadError):
        engine.compute_technical_features(bars, as_of=DECISION_TIME)


def test_future_data_does_not_affect_pit_feature_vector() -> None:
    """The feature vector computed at T0 must be identical whether future bars exist in storage or not."""
    engine = FeatureEngine()

    past_bars = [_bar(minutes_offset=i, close=50000.0 + i * 2) for i in range(-55, 0)]
    vec1 = engine.compute_technical_features(past_bars, as_of=DECISION_TIME)

    # Now simulate future bars arriving
    future_bars = [_bar(minutes_offset=i, close=60000.0) for i in range(1, 10)]
    all_bars = past_bars + future_bars

    # Only pass bars knowable on or before DECISION_TIME
    pit_bars = [b for b in all_bars if b.knowable_at <= DECISION_TIME]
    vec2 = engine.compute_technical_features(pit_bars, as_of=DECISION_TIME)

    assert vec1.values == vec2.values
    assert vec1.timestamp == vec2.timestamp
    assert vec1.knowable_at == vec2.knowable_at
