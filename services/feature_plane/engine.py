"""Feature calculation engine for AMLIS (T0.8 / T0.9).

Computes point-in-time features across technical, fundamental, sentiment,
and macro-event planes validated against the feature schema.
Ensures zero look-ahead bias by validating `knowable_at <= as_of` on every input record.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from libs.common.pit import assert_point_in_time
from libs.config import get_feature_schema
from libs.contracts.models import OHLCVBar
from services.feature_plane.models import FundamentalRecord, MacroRecord, SentimentRecord
from services.feature_plane.other_features import (
    extract_fundamentals,
    extract_macro_features,
    extract_sentiment,
)
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
    values: dict[str, Any]

    def get(self, name: str) -> Any:
        if name not in self.values:
            raise KeyError(f"Feature '{name}' not found in feature vector")
        return self.values[name]


class FeatureEngine:
    """Extracts and validates technical, sentiment, macro, and fundamental features."""

    def __init__(self) -> None:
        self.schema = get_feature_schema()

    def compute_technical_features(
        self,
        bars: Sequence[OHLCVBar],
        as_of: datetime,
    ) -> FeatureVector:
        """Compute only technical indicators defined in schema."""
        return self.compute_features(bars=bars, as_of=as_of)

    def compute_features(
        self,
        bars: Sequence[OHLCVBar],
        as_of: datetime,
        sentiment_records: Sequence[SentimentRecord] = (),
        macro_records: Sequence[MacroRecord] = (),
        fundamental_records: Sequence[FundamentalRecord] = (),
    ) -> FeatureVector:
        """Compute complete multi-plane feature vector strictly bounded as of `as_of`."""
        if not bars:
            raise ValueError("Cannot compute features from an empty sequence of bars")

        symbol = bars[0].symbol
        for b in bars:
            if b.symbol != symbol:
                raise ValueError(f"Mixed symbols in bars: {symbol} vs {b.symbol}")
            assert_point_in_time(b.knowable_at, as_of)

        latest_bar = bars[-1]
        close_prices = [b.close for b in bars]

        # 1. Technical features (T0.8)
        rsi_14 = compute_rsi(close_prices, period=14)
        macd_line, macd_signal, macd_hist = compute_macd(close_prices, 12, 26, 9)
        sma_20 = compute_sma(close_prices, period=20)
        sma_50 = compute_sma(close_prices, period=50)
        vol_20 = compute_volatility(close_prices, period=20)

        # 2. Sentiment features (T0.9)
        sentiment_score = extract_sentiment(sentiment_records, as_of=as_of)

        # 3. Macro features (T0.9)
        cpi_surprise, shock_flag, shock_mag = extract_macro_features(macro_records, as_of=as_of)

        # 4. Fundamental features (T0.9)
        fund_metrics = extract_fundamentals(fundamental_records, as_of=as_of)

        # Map to schema-defined names
        raw_values: dict[str, Any] = {
            "rsi_14": rsi_14,
            "macd_line": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "volatility_20": vol_20,
            "sentiment_score": sentiment_score,
            "macro_surprise_cpi": cpi_surprise,
            "macro_shock_flag": shock_flag,
            "macro_shock_magnitude": shock_mag,
            **fund_metrics,
        }

        # Validate against schema bounds where defined
        for name in self.schema.feature_names:
            val = raw_values.get(name)
            if val is not None and isinstance(val, int | float):
                feat_def = self.schema.get_feature(name)
                if feat_def.min_value is not None and val < feat_def.min_value:
                    raise ValueError(f"Feature '{name}' value {val} is below schema min {feat_def.min_value}")
                if feat_def.max_value is not None and val > feat_def.max_value:
                    raise ValueError(f"Feature '{name}' value {val} exceeds schema max {feat_def.max_value}")

        # Maximum knowable_at across all inputs consumed
        knowables = [b.knowable_at for b in bars]
        if sentiment_records:
            knowables.extend(s.knowable_at for s in sentiment_records)
        if macro_records:
            knowables.extend(m.knowable_at for m in macro_records)
        if fundamental_records:
            knowables.extend(f.knowable_at for f in fundamental_records)

        return FeatureVector(
            symbol=symbol,
            timestamp=latest_bar.timestamp,
            knowable_at=max(knowables),
            values=raw_values,
        )
