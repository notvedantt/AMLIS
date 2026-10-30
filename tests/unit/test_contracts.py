from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from libs.contracts import Direction, ModelPrediction, RegimeState

NOW = datetime(2026, 1, 5, tzinfo=UTC)


def test_regime_probs_must_sum_to_one() -> None:
    RegimeState(timestamp=NOW, regime_probs=(0.5, 0.3, 0.2), shock_flag=False, shock_magnitude=0.0)
    with pytest.raises(ValidationError):
        RegimeState(timestamp=NOW, regime_probs=(0.5, 0.5, 0.5), shock_flag=False, shock_magnitude=0.0)


def test_prediction_is_frozen_and_rejects_unknown_fields() -> None:
    p = ModelPrediction(
        source="gbt", timestamp=NOW, direction=Direction.LONG, confidence=0.6, features_used=("rsi",)
    )
    with pytest.raises(ValidationError):
        p.confidence = 0.9  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ModelPrediction(
            source="x", timestamp=NOW, direction=Direction.FLAT, confidence=0.5, features_used=(), surprise=1
        )  # type: ignore[call-arg]
