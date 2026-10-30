"""Validated configuration schemas for AMLIS (T0.4).

Single source of truth for assets, features, and regime definitions.
All config models are strictly typed, immutable (frozen), and forbid extra fields.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FrozenConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# ---------------------------------------------------------------------------
# Asset Configuration
# ---------------------------------------------------------------------------


class AssetClass(StrEnum):
    CRYPTO = "crypto"
    EQUITY = "equity"
    FX = "fx"
    COMMODITY = "commodity"


class AssetDefinition(FrozenConfig):
    symbol: str = Field(min_length=1)
    asset_class: AssetClass | str
    base_currency: str = Field(min_length=1)
    quote_currency: str = Field(min_length=1)
    tick_size: float = Field(gt=0.0)
    lot_size: float = Field(gt=0.0)
    min_order_size: float = Field(gt=0.0)
    price_precision: int = Field(ge=0)
    quantity_precision: int = Field(ge=0)
    trading_hours: str = Field(min_length=1)
    enabled: bool = True


class AssetConfig(FrozenConfig):
    version: str = Field(min_length=1)
    assets: tuple[AssetDefinition, ...]

    @field_validator("assets", mode="before")
    @classmethod
    def _coerce_assets(cls, v: Any) -> tuple[Any, ...]:
        if isinstance(v, list):
            return tuple(v)
        return v  # type: ignore[no-any-return]

    @model_validator(mode="after")
    def _unique_symbols(self) -> AssetConfig:
        symbols = [a.symbol for a in self.assets]
        if len(symbols) != len(set(symbols)):
            raise ValueError(f"Duplicate asset symbols found: {symbols}")
        return self

    def get_asset(self, symbol: str) -> AssetDefinition:
        for a in self.assets:
            if a.symbol == symbol:
                return a
        raise KeyError(f"Asset symbol '{symbol}' not found in configuration")

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(a.symbol for a in self.assets)

    @property
    def enabled_symbols(self) -> tuple[str, ...]:
        return tuple(a.symbol for a in self.assets if a.enabled)


# ---------------------------------------------------------------------------
# Feature Configuration
# ---------------------------------------------------------------------------


class FeatureCategory(StrEnum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MACRO = "macro"


class FeatureDtype(StrEnum):
    FLOAT = "float"
    BOOL = "bool"
    INT = "int"


class FeatureDefinition(FrozenConfig):
    name: str = Field(min_length=1)
    category: FeatureCategory
    lookback_periods: int = Field(ge=1)
    dtype: FeatureDtype
    description: str = Field(min_length=1)
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None

    @model_validator(mode="after")
    def _bounds_check(self) -> FeatureDefinition:
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) cannot exceed max_value ({self.max_value}) for {self.name}"
                )
        return self


class FeatureSchema(FrozenConfig):
    version: str = Field(min_length=1)
    features: tuple[FeatureDefinition, ...]
    staleness_max_seconds: int = Field(gt=0)
    default_fill_method: str = "forward_fill"

    @field_validator("features", mode="before")
    @classmethod
    def _coerce_features(cls, v: Any) -> tuple[Any, ...]:
        if isinstance(v, list):
            return tuple(v)
        return v  # type: ignore[no-any-return]

    @model_validator(mode="after")
    def _unique_features(self) -> FeatureSchema:
        names = [f.name for f in self.features]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate feature names found: {names}")
        return self

    def get_feature(self, name: str) -> FeatureDefinition:
        for f in self.features:
            if f.name == name:
                return f
        raise KeyError(f"Feature '{name}' not found in schema")

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.features)

    @property
    def required_feature_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.features if f.required)


# ---------------------------------------------------------------------------
# Regime Configuration
# ---------------------------------------------------------------------------


class RegimeStateDefinition(FrozenConfig):
    name: str = Field(min_length=1)
    index: int = Field(ge=0)
    description: str = Field(min_length=1)
    min_volatility: float | None = Field(default=None, ge=0.0)
    max_volatility: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def _vol_bounds(self) -> RegimeStateDefinition:
        if self.min_volatility is not None and self.max_volatility is not None:
            if self.min_volatility > self.max_volatility:
                raise ValueError("min_volatility cannot exceed max_volatility")
        return self


class HMMConfig(FrozenConfig):
    n_states: int = Field(ge=2)
    features: tuple[str, ...]
    covariance_type: str = "diag"
    min_history_bars: int = Field(ge=10)

    @field_validator("features", mode="before")
    @classmethod
    def _coerce_features(cls, v: Any) -> tuple[Any, ...]:
        if isinstance(v, list):
            return tuple(v)
        return v  # type: ignore[no-any-return]


class ShockDetectorConfig(FrozenConfig):
    anomaly_threshold_std: float = Field(gt=0.0)
    lookback_window: int = Field(ge=1)
    min_reconstruction_error: float = Field(gt=0.0)


class RegimeConfig(FrozenConfig):
    version: str = Field(min_length=1)
    states: tuple[RegimeStateDefinition, ...]
    hmm: HMMConfig
    shock_detector: ShockDetectorConfig

    @field_validator("states", mode="before")
    @classmethod
    def _coerce_states(cls, v: Any) -> tuple[Any, ...]:
        if isinstance(v, list):
            return tuple(v)
        return v  # type: ignore[no-any-return]

    @model_validator(mode="after")
    def _validate_states(self) -> RegimeConfig:
        names = [s.name for s in self.states]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate regime state names: {names}")
        indices = [s.index for s in self.states]
        if len(indices) != len(set(indices)):
            raise ValueError(f"Duplicate regime state indices: {indices}")
        expected_indices = list(range(len(self.states)))
        if sorted(indices) != expected_indices:
            raise ValueError(f"Regime indices must be contiguous starting from 0: {sorted(indices)}")
        if len(self.states) != self.hmm.n_states:
            raise ValueError(
                f"Number of regime states ({len(self.states)}) must equal HMM n_states ({self.hmm.n_states})"
            )
        return self

    @property
    def state_names(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.states)

    def get_state_by_index(self, index: int) -> RegimeStateDefinition:
        for s in self.states:
            if s.index == index:
                return s
        raise KeyError(f"Regime index '{index}' not found")

    def get_state_by_name(self, name: str) -> RegimeStateDefinition:
        for s in self.states:
            if s.name == name:
                return s
        raise KeyError(f"Regime name '{name}' not found")


# ---------------------------------------------------------------------------
# Top-level Application Configuration
# ---------------------------------------------------------------------------


class AppConfig(FrozenConfig):
    assets: AssetConfig
    features: FeatureSchema
    regimes: RegimeConfig
