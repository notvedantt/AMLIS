"""Point-in-time market data store for AMLIS (T0.5 / T0.7).

Enforces Principle 3: no component sees data dated after its decision.
Every query requires an explicit `as_of` timestamp. Any record whose
`knowable_at` is strictly after `as_of` is invisible to callers.
Supports both OHLCV bars and macroeconomic calendar releases.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta

from libs.common.pit import assert_point_in_time
from libs.contracts.models import OHLCVBar
from services.data_plane.calendar import MacroCalendarStore, MacroEvent


class PointInTimeStore:
    """In-memory point-in-time store for OHLCV bars and macro calendar events.

    Records are stored ordered by timestamp and indexed by symbol.
    Queries always filter on ``knowable_at <= as_of``, ensuring zero look-ahead bias.
    """

    def __init__(self) -> None:
        self._bars: dict[str, list[OHLCVBar]] = defaultdict(list)
        self._macro_calendar: MacroCalendarStore = MacroCalendarStore()

    def insert(self, bar: OHLCVBar) -> None:
        """Insert a single OHLCV bar into the store."""
        bars = self._bars[bar.symbol]
        for idx, existing in enumerate(bars):
            if existing.timestamp == bar.timestamp:
                bars[idx] = bar
                return
            if existing.timestamp > bar.timestamp:
                bars.insert(idx, bar)
                return
        bars.append(bar)

    def insert_batch(self, bars: Iterable[OHLCVBar]) -> int:
        """Insert multiple bars. Returns the count of inserted bars."""
        count = 0
        for b in bars:
            self.insert(b)
            count += 1
        return count

    def get_bars(
        self,
        symbol: str,
        as_of: datetime,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[OHLCVBar, ...]:
        """Query bars for a symbol knowable as of `as_of`."""
        if symbol not in self._bars:
            return ()

        effective_end = end_time if end_time is not None else as_of
        if effective_end > as_of:
            effective_end = as_of

        results: list[OHLCVBar] = []
        for bar in self._bars[symbol]:
            if start_time is not None and bar.timestamp < start_time:
                continue
            if bar.timestamp > effective_end:
                continue
            if bar.knowable_at > as_of:
                continue

            assert_point_in_time(bar.knowable_at, as_of)
            results.append(bar)

        if limit is not None and limit > 0:
            results = results[-limit:]

        return tuple(results)

    def get_latest_bar(self, symbol: str, as_of: datetime) -> OHLCVBar | None:
        """Retrieve the single most recent bar for a symbol knowable as of `as_of`."""
        bars = self.get_bars(symbol=symbol, as_of=as_of, limit=1)
        return bars[0] if bars else None

    # Macro calendar integration (T0.7)
    def insert_macro_event(self, event: MacroEvent) -> None:
        """Insert a single macro event into the calendar store."""
        self._macro_calendar.insert(event)

    def insert_macro_events(self, events: Iterable[MacroEvent]) -> int:
        """Insert multiple macro events into the calendar store."""
        return self._macro_calendar.insert_batch(events)

    def get_macro_events(
        self,
        as_of: datetime,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        event_type: str | None = None,
    ) -> tuple[MacroEvent, ...]:
        """Retrieve released macro events knowable as of `as_of`."""
        return self._macro_calendar.get_released_events(
            as_of=as_of,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
        )

    def get_macro_schedule(
        self,
        as_of: datetime,
        lookahead: timedelta,
        event_type: str | None = None,
    ) -> tuple[MacroEvent, ...]:
        """Retrieve upcoming schedule for [as_of, as_of + lookahead] (unreleased data censored)."""
        return self._macro_calendar.get_schedule(as_of=as_of, lookahead=lookahead, event_type=event_type)

    @property
    def macro_calendar(self) -> MacroCalendarStore:
        """Access the underlying MacroCalendarStore."""
        return self._macro_calendar

    def symbols(self) -> tuple[str, ...]:
        """Return all distinct symbols present in the store."""
        return tuple(sorted(self._bars.keys()))

    def count(self, symbol: str | None = None) -> int:
        """Return bar count for a symbol or total store count."""
        if symbol is not None:
            return len(self._bars.get(symbol, []))
        return sum(len(b) for b in self._bars.values())

    def clear(self) -> None:
        """Empty the store."""
        self._bars.clear()
        self._macro_calendar.clear()
