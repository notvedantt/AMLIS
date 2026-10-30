"""Leakage regression tests for Macro Calendar (T0.7 / T0.11).

Guarantees that macroeconomic surprises and actual release values are never accessible
prior to their point-in-time knowability timestamp.
"""

from datetime import UTC, datetime, timedelta

import pytest

from libs.common.pit import LookAheadError, assert_point_in_time
from services.data_plane import MacroCalendarStore, MacroEvent, MacroEventType

DECISION_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def test_unreleased_macro_event_is_invisible_to_pit_query() -> None:
    store = MacroCalendarStore()
    # Event scheduled at decision time, but release lag is 5 seconds
    event = MacroEvent(
        event_id="cpi_fomc_test",
        event_type=MacroEventType.CPI,
        country="US",
        scheduled_time=DECISION_TIME,
        knowable_at=DECISION_TIME + timedelta(seconds=5),
        actual=3.5,
        consensus=3.0,
        surprise=0.5,
        is_shock=True,
    )
    store.insert(event)

    # At DECISION_TIME: released events query must return empty
    released = store.get_released_events(as_of=DECISION_TIME)
    assert len(released) == 0

    # Direct manual access to knowable_at triggers LookAheadError
    with pytest.raises(LookAheadError):
        assert_point_in_time(event.knowable_at, DECISION_TIME)

    # 5 seconds later: becomes knowable
    released_later = store.get_released_events(as_of=DECISION_TIME + timedelta(seconds=5))
    assert len(released_later) == 1
    assert released_later[0].actual == 3.5


def test_schedule_query_censors_actual_for_future_releases() -> None:
    store = MacroCalendarStore()
    # 5 upcoming economic events over the next 5 days
    for day in range(1, 6):
        release_time = DECISION_TIME + timedelta(days=day)
        store.insert(
            MacroEvent(
                event_id=f"event_day_{day}",
                event_type=MacroEventType.NFP,
                country="US",
                scheduled_time=release_time,
                knowable_at=release_time + timedelta(seconds=2),
                actual=200.0 + day * 10,
                consensus=190.0,
                surprise=10.0 + day * 10,
                is_shock=False,
            )
        )

    schedule = store.get_schedule(as_of=DECISION_TIME, lookahead=timedelta(days=7))
    assert len(schedule) == 5

    # Crucial PIT invariant: every single future event must have its actual/surprise censored
    for event in schedule:
        assert event.actual is None
        assert event.surprise is None
        assert event.consensus == 190.0  # Consensus is knowable in advance
