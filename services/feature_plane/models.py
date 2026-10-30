"""Input record models for feature plane (T0.9).

Adheres to service independence: defined within feature_plane or libs.contracts.
All records carry strict knowable_at timestamps to enforce point-in-time guarantees.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SentimentRecord(FrozenRecord):
    """Sentiment observation from news, transcripts, or social channels."""

    symbol: str = Field(min_length=1)
    timestamp: datetime
    knowable_at: datetime
    score: float = Field(ge=-1.0, le=1.0)
    source: str = "news"

    @model_validator(mode="after")
    def _pit_sane(self) -> SentimentRecord:
        if self.knowable_at < self.timestamp:
            raise ValueError("knowable_at cannot precede observation timestamp")
        return self


class MacroRecord(FrozenRecord):
    """Macro event observation for surprise and shock extraction."""

    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    scheduled_time: datetime
    knowable_at: datetime
    actual: float | None = None
    consensus: float | None = None
    surprise: float | None = None
    is_shock: bool = False
    shock_magnitude: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def _pit_sane(self) -> MacroRecord:
        if self.knowable_at < self.scheduled_time:
            raise ValueError("knowable_at cannot precede scheduled_time")
        return self


class FundamentalRecord(FrozenRecord):
    """Fundamental accounting or earnings observation."""

    symbol: str = Field(min_length=1)
    timestamp: datetime
    knowable_at: datetime
    metric_name: str = Field(min_length=1)
    value: float

    @model_validator(mode="after")
    def _pit_sane(self) -> FundamentalRecord:
        if self.knowable_at < self.timestamp:
            raise ValueError("knowable_at cannot precede filing/report timestamp")
        return self
