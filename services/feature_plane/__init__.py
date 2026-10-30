"""Technical, fundamental, sentiment and macro-event features under one schema."""

from services.feature_plane.engine import FeatureEngine, FeatureVector
from services.feature_plane.models import FundamentalRecord, MacroRecord, SentimentRecord
from services.feature_plane.other_features import (
    extract_fundamentals,
    extract_macro_features,
    extract_sentiment,
)
from services.feature_plane.technical import (
    compute_ema,
    compute_ema_series,
    compute_macd,
    compute_rsi,
    compute_sma,
    compute_volatility,
)

__all__ = [
    "FeatureEngine",
    "FeatureVector",
    "FundamentalRecord",
    "MacroRecord",
    "SentimentRecord",
    "compute_ema",
    "compute_ema_series",
    "compute_macd",
    "compute_rsi",
    "compute_sma",
    "compute_volatility",
    "extract_fundamentals",
    "extract_macro_features",
    "extract_sentiment",
]
