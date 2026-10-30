"""Permanent leakage-regression tests for PointInTimeStore (T0.5 / T0.11).

Proves that no future data can ever be retrieved by queries at decision time `as_of`.
"""

from datetime import UTC, datetime, timedelta

import pytest

from libs.common.pit import LookAheadError, assert_point_in_time
from libs.contracts.models import OHLCVBar
from services.data_plane import PointInTimeStore

DECISION_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def _bar(offset_minutes: int, lag_seconds: int = 10) -> OHLCVBar:
    ts = DECISION_TIME + timedelta(minutes=offset_minutes)
    knowable = ts + timedelta(seconds=lag_seconds)
    return OHLCVBar(
        symbol="BTC/USD",
        timestamp=ts,
        knowable_at=knowable,
        open=50000.0,
        high=50100.0,
        low=49900.0,
        close=50050.0,
        volume=1.0,
    )


def test_pit_store_never_returns_bars_knowable_after_as_of() -> None:
    """Store loaded with future bars must strictly filter them out at decision time."""
    store = PointInTimeStore()

    # Insert 10 bars in the past, 1 bar closing at DECISION_TIME (knowable 10s later),
    # and 10 bars in the future
    for m in range(-10, 11):
        store.insert(_bar(offset_minutes=m, lag_seconds=10))

    # Query as of DECISION_TIME
    bars = store.get_bars("BTC/USD", as_of=DECISION_TIME)

    # Every single returned bar MUST have knowable_at <= DECISION_TIME
    assert len(bars) > 0
    for bar in bars:
        assert bar.knowable_at <= DECISION_TIME
        # assert_point_in_time must succeed without LookAheadError
        assert_point_in_time(bar.knowable_at, DECISION_TIME)

    # The bar that closed at DECISION_TIME has knowable_at = DECISION_TIME + 10s,
    # so it MUST NOT be returned at DECISION_TIME!
    closing_bar = [b for b in bars if b.timestamp == DECISION_TIME]
    assert len(closing_bar) == 0

    # Moving as_of forward by 10s reveals the bar
    bars_10s_later = store.get_bars("BTC/USD", as_of=DECISION_TIME + timedelta(seconds=10))
    closing_bar_later = [b for b in bars_10s_later if b.timestamp == DECISION_TIME]
    assert len(closing_bar_later) == 1


def test_leakage_assertion_triggers_if_future_bar_examined() -> None:
    """Demonstrate that manually attempting to consume a future bar triggers LookAheadError."""
    future_bar = _bar(offset_minutes=1, lag_seconds=5)
    with pytest.raises(LookAheadError):
        assert_point_in_time(future_bar.knowable_at, DECISION_TIME)


def test_rolling_window_pit_integrity() -> None:
    """Simulate a rolling decision loop and ensure at each step no future bars are ever seen."""
    store = PointInTimeStore()
    total_bars = 50
    for i in range(total_bars):
        store.insert(_bar(offset_minutes=i, lag_seconds=5))

    for step in range(5, 30):
        current_decision_time = DECISION_TIME + timedelta(minutes=step)
        visible_bars = store.get_bars("BTC/USD", as_of=current_decision_time)

        # Ensure no bar in visible_bars has knowable_at > current_decision_time
        for b in visible_bars:
            assert b.knowable_at <= current_decision_time
