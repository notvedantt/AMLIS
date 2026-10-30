"""Unit tests for DataIntegrityGate (T0.6).

Tests every failure mode: staleness, range sanity, extreme jumps, and cross-source discrepancies.
"""

from datetime import UTC, datetime, timedelta

import pytest

from libs.contracts.models import OHLCVBar
from services.data_plane import CrossSourceCheckResult, DataIntegrityGate, IntegrityCheckResult

T0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def make_bar(
    symbol: str = "BTC/USD",
    ts: datetime = T0,
    knowable: datetime | None = None,
    open_price: float = 50000.0,
    high_price: float | None = None,
    low_price: float | None = None,
    close_price: float = 50050.0,
    volume: float = 1.0,
) -> OHLCVBar:
    actual_high = high_price if high_price is not None else max(open_price, close_price) + 50.0
    actual_low = low_price if low_price is not None else min(open_price, close_price) - 50.0
    return OHLCVBar(
        symbol=symbol,
        timestamp=ts,
        knowable_at=knowable or ts,
        open=open_price,
        high=actual_high,
        low=actual_low,
        close=close_price,
        volume=volume,
    )


# ---------------------------------------------------------------------------
# Individual failure mode tests
# ---------------------------------------------------------------------------


def test_valid_bar_passes() -> None:
    gate = DataIntegrityGate(max_staleness_seconds=300)
    bar = make_bar()
    res = gate.check_bar(bar, as_of=T0 + timedelta(seconds=60))
    assert res.passed is True
    assert res.failure_reasons == ()
    assert res.symbol == "BTC/USD"


def test_stale_bar_rejected() -> None:
    gate = DataIntegrityGate(max_staleness_seconds=300)
    # Bar is 500 seconds old
    bar = make_bar(ts=T0 - timedelta(seconds=500), knowable=T0 - timedelta(seconds=500))
    res = gate.check_bar(bar, as_of=T0)
    assert res.passed is False
    assert any("stale" in r.lower() for r in res.failure_reasons)


def test_future_bar_rejected() -> None:
    gate = DataIntegrityGate(max_staleness_seconds=300)
    # Bar knowable_at is in the future
    bar = make_bar(ts=T0, knowable=T0 + timedelta(seconds=30))
    res = gate.check_bar(bar, as_of=T0)
    assert res.passed is False
    assert any("future" in r.lower() for r in res.failure_reasons)


def test_extreme_price_jump_rejected() -> None:
    gate = DataIntegrityGate(max_single_bar_change_pct=0.20)  # 20% limit
    prev_bar = make_bar(close_price=50000.0)

    # 30% jump
    cur_bar = make_bar(
        open_price=65000.0,
        close_price=65000.0,
    )

    res = gate.check_bar(cur_bar, as_of=T0 + timedelta(minutes=1), prev_bar=prev_bar)
    assert res.passed is False
    assert any("extreme price jump" in r.lower() for r in res.failure_reasons)


# ---------------------------------------------------------------------------
# Cross-Source Check Tests
# ---------------------------------------------------------------------------


def test_cross_source_agreement_passes_when_close() -> None:
    gate = DataIntegrityGate(max_cross_source_discrepancy_pct=0.01)  # 1% tolerance
    feed_a = make_bar(close_price=50000.0)
    feed_b = make_bar(close_price=50100.0)  # 0.2% difference

    res = gate.check_cross_source(feed_a, feed_b)
    assert isinstance(res, CrossSourceCheckResult)
    assert res.passed is True
    assert res.discrepancy_pct < 0.01
    assert res.failure_reason is None


def test_cross_source_disagreement_rejected() -> None:
    gate = DataIntegrityGate(max_cross_source_discrepancy_pct=0.01)  # 1% tolerance
    feed_a = make_bar(close_price=50000.0)
    feed_b = make_bar(close_price=52000.0)  # ~3.9% difference

    res = gate.check_cross_source(feed_a, feed_b)
    assert res.passed is False
    assert res.failure_reason is not None
    assert "exceeds limit" in res.failure_reason


def test_cross_source_mismatched_inputs_raise() -> None:
    gate = DataIntegrityGate()
    bar1 = make_bar(symbol="BTC/USD")
    bar2 = make_bar(symbol="ETH/USD")

    with pytest.raises(ValueError, match="different symbols"):
        gate.check_cross_source(bar1, bar2)

    bar3 = make_bar(ts=T0 + timedelta(minutes=1))
    with pytest.raises(ValueError, match="different timestamps"):
        gate.check_cross_source(bar1, bar3)


# ---------------------------------------------------------------------------
# Stream Filtering Tests
# ---------------------------------------------------------------------------


def test_filter_bars_stream() -> None:
    gate = DataIntegrityGate(max_staleness_seconds=300, max_single_bar_change_pct=0.5)

    valid_bar1 = make_bar(ts=T0 - timedelta(seconds=120), close_price=50000.0)
    valid_bar2 = make_bar(ts=T0 - timedelta(seconds=60), close_price=50200.0)
    stale_bar = make_bar(ts=T0 - timedelta(seconds=600), close_price=50000.0)
    future_bar = make_bar(ts=T0, knowable=T0 + timedelta(seconds=10), close_price=50300.0)

    stream = [stale_bar, valid_bar1, valid_bar2, future_bar]
    accepted, rejected = gate.filter_bars(stream, as_of=T0)

    assert len(accepted) == 2
    assert accepted[0] == valid_bar1
    assert accepted[1] == valid_bar2

    assert len(rejected) == 2
    assert all(isinstance(r, IntegrityCheckResult) for r in rejected)
    assert any("stale" in r.failure_reasons[0].lower() for r in rejected)
    assert any("future" in r.failure_reasons[0].lower() for r in rejected)
