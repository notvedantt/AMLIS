"""Configuration loading and validation for AMLIS (T0.4).

Single source of truth for assets, features, and regime definitions.
Provides cached loaders with explicit cache invalidation for testing.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from libs.config.models import AppConfig, AssetConfig, FeatureSchema, RegimeConfig

_DEFAULTS_DIR = Path(__file__).parent / "defaults"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file {path.name} must contain a top-level YAML mapping/dict")
    return data


def load_asset_config(path: Path | str | None = None) -> AssetConfig:
    """Load and validate the asset configuration from YAML."""
    file_path = Path(path) if path else _DEFAULTS_DIR / "assets.yaml"
    data = _read_yaml(file_path)
    return AssetConfig.model_validate(data)


def load_feature_schema(path: Path | str | None = None) -> FeatureSchema:
    """Load and validate the feature schema from YAML."""
    file_path = Path(path) if path else _DEFAULTS_DIR / "features.yaml"
    data = _read_yaml(file_path)
    return FeatureSchema.model_validate(data)


def load_regime_config(path: Path | str | None = None) -> RegimeConfig:
    """Load and validate the regime configuration from YAML."""
    file_path = Path(path) if path else _DEFAULTS_DIR / "regimes.yaml"
    data = _read_yaml(file_path)
    return RegimeConfig.model_validate(data)


def load_app_config(config_dir: Path | str | None = None) -> AppConfig:
    """Load all AMLIS configurations from a directory (defaults to libs/config/defaults)."""
    base_dir = Path(config_dir) if config_dir else _DEFAULTS_DIR
    assets = load_asset_config(base_dir / "assets.yaml")
    features = load_feature_schema(base_dir / "features.yaml")
    regimes = load_regime_config(base_dir / "regimes.yaml")
    return AppConfig(assets=assets, features=features, regimes=regimes)


@functools.lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return the cached default application configuration."""
    return load_app_config()


@functools.lru_cache(maxsize=1)
def get_asset_config() -> AssetConfig:
    """Return the cached default asset configuration."""
    return load_asset_config()


@functools.lru_cache(maxsize=1)
def get_feature_schema() -> FeatureSchema:
    """Return the cached default feature schema."""
    return load_feature_schema()


@functools.lru_cache(maxsize=1)
def get_regime_config() -> RegimeConfig:
    """Return the cached default regime configuration."""
    return load_regime_config()


def clear_config_cache() -> None:
    """Clear all cached configuration instances (useful in tests)."""
    get_config.cache_clear()
    get_asset_config.cache_clear()
    get_feature_schema.cache_clear()
    get_regime_config.cache_clear()
