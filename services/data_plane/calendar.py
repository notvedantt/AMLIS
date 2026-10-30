"""Macro calendar loader and store for AMLIS (T0.7).

Loads and queries scheduled economic releases (CPI, NFP, interest rate decisions)
with strict point-in-time knowability guarantees.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from libs.common.pit import assert_point_in_time


class MacroEventType(StrEnum):
    CPI = "cpi"
    NFP = "nfp"
    RATE_DECISION = "rate_decision"
    GDP = "gdp"
    PMI = "pmi"
    OTHER = "other"


def _parse_ts(val: Any) -> datetime:
    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, int | float):
        if val > 1e11:
            val = val / 1000.0
        dt = datetime.fromtimestamp(val, tz=UTC)
    elif isinstance(val, str):
        clean_str = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
    else:
        raise TypeError(f"Cannot parse timestamp: {val}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


class MacroEvent(BaseModel):
    """An economic calendar event with point-in-time release knowability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(min_length=1)
    event_type: MacroEventType | str
    country: str = "US"
    scheduled_time: datetime
    knowable_at: datetime
    actual: float | None = None
    consensus: float | None = None
    previous: float | None = None
    surprise: float | None = None
    is_shock: bool = False

    @model_validator(mode="after")
    def _validate_pit(self) -> MacroEvent:
        if self.knowable_at < self.scheduled_time:
            raise ValueError(
                f"knowable_at ({self.knowable_at.isoformat()}) cannot be before "
                f"scheduled_time ({self.scheduled_time.isoformat()})"
            )
        return self

    def censor_unreleased(self, as_of: datetime) -> MacroEvent:
        """Return a copy of this event with actual/surprise censored if not yet released at as_of."""
        if self.knowable_at > as_of:
            return self.model_copy(update={"actual": None, "surprise": None, "is_shock": False})
        return self


class MacroCalendarStore:
    """Point-in-time store for macroeconomic calendar events."""

    def __init__(self) -> None:
        self._events: list[MacroEvent] = []

    def insert(self, event: MacroEvent) -> None:
        """Insert or replace an event by event_id."""
        for idx, existing in enumerate(self._events):
            if existing.event_id == event.event_id:
                self._events[idx] = event
                return
        self._events.append(event)
        self._events.sort(key=lambda e: e.scheduled_time)

    def insert_batch(self, events: Iterable[MacroEvent]) -> int:
        count = 0
        for e in events:
            self.insert(e)
            count += 1
        return count

    def get_released_events(
        self,
        as_of: datetime,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        event_type: str | None = None,
    ) -> tuple[MacroEvent, ...]:
        """Retrieve macro events whose actual values are knowable as of `as_of`."""
        effective_end = end_time if end_time is not None else as_of
        if effective_end > as_of:
            effective_end = as_of

        results: list[MacroEvent] = []
        for e in self._events:
            if start_time is not None and e.scheduled_time < start_time:
                continue
            if e.scheduled_time > effective_end:
                continue
            if e.knowable_at > as_of:
                continue
            if event_type is not None and e.event_type != event_type:
                continue

            assert_point_in_time(e.knowable_at, as_of)
            results.append(e)

        return tuple(results)

    def get_schedule(
        self,
        as_of: datetime,
        lookahead: timedelta,
        event_type: str | None = None,
    ) -> tuple[MacroEvent, ...]:
        """Retrieve scheduled events within [as_of, as_of + lookahead].

        Unreleased outcomes are strictly censored to prevent future leak.
        """
        window_end = as_of + lookahead
        results: list[MacroEvent] = []

        for e in self._events:
            if as_of <= e.scheduled_time <= window_end:
                if event_type is not None and e.event_type != event_type:
                    continue
                results.append(e.censor_unreleased(as_of))

        return tuple(results)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()


class MacroCalendarLoader:
    """Loader to parse CSV records into MacroEvent objects and load them into stores."""

    @staticmethod
    def to_event(record: dict[str, Any], default_release_lag_seconds: float = 0.0) -> MacroEvent:
        event_id = str(record.get("event_id") or record.get("id") or "")
        if not event_id:
            raise ValueError(f"Missing event_id in record: {record}")

        event_type = str(record.get("event_type") or record.get("type") or "other").lower()
        country = str(record.get("country") or "US").upper()

        sched_raw = record.get("scheduled_time") or record.get("time") or record.get("date")
        if sched_raw is None or str(sched_raw).strip() == "":
            raise ValueError(f"Missing scheduled_time in record: {record}")
        scheduled_time = _parse_ts(sched_raw)

        knowable_raw = record.get("knowable_at")
        if knowable_raw not in (None, "", "null"):
            knowable_at = _parse_ts(knowable_raw)
        else:
            knowable_at = scheduled_time + timedelta(seconds=default_release_lag_seconds)

        actual_val = record.get("actual")
        actual = float(actual_val) if actual_val not in (None, "", "null") else None

        consensus_val = record.get("consensus")
        consensus = float(consensus_val) if consensus_val not in (None, "", "null") else None

        previous_val = record.get("previous")
        previous = float(previous_val) if previous_val not in (None, "", "null") else None

        surprise_val = record.get("surprise")
        if surprise_val not in (None, "", "null"):
            surprise = float(surprise_val)
        elif actual is not None and consensus is not None:
            surprise = actual - consensus
        else:
            surprise = None

        shock_raw = record.get("is_shock")
        is_shock = bool(shock_raw) if shock_raw not in (None, "", "null") else False

        return MacroEvent(
            event_id=event_id,
            event_type=event_type,
            country=country,
            scheduled_time=scheduled_time,
            knowable_at=knowable_at,
            actual=actual,
            consensus=consensus,
            previous=previous,
            surprise=surprise,
            is_shock=is_shock,
        )

    @classmethod
    def from_csv(
        cls,
        path: Path | str,
        default_release_lag_seconds: float = 0.0,
    ) -> tuple[MacroEvent, ...]:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"Macro calendar CSV not found: {file_path}")

        events: list[MacroEvent] = []
        with file_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError(f"Empty or headerless CSV: {file_path}")

            for row_idx, row in enumerate(reader):
                normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k is not None}
                try:
                    event = cls.to_event(normalized, default_release_lag_seconds=default_release_lag_seconds)
                    events.append(event)
                except Exception as exc:
                    raise ValueError(f"Error parsing row {row_idx + 1} in {file_path}: {exc}") from exc

        return tuple(events)
