"""Market data adapter for AMLIS (T0.5).

Converts raw market data feeds, dictionary records, or CSV files into strictly-typed
`OHLCVBar` contract models stamped with explicit `knowable_at` timestamps.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from libs.contracts.models import OHLCVBar


def _parse_timestamp(val: Any) -> datetime:
    """Parse a datetime value and ensure it is UTC-aware."""
    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, int | float):
        # Treat as unix epoch timestamp (seconds or milliseconds)
        if val > 1e11:  # Milliseconds heuristic
            val = val / 1000.0
        dt = datetime.fromtimestamp(val, tz=UTC)
    elif isinstance(val, str):
        # Handle ISO-8601 strings
        clean_str = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
    else:
        raise TypeError(f"Cannot parse timestamp from type {type(val)}: {val}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


class MarketDataAdapter:
    """Adapter that validates and converts external market data into OHLCVBar contracts."""

    def __init__(self, default_publication_lag_seconds: float = 0.0) -> None:
        if default_publication_lag_seconds < 0.0:
            raise ValueError("default_publication_lag_seconds must be >= 0")
        self.default_lag = timedelta(seconds=default_publication_lag_seconds)

    def to_bar(
        self,
        record: dict[str, Any],
        symbol_override: str | None = None,
        publication_lag: timedelta | None = None,
    ) -> OHLCVBar:
        """Parse a single dictionary record into an OHLCVBar.

        If `knowable_at` is not provided in `record`, it is computed as
        `timestamp + publication_lag` (or `default_lag`).
        """
        symbol = str(symbol_override or record.get("symbol") or "")
        if not symbol:
            raise ValueError("symbol is required in record or as symbol_override")

        ts_raw = record.get("timestamp") or record.get("time") or record.get("datetime")
        if ts_raw is None:
            raise ValueError(f"Missing timestamp in record: {record}")
        timestamp = _parse_timestamp(ts_raw)

        knowable_raw = record.get("knowable_at")
        if knowable_raw is not None:
            knowable_at = _parse_timestamp(knowable_raw)
        else:
            lag = publication_lag if publication_lag is not None else self.default_lag
            knowable_at = timestamp + lag

        return OHLCVBar(
            symbol=symbol,
            timestamp=timestamp,
            knowable_at=knowable_at,
            open=float(record["open"]),
            high=float(record["high"]),
            low=float(record["low"]),
            close=float(record["close"]),
            volume=float(record.get("volume", 0.0)),
        )

    def from_csv(
        self,
        path: Path | str,
        symbol: str,
        publication_lag_seconds: float | None = None,
    ) -> tuple[OHLCVBar, ...]:
        """Read a CSV file of OHLCV bars for a given symbol."""
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"Market data CSV not found: {file_path}")

        lag = (
            timedelta(seconds=publication_lag_seconds)
            if publication_lag_seconds is not None
            else self.default_lag
        )

        bars: list[OHLCVBar] = []
        with file_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError(f"Empty or headerless CSV: {file_path}")

            # Normalize column names to lowercase
            for row_idx, row in enumerate(reader):
                normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k is not None}
                try:
                    bar = self.to_bar(normalized, symbol_override=symbol, publication_lag=lag)
                    bars.append(bar)
                except Exception as exc:
                    raise ValueError(f"Error parsing row {row_idx + 1} in {file_path}: {exc}") from exc

        return tuple(bars)
