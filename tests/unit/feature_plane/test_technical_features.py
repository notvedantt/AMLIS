"""Unit tests for Technical Indicator Features (T0.8)."""

from datetime import UTC, datetime, timedelta

import pytest

from libs.contracts.models import OHLCVBar
from services.feature_plane import (
    FeatureEngine,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_sma,
    compute_volatility,
)

T0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def make_bars(count: int, base_price: float = 100.0, trend: float = 1.0) -> list[OHLCVBar]:
    bars = []
    for i in range(count):
        ts = T0 + timedelta(minutes=i)
        close = base_price + i * trend
        bars.append(
            OHLCVBar(
                symbol="BTC/USD",
                timestamp=ts,
                knowable_at=ts + timedelta(seconds=1),
                open=close - 0.5,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=10.0,
            )
        )
    return bars


# ---------------------------------------------------------------------------
# Indicator Math Unit Tests
# ---------------------------------------------------------------------------


def test_compute_sma() -> None:
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert compute_sma(prices, 3) == pytest.approx(40.0)
    assert compute_sma(prices, 5) == pytest.approx(30.0)
    assert compute_sma(prices, 10) is None  # Insufficient history
    assert compute_sma(prices, 0) is None


def test_compute_ema() -> None:
    prices = [10.0, 11.0, 12.0, 13.0, 14.0]
    ema = compute_ema(prices, 3)
    assert ema is not None
    assert ema > 12.0
    assert compute_ema(prices, 10) is None


def test_compute_rsi() -> None:
    # Upward trend: prices strictly increasing
    up_prices = [100.0 + i * 2.0 for i in range(30)]
    rsi_up = compute_rsi(up_prices, period=14)
    assert rsi_up is not None
    assert rsi_up > 80.0
    assert 0.0 <= rsi_up <= 100.0

    # Downward trend: prices strictly decreasing
    down_prices = [200.0 - i * 2.0 for i in range(30)]
    rsi_down = compute_rsi(down_prices, period=14)
    assert rsi_down is not None
    assert rsi_down < 20.0
    assert 0.0 <= rsi_down <= 100.0

    # Insufficient prices
    assert compute_rsi([100.0, 101.0], period=14) is None


def test_compute_macd() -> None:
    prices = [100.0 + (i % 5) * 1.5 + i * 0.2 for i in range(60)]
    line, signal, hist = compute_macd(prices, 12, 26, 9)
    assert line is not None
    assert signal is not None
    assert hist is not None
    assert hist == pytest.approx(line - signal)

    # Short history
    short_line, short_signal, short_hist = compute_macd([100.0, 101.0], 12, 26, 9)
    assert short_line is None
    assert short_signal is None
    assert short_hist is None


def test_compute_volatility() -> None:
    # Constant prices -> zero volatility
    flat_prices = [100.0] * 30
    vol_flat = compute_volatility(flat_prices, period=20)
    assert vol_flat == pytest.approx(0.0)

    # Varying prices -> positive volatility
    varying_prices = [100.0 + (i % 3) * 2.0 for i in range(30)]
    vol = compute_volatility(varying_prices, period=20)
    assert vol is not None
    assert vol > 0.0

    assert compute_volatility([100.0], period=20) is None


# ---------------------------------------------------------------------------
# FeatureEngine Tests
# ---------------------------------------------------------------------------


def test_feature_engine_extracts_schema_features() -> None:
    engine = FeatureEngine()
    bars = make_bars(count=60, base_price=50000.0, trend=10.0)
    as_of = bars[-1].knowable_at + timedelta(seconds=5)

    feat_vec = engine.compute_technical_features(bars, as_of=as_of)
    assert feat_vec.symbol == "BTC/USD"
    assert feat_vec.timestamp == bars[-1].timestamp
    assert feat_vec.knowable_at == bars[-1].knowable_at

    # Check all schema technical features exist
    expected_feats = [
        "rsi_14",
        "macd_line",
        "macd_signal",
        "macd_hist",
        "sma_20",
        "sma_50",
        "volatility_20",
    ]
    for feat in expected_feats:
        assert feat in feat_vec.values
        val = feat_vec.get(feat)
        assert val is not None

    # Check bounds
    assert 0.0 <= feat_vec.get("rsi_14") <= 100.0
    assert feat_vec.get("volatility_20") >= 0.0


def test_feature_engine_validations() -> None:
    engine = FeatureEngine()
    # Empty bars
    with pytest.raises(ValueError, match="empty sequence"):
        engine.compute_technical_features([], as_of=T0)

    # Mixed symbols
    b1 = make_bars(1)[0]
    b2 = OHLCVBar(
        symbol="ETH/USD",
        timestamp=b1.timestamp + timedelta(minutes=1),
        knowable_at=b1.timestamp + timedelta(minutes=1),
        open=3000.0,
        high=3010.0,
        low=2990.0,
        close=3005.0,
        volume=1.0,
    )
    with pytest.raises(ValueError, match="Mixed symbols"):
        engine.compute_technical_features([b1, b2], as_of=b2.knowable_at)
