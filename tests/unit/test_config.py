"""Unit tests for AMLIS configuration schema and loader (T0.4)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from libs.config import (
    AppConfig,
    AssetClass,
    AssetConfig,
    AssetDefinition,
    FeatureCategory,
    FeatureDefinition,
    FeatureDtype,
    FeatureSchema,
    HMMConfig,
    RegimeConfig,
    RegimeStateDefinition,
    ShockDetectorConfig,
    clear_config_cache,
    get_asset_config,
    get_config,
    get_feature_schema,
    get_regime_config,
    load_app_config,
    load_asset_config,
    load_feature_schema,
    load_regime_config,
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    clear_config_cache()
    yield
    clear_config_cache()


# ---------------------------------------------------------------------------
# Default configuration loading tests
# ---------------------------------------------------------------------------


def test_load_default_app_config() -> None:
    config = get_config()
    assert isinstance(config, AppConfig)
    assert isinstance(config.assets, AssetConfig)
    assert isinstance(config.features, FeatureSchema)
    assert isinstance(config.regimes, RegimeConfig)


def test_default_asset_config() -> None:
    asset_cfg = get_asset_config()
    assert asset_cfg.version == "0.1.0"
    symbols = asset_cfg.symbols
    assert "BTC/USD" in symbols
    assert "ETH/USD" in symbols
    assert "SPY" in symbols
    assert asset_cfg.enabled_symbols == symbols

    btc = asset_cfg.get_asset("BTC/USD")
    assert btc.symbol == "BTC/USD"
    assert btc.asset_class == AssetClass.CRYPTO
    assert btc.tick_size == 0.01
    assert btc.lot_size > 0.0
    assert btc.min_order_size > 0.0
    assert btc.price_precision == 2
    assert btc.quantity_precision == 4
    assert btc.trading_hours == "24/7"

    with pytest.raises(KeyError):
        asset_cfg.get_asset("NONEXISTENT")


def test_default_feature_schema() -> None:
    feat_schema = get_feature_schema()
    assert feat_schema.version == "0.1.0"
    assert feat_schema.staleness_max_seconds == 300
    names = feat_schema.feature_names
    assert "rsi_14" in names
    assert "macd_line" in names
    assert "sma_20" in names
    assert "volatility_20" in names
    assert "sentiment_score" in names
    assert "macro_surprise_cpi" in names
    assert "macro_shock_flag" in names

    rsi = feat_schema.get_feature("rsi_14")
    assert rsi.category == FeatureCategory.TECHNICAL
    assert rsi.dtype == FeatureDtype.FLOAT
    assert rsi.lookback_periods == 14
    assert rsi.min_value == 0.0
    assert rsi.max_value == 100.0

    sentiment = feat_schema.get_feature("sentiment_score")
    assert sentiment.category == FeatureCategory.SENTIMENT
    assert sentiment.required is False
    assert sentiment.min_value == -1.0
    assert sentiment.max_value == 1.0

    with pytest.raises(KeyError):
        feat_schema.get_feature("unknown_feature")


def test_default_regime_config() -> None:
    regime_cfg = get_regime_config()
    assert regime_cfg.version == "0.1.0"
    assert regime_cfg.state_names == ("low_vol", "transitional", "high_vol")

    s0 = regime_cfg.get_state_by_index(0)
    assert s0.name == "low_vol"
    assert s0.max_volatility == 0.15

    s1 = regime_cfg.get_state_by_name("transitional")
    assert s1.index == 1
    assert s1.min_volatility == 0.15
    assert s1.max_volatility == 0.35

    assert regime_cfg.hmm.n_states == 3
    assert "volatility_20" in regime_cfg.hmm.features
    assert regime_cfg.shock_detector.anomaly_threshold_std == 2.5
    assert regime_cfg.shock_detector.lookback_window == 60

    with pytest.raises(KeyError):
        regime_cfg.get_state_by_index(99)

    with pytest.raises(KeyError):
        regime_cfg.get_state_by_name("unknown_regime")


# ---------------------------------------------------------------------------
# Immutability and extra field rejection tests
# ---------------------------------------------------------------------------


def test_models_are_frozen() -> None:
    config = get_config()
    with pytest.raises(ValidationError):
        config.assets = None  # type: ignore[misc]

    btc = config.assets.get_asset("BTC/USD")
    with pytest.raises(ValidationError):
        btc.tick_size = 0.5  # type: ignore[misc]


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        AssetDefinition(
            symbol="TEST",
            asset_class="crypto",
            base_currency="TEST",
            quote_currency="USD",
            tick_size=0.01,
            lot_size=1.0,
            min_order_size=1.0,
            price_precision=2,
            quantity_precision=2,
            trading_hours="24/7",
            unexpected_field="disallowed",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# Validation error scenarios
# ---------------------------------------------------------------------------


def test_duplicate_asset_symbols_rejected() -> None:
    asset = AssetDefinition(
        symbol="BTC/USD",
        asset_class="crypto",
        base_currency="BTC",
        quote_currency="USD",
        tick_size=0.01,
        lot_size=0.1,
        min_order_size=0.1,
        price_precision=2,
        quantity_precision=2,
        trading_hours="24/7",
    )
    with pytest.raises(ValidationError, match="Duplicate asset symbols"):
        AssetConfig(version="1.0", assets=(asset, asset))


def test_duplicate_feature_names_rejected() -> None:
    feat = FeatureDefinition(
        name="test_feat",
        category=FeatureCategory.TECHNICAL,
        lookback_periods=5,
        dtype=FeatureDtype.FLOAT,
        description="test",
    )
    with pytest.raises(ValidationError, match="Duplicate feature names"):
        FeatureSchema(version="1.0", features=(feat, feat), staleness_max_seconds=60)


def test_inverted_feature_bounds_rejected() -> None:
    with pytest.raises(ValidationError, match="min_value .* cannot exceed max_value"):
        FeatureDefinition(
            name="bad_bounds",
            category=FeatureCategory.TECHNICAL,
            lookback_periods=5,
            dtype=FeatureDtype.FLOAT,
            description="bad",
            min_value=100.0,
            max_value=10.0,
        )


def test_regime_index_and_state_count_mismatch() -> None:
    s0 = RegimeStateDefinition(name="low", index=0, description="low")
    s1 = RegimeStateDefinition(name="high", index=2, description="high non contiguous")  # index 1 skipped
    hmm = HMMConfig(n_states=2, features=("vol",), min_history_bars=20)
    shock = ShockDetectorConfig(anomaly_threshold_std=2.0, lookback_window=10, min_reconstruction_error=0.1)

    with pytest.raises(ValidationError, match="contiguous"):
        RegimeConfig(version="1.0", states=(s0, s1), hmm=hmm, shock_detector=shock)

    # State count mismatch with hmm.n_states
    s1_fixed = RegimeStateDefinition(name="high", index=1, description="high")
    hmm_3 = HMMConfig(n_states=3, features=("vol",), min_history_bars=20)
    with pytest.raises(ValidationError, match="must equal HMM n_states"):
        RegimeConfig(version="1.0", states=(s0, s1_fixed), hmm=hmm_3, shock_detector=shock)


def test_inverted_regime_volatility_bounds_rejected() -> None:
    with pytest.raises(ValidationError, match="min_volatility cannot exceed max_volatility"):
        RegimeStateDefinition(
            name="invalid",
            index=0,
            description="invalid",
            min_volatility=0.5,
            max_volatility=0.2,
        )


# ---------------------------------------------------------------------------
# File loading error handling
# ---------------------------------------------------------------------------


def test_missing_config_file_raises_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_asset_config(tmp_path / "nonexistent.yaml")

    with pytest.raises(FileNotFoundError):
        load_feature_schema(tmp_path / "nonexistent.yaml")

    with pytest.raises(FileNotFoundError):
        load_regime_config(tmp_path / "nonexistent.yaml")

    with pytest.raises(FileNotFoundError):
        load_app_config(tmp_path)


def test_invalid_yaml_structure(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("- item1\n- item2\n", encoding="utf-8")  # list instead of mapping
    with pytest.raises(ValueError, match="must contain a top-level YAML mapping/dict"):
        load_asset_config(bad_file)
