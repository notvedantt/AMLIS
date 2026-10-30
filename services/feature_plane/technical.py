"""Technical indicator calculation library for AMLIS (T0.8).

Pure-math indicators matching the feature schema:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- SMA (Simple Moving Average)
- Volatility (Annualized rolling close-to-close log return volatility)
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def compute_sma(prices: Sequence[float], period: int) -> float | None:
    """Calculate Simple Moving Average for the given period."""
    if period <= 0 or len(prices) < period:
        return None
    window = prices[-period:]
    return sum(window) / period


def compute_ema_series(prices: Sequence[float], period: int) -> list[float]:
    """Calculate an Exponential Moving Average series for a given period.

    Uses standard multiplier: 2 / (period + 1).
    Initial value seeded from the SMA of the first `period` observations.
    """
    if period <= 0 or len(prices) < period:
        return []

    multiplier = 2.0 / (period + 1)
    # Seed with SMA
    ema = sum(prices[:period]) / period
    series = [ema]

    for p in prices[period:]:
        ema = (p - ema) * multiplier + ema
        series.append(ema)

    return series


def compute_ema(prices: Sequence[float], period: int) -> float | None:
    """Calculate the latest Exponential Moving Average."""
    series = compute_ema_series(prices, period)
    return series[-1] if series else None


def compute_rsi(prices: Sequence[float], period: int = 14) -> float | None:
    """Calculate Wilder's Relative Strength Index (RSI).

    Output is bounded in [0.0, 100.0].
    Requires at least `period + 1` prices.
    """
    if period <= 0 or len(prices) <= period:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    if len(deltas) < period:
        return None

    # Initial average gain/loss over first `period` deltas
    gains = [d if d > 0 else 0.0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0.0 for d in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Smoothed averages (Wilder's method)
    for d in deltas[period:]:
        gain = d if d > 0 else 0.0
        loss = -d if d < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return max(0.0, min(100.0, rsi))


def compute_macd(
    prices: Sequence[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[float | None, float | None, float | None]:
    """Calculate MACD Line, Signal Line, and MACD Histogram.

    - macd_line = EMA(fast) - EMA(slow)
    - macd_signal = EMA(macd_line, signal_period)
    - macd_hist = macd_line - macd_signal

    Returns (macd_line, macd_signal, macd_hist).
    """
    if len(prices) < slow_period + signal_period - 1:
        return None, None, None

    fast_ema_series = compute_ema_series(prices, fast_period)
    slow_ema_series = compute_ema_series(prices, slow_period)

    # Align series: slow_ema starts at index slow_period - 1 of prices
    # fast_ema started at index fast_period - 1
    offset = slow_period - fast_period
    macd_line_series = [
        fast - slow for fast, slow in zip(fast_ema_series[offset:], slow_ema_series, strict=False)
    ]

    if len(macd_line_series) < signal_period:
        return macd_line_series[-1] if macd_line_series else None, None, None

    signal_series = compute_ema_series(macd_line_series, signal_period)
    if not signal_series:
        return macd_line_series[-1], None, None

    latest_macd = macd_line_series[-1]
    latest_signal = signal_series[-1]
    latest_hist = latest_macd - latest_signal

    return latest_macd, latest_signal, latest_hist


def compute_volatility(
    prices: Sequence[float],
    period: int = 20,
    annualization_factor: float = math.sqrt(252.0),
) -> float | None:
    """Calculate rolling annualized close-to-close log return volatility.

    Requires at least `period + 1` prices.
    """
    if period <= 1 or len(prices) <= period:
        return None

    # Calculate log returns for the most recent `period` intervals
    window = prices[-(period + 1) :]
    log_returns = [math.log(window[i] / window[i - 1]) for i in range(1, len(window))]

    mean_ret = sum(log_returns) / len(log_returns)
    variance = sum((r - mean_ret) ** 2 for r in log_returns) / (len(log_returns) - 1)
    std_dev = math.sqrt(max(0.0, variance))

    return std_dev * annualization_factor
