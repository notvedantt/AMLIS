"""Feature calculation engine for AMLIS (T0.8).

Computes point-in-time features validated against the feature schema.
Ensures zero look-ahead bias by validating `knowable_at <= as_of` on every input bar.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from libs.common.pit import assert_point_in_time
from libs.config import get_feature_schema
from libs.contracts.models import OHLCVBar
from services.feature_plane.technical import (
    compute_macd,
    compute_rsi,
    compute_sma,
    compute_volatility,
)


class FeatureVector(BaseModel):
    """Point-in-time feature vector for an asset at a specific timestamp."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(min_length=1)
    timestamp: datetime
    knowable_at: datetime
    values: dict[str, float | None]

    def get(self, name: str) -> float | None:
        if name not in self.values:
            raise KeyError(f"Feature '{name}' not found in feature vector")
        return self.values[name]


class FeatureEngine:
    """Extracts and validates technical features from point-in-time market data."""

    def __init__(self) -> None:
        self.schema = get_feature_schema()

    def compute_technical_features(
        self,
        bars: Sequence[OHLCVBar],
        as_of: datetime,
    ) -> FeatureVector:
        """Compute all technical indicators defined in schema for the given bars as of `as_of`."""
        if not bars:
            raise ValueError("Cannot compute features from an empty sequence of bars")

        # Symbol consistency check
        symbol = bars[0].symbol
        for b in bars:
            if b.symbol != symbol:
                raise ValueError(f"Mixed symbols in bars: {symbol} vs {b.symbol}")
            # Strict point-in-time enforcement
            assert_point_in_time(b.knowable_at, as_of)

        latest_bar = bars[-1]
        close_prices = [b.close for b in bars]

        # Compute technical features
        rsi_14 = compute_rsi(close_prices, period=14)
        macd_line, macd_signal, macd_hist = compute_macd(close_prices, 12, 26, 9)
        sma_20 = compute_sma(close_prices, period=20)
        sma_50 = compute_sma(close_prices, period=50)
        vol_20 = compute_volatility(close_prices, period=20)

        # Map to schema-defined names
        raw_values: dict[str, float | None] = {
            "rsi_14": rsi_14,
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "volatility_20": vol_20,
        }

        # Validate against schema bounds
        for name, val in raw_values.items():
            if val is not None:
                feat_def = self.schema.get_feature(name)
                if feat_def.min_value is not None and val < feat_def.min_value:
                    raise ValueError(
                        f"Computed feature '{name}' value {val} is below schema min {feat_def.min_value}"
                    )
                if feat_def.max_value is not None and val > feat_def.max_value:
                    raise ValueError(
                        f"Computed feature '{name}' value {val} exceeds schema max {feat_def.max_value}"
                    )

        # The knowable_at of this feature vector is the maximum knowable_at of any input bar used
        max_knowable = max(b.knowable_at for b in bars)

        return FeatureVector(
            symbol=symbol,
            timestamp=latest_bar.timestamp,
            knowable_at=max_knowable,
            values=raw_values,
        )
