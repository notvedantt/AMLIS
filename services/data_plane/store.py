"""Point-in-time market data store for AMLIS (T0.5).

Enforces Principle 3: no component sees data dated after its decision.
Every query requires an explicit `as_of` timestamp. Any record whose
`knowable_at` is strictly after `as_of` is invisible to callers.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime

from libs.common.pit import assert_point_in_time
from libs.contracts.models import OHLCVBar


class PointInTimeStore:
    """In-memory point-in-time store for OHLCV bars.

    Records are stored ordered by timestamp and indexed by symbol.
    Queries always filter on ``knowable_at <= as_of``, ensuring zero look-ahead bias.
    """

    def __init__(self) -> None:
        self._bars: dict[str, list[OHLCVBar]] = defaultdict(list)

    def insert(self, bar: OHLCVBar) -> None:
        """Insert a single OHLCV bar into the store."""
        bars = self._bars[bar.symbol]
        # Maintain sorted order by bar timestamp
        # If a bar with the same timestamp already exists, replace it
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
        """Query bars for a symbol knowable as of `as_of`.

        Parameters
        ----------
        symbol:
            Asset ticker or pair (e.g. 'BTC/USD').
        as_of:
            Decision timestamp. Absolutely no bar with `knowable_at > as_of` will be returned.
        start_time:
            Optional lower bound for bar close timestamp (inclusive).
        end_time:
            Optional upper bound for bar close timestamp (inclusive). Cannot exceed `as_of`.
        limit:
            Optional maximum number of bars to return (most recent first if limited).
        """
        if symbol not in self._bars:
            return ()

        # An end_time in the future relative to as_of makes no sense in a PIT query
        effective_end = end_time if end_time is not None else as_of
        if effective_end > as_of:
            effective_end = as_of

        results: list[OHLCVBar] = []
        for bar in self._bars[symbol]:
            # Hard PIT check: bar close must be within range
            if start_time is not None and bar.timestamp < start_time:
                continue
            if bar.timestamp > effective_end:
                continue

            # Core invariant: knowable_at must be <= as_of
            if bar.knowable_at > as_of:
                continue

            # Double check with pit assertion helper to guarantee safety
            assert_point_in_time(bar.knowable_at, as_of)
            results.append(bar)

        if limit is not None and limit > 0:
            results = results[-limit:]

        return tuple(results)

    def get_latest_bar(self, symbol: str, as_of: datetime) -> OHLCVBar | None:
        """Retrieve the single most recent bar for a symbol knowable as of `as_of`."""
        bars = self.get_bars(symbol=symbol, as_of=as_of, limit=1)
        return bars[0] if bars else None

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
