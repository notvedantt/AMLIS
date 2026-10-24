"""Point-in-time helpers. Principle 3: no component sees data dated after its decision."""

from __future__ import annotations

from datetime import datetime


class LookAheadError(RuntimeError):
    """Raised when data that was not yet knowable is used at decision time."""


def assert_point_in_time(knowable_at: datetime, decision_ts: datetime) -> None:
    if knowable_at > decision_ts:
        raise LookAheadError(
            f"data knowable at {knowable_at.isoformat()} used at decision time {decision_ts.isoformat()}"
        )
