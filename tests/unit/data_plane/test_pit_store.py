"""Unit tests for PointInTimeStore and MarketDataAdapter (T0.5)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from libs.contracts.models import OHLCVBar
from services.data_plane import MarketDataAdapter, PointInTimeStore

BASE_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def make_bar(
    symbol: str = "BTC/USD",
    minutes_offset: int = 0,
    lag_seconds: int = 5,
    close: float = 50000.0,
) -> OHLCVBar:
    ts = BASE_TIME + timedelta(minutes=minutes_offset)
    knowable = ts + timedelta(seconds=lag_seconds)
    return OHLCVBar(
        symbol=symbol,
        timestamp=ts,
        knowable_at=knowable,
        open=close - 10.0,
        high=close + 50.0,
        low=close - 50.0,
        close=close,
        volume=1.5,
    )


# ---------------------------------------------------------------------------
# PointInTimeStore Tests
# ---------------------------------------------------------------------------


def test_insert_and_count() -> None:
    store = PointInTimeStore()
    assert store.count() == 0
    assert store.symbols() == ()

    bar1 = make_bar("BTC/USD", minutes_offset=0)
    store.insert(bar1)
    assert store.count() == 1
    assert store.count("BTC/USD") == 1
    assert store.count("ETH/USD") == 0
    assert store.symbols() == ("BTC/USD",)


def test_batch_insert() -> None:
    store = PointInTimeStore()
    bars = [make_bar("BTC/USD", minutes_offset=i) for i in range(5)]
    count = store.insert_batch(bars)
    assert count == 5
    assert store.count("BTC/USD") == 5


def test_replace_existing_timestamp() -> None:
    store = PointInTimeStore()
    bar1 = make_bar("BTC/USD", minutes_offset=0, close=50000.0)
    bar2 = make_bar("BTC/USD", minutes_offset=0, close=51000.0)
    store.insert(bar1)
    store.insert(bar2)
    assert store.count("BTC/USD") == 1

    as_of = BASE_TIME + timedelta(minutes=1)
    latest = store.get_latest_bar("BTC/USD", as_of=as_of)
    assert latest is not None
    assert latest.close == 51000.0


def test_point_in_time_filtering() -> None:
    store = PointInTimeStore()
    # Bar 0: timestamp T+0m, knowable T+0m + 5s
    # Bar 1: timestamp T+1m, knowable T+1m + 5s
    # Bar 2: timestamp T+2m, knowable T+2m + 5s
    store.insert(make_bar("BTC/USD", minutes_offset=0, lag_seconds=5))
    store.insert(make_bar("BTC/USD", minutes_offset=1, lag_seconds=5))
    store.insert(make_bar("BTC/USD", minutes_offset=2, lag_seconds=5))

    # At decision time T+1m exactly, Bar 1 is NOT knowable yet because knowable_at is T+1m+5s!
    as_of_t1 = BASE_TIME + timedelta(minutes=1)
    bars_t1 = store.get_bars("BTC/USD", as_of=as_of_t1)
    assert len(bars_t1) == 1
    assert bars_t1[0].timestamp == BASE_TIME

    # At decision time T+1m + 5s, Bar 1 becomes knowable
    as_of_t1_plus = BASE_TIME + timedelta(minutes=1, seconds=5)
    bars_t1_plus = store.get_bars("BTC/USD", as_of=as_of_t1_plus)
    assert len(bars_t1_plus) == 2

    # Bar 2 is still not knowable
    assert not any(b.timestamp == BASE_TIME + timedelta(minutes=2) for b in bars_t1_plus)


def test_get_bars_start_and_end_filters() -> None:
    store = PointInTimeStore()
    for i in range(5):
        store.insert(make_bar("BTC/USD", minutes_offset=i, lag_seconds=0))

    as_of = BASE_TIME + timedelta(minutes=10)
    # Query with start_time
    start = BASE_TIME + timedelta(minutes=2)
    bars = store.get_bars("BTC/USD", as_of=as_of, start_time=start)
    assert len(bars) == 3
    assert bars[0].timestamp == start

    # Query with end_time
    end = BASE_TIME + timedelta(minutes=3)
    bars_end = store.get_bars("BTC/USD", as_of=as_of, end_time=end)
    assert len(bars_end) == 4
    assert bars_end[-1].timestamp == end

    # Query with limit
    bars_limited = store.get_bars("BTC/USD", as_of=as_of, limit=2)
    assert len(bars_limited) == 2
    assert bars_limited[-1].timestamp == BASE_TIME + timedelta(minutes=4)


def test_get_latest_bar() -> None:
    store = PointInTimeStore()
    assert store.get_latest_bar("BTC/USD", as_of=BASE_TIME) is None

    store.insert(make_bar("BTC/USD", minutes_offset=0, lag_seconds=10))
    # Before knowable
    assert store.get_latest_bar("BTC/USD", as_of=BASE_TIME) is None
    # After knowable
    latest = store.get_latest_bar("BTC/USD", as_of=BASE_TIME + timedelta(seconds=10))
    assert latest is not None
    assert latest.timestamp == BASE_TIME


def test_clear_store() -> None:
    store = PointInTimeStore()
    store.insert(make_bar("BTC/USD"))
    assert store.count() == 1
    store.clear()
    assert store.count() == 0


# ---------------------------------------------------------------------------
# MarketDataAdapter Tests
# ---------------------------------------------------------------------------


def test_adapter_to_bar_variations() -> None:
    adapter = MarketDataAdapter(default_publication_lag_seconds=2.0)

    # From ISO string
    rec_iso = {
        "symbol": "BTC/USD",
        "timestamp": "2026-01-15T12:00:00Z",
        "open": "50000.0",
        "high": "50100.0",
        "low": "49900.0",
        "close": "50050.0",
        "volume": "10.5",
    }
    bar = adapter.to_bar(rec_iso)
    assert bar.symbol == "BTC/USD"
    assert bar.timestamp == BASE_TIME
    assert bar.knowable_at == BASE_TIME + timedelta(seconds=2.0)

    # From unix epoch seconds
    rec_epoch = {
        "symbol": "ETH/USD",
        "timestamp": BASE_TIME.timestamp(),
        "open": 3000.0,
        "high": 3050.0,
        "low": 2980.0,
        "close": 3020.0,
        "volume": 5.0,
    }
    bar_eth = adapter.to_bar(rec_epoch)
    assert bar_eth.symbol == "ETH/USD"
    assert bar_eth.timestamp == BASE_TIME


def test_adapter_custom_knowable_at() -> None:
    adapter = MarketDataAdapter()
    rec = {
        "symbol": "SPY",
        "timestamp": BASE_TIME,
        "knowable_at": BASE_TIME + timedelta(seconds=15),
        "open": 450.0,
        "high": 452.0,
        "low": 449.0,
        "close": 451.0,
        "volume": 1000.0,
    }
    bar = adapter.to_bar(rec)
    assert bar.knowable_at == BASE_TIME + timedelta(seconds=15)


def test_adapter_invalid_data_raises() -> None:
    adapter = MarketDataAdapter()

    # Missing symbol
    with pytest.raises(ValueError, match="symbol is required"):
        adapter.to_bar({"timestamp": BASE_TIME, "open": 1, "high": 2, "low": 1, "close": 2})

    # High lower than low (contract validation)
    with pytest.raises(ValidationError):
        adapter.to_bar(
            {
                "symbol": "BTC/USD",
                "timestamp": BASE_TIME,
                "open": 100.0,
                "high": 80.0,
                "low": 90.0,
                "close": 95.0,
            }
        )


def test_adapter_from_csv(tmp_path: Path) -> None:
    csv_file = tmp_path / "bars.csv"
    csv_content = """timestamp,open,high,low,close,volume
2026-01-15T12:00:00Z,50000,50100,49900,50050,10.5
2026-01-15T12:01:00Z,50050,50200,50000,50150,8.2
"""
    csv_file.write_text(csv_content, encoding="utf-8")

    adapter = MarketDataAdapter(default_publication_lag_seconds=1.0)
    bars = adapter.from_csv(csv_file, symbol="BTC/USD")
    assert len(bars) == 2
    assert bars[0].symbol == "BTC/USD"
    assert bars[0].close == 50050.0
    assert bars[1].close == 50150.0
    assert bars[0].knowable_at == bars[0].timestamp + timedelta(seconds=1.0)
