"""Unit tests for Macro calendar loader and store (T0.7)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from services.data_plane import (
    MacroCalendarLoader,
    MacroCalendarStore,
    MacroEvent,
    MacroEventType,
    PointInTimeStore,
)

T0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def make_macro_event(
    event_id: str = "cpi_2026_01",
    event_type: str = MacroEventType.CPI,
    scheduled: datetime = T0,
    knowable: datetime | None = None,
    actual: float | None = 3.2,
    consensus: float | None = 3.0,
    previous: float | None = 2.9,
    is_shock: bool = False,
) -> MacroEvent:
    return MacroEvent(
        event_id=event_id,
        event_type=event_type,
        country="US",
        scheduled_time=scheduled,
        knowable_at=knowable or scheduled,
        actual=actual,
        consensus=consensus,
        previous=previous,
        surprise=(actual - consensus) if (actual is not None and consensus is not None) else None,
        is_shock=is_shock,
    )


def test_macro_event_creation_and_surprise() -> None:
    event = make_macro_event(actual=3.4, consensus=3.1)
    assert event.event_type == MacroEventType.CPI
    assert event.surprise == pytest.approx(0.3)
    assert event.knowable_at == T0


def test_macro_event_invalid_pit_raises() -> None:
    with pytest.raises(ValidationError, match="cannot be before"):
        MacroEvent(
            event_id="bad",
            event_type=MacroEventType.NFP,
            scheduled_time=T0,
            knowable_at=T0 - timedelta(minutes=1),  # Future knowledge violation!
        )


def test_censor_unreleased() -> None:
    event = make_macro_event(
        scheduled=T0 + timedelta(hours=1),
        knowable=T0 + timedelta(hours=1),
        actual=250.0,
        consensus=200.0,
        is_shock=True,
    )
    # At T0, the event has not yet been released
    censored = event.censor_unreleased(as_of=T0)
    assert censored.actual is None
    assert censored.surprise is None
    assert censored.is_shock is False
    assert censored.consensus == 200.0  # Consensus was known in advance

    # At T0 + 2h, it is released
    released = event.censor_unreleased(as_of=T0 + timedelta(hours=2))
    assert released.actual == 250.0
    assert released.is_shock is True


def test_calendar_store_pit_filtering() -> None:
    store = MacroCalendarStore()
    e_past = make_macro_event("cpi_1", MacroEventType.CPI, scheduled=T0 - timedelta(days=30))
    e_today = make_macro_event(
        "nfp_1",
        MacroEventType.NFP,
        scheduled=T0,
        knowable=T0 + timedelta(seconds=15),
        actual=180.0,
    )
    e_future = make_macro_event("rate_1", MacroEventType.RATE_DECISION, scheduled=T0 + timedelta(days=7))

    store.insert_batch([e_past, e_today, e_future])
    assert store.count() == 3

    # At T0 exactly: e_today is not knowable yet because knowable_at is T0 + 15s
    released_t0 = store.get_released_events(as_of=T0)
    assert len(released_t0) == 1
    assert released_t0[0].event_id == "cpi_1"

    # At T0 + 15s: e_today is knowable
    released_t0_15s = store.get_released_events(as_of=T0 + timedelta(seconds=15))
    assert len(released_t0_15s) == 2
    assert any(e.event_id == "nfp_1" for e in released_t0_15s)

    # Filter by event_type
    nfp_only = store.get_released_events(as_of=T0 + timedelta(seconds=15), event_type=MacroEventType.NFP)
    assert len(nfp_only) == 1
    assert nfp_only[0].event_id == "nfp_1"


def test_calendar_store_get_schedule_censoring() -> None:
    store = MacroCalendarStore()
    e_upcoming = make_macro_event(
        "rate_upcoming",
        MacroEventType.RATE_DECISION,
        scheduled=T0 + timedelta(days=2),
        knowable=T0 + timedelta(days=2),
        actual=5.25,
        consensus=5.25,
    )
    store.insert(e_upcoming)

    # Schedule query for the next 7 days as of T0
    schedule = store.get_schedule(as_of=T0, lookahead=timedelta(days=7))
    assert len(schedule) == 1
    # Actual result must be censored!
    assert schedule[0].actual is None
    assert schedule[0].consensus == 5.25


def test_macro_calendar_loader_from_csv(tmp_path: Path) -> None:
    csv_file = tmp_path / "macro.csv"
    csv_content = """event_id,event_type,scheduled_time,knowable_at,actual,consensus,previous,is_shock
cpi_jan,cpi,2026-01-15T12:00:00Z,2026-01-15T12:00:05Z,3.2,3.0,2.9,false
nfp_jan,nfp,2026-01-16T13:30:00Z,2026-01-16T13:30:02Z,215,200,195,false
rate_fomc,rate_decision,2026-01-28T19:00:00Z,,5.25,5.25,5.50,false
"""
    csv_file.write_text(csv_content, encoding="utf-8")

    events = MacroCalendarLoader.from_csv(csv_file, default_release_lag_seconds=2.0)
    assert len(events) == 3

    cpi = events[0]
    assert cpi.event_id == "cpi_jan"
    assert cpi.event_type == "cpi"
    assert cpi.actual == 3.2
    assert cpi.surprise == pytest.approx(0.2)
    assert cpi.knowable_at == datetime(2026, 1, 15, 12, 0, 5, tzinfo=UTC)

    rate = events[2]
    assert rate.event_id == "rate_fomc"
    assert rate.event_type == "rate_decision"
    # Default lag used
    assert rate.knowable_at == datetime(2026, 1, 28, 19, 0, 2, tzinfo=UTC)


def test_point_in_time_store_macro_integration() -> None:
    store = PointInTimeStore()
    event = make_macro_event("cpi_test", scheduled=T0 - timedelta(hours=1))
    store.insert_macro_event(event)

    events = store.get_macro_events(as_of=T0)
    assert len(events) == 1
    assert events[0].event_id == "cpi_test"

    schedule = store.get_macro_schedule(as_of=T0, lookahead=timedelta(days=1))
    assert len(schedule) == 0  # Event was in the past

    store.clear()
    assert len(store.get_macro_events(as_of=T0)) == 0
