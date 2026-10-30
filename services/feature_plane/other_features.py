"""Feature extractors for sentiment, fundamental, and macroeconomic events (T0.9).

Calculates surprise-vs-consensus and shock flags per timestamp under strict PIT rules.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from libs.common.pit import assert_point_in_time
from services.feature_plane.models import FundamentalRecord, MacroRecord, SentimentRecord


def extract_sentiment(
    records: Sequence[SentimentRecord],
    as_of: datetime,
) -> float | None:
    """Extract latest knowable sentiment score for an asset as of `as_of`."""
    valid_records: list[SentimentRecord] = []
    for r in records:
        assert_point_in_time(r.knowable_at, as_of)
        valid_records.append(r)

    if not valid_records:
        return None

    # Return the most recent knowable sentiment observation
    latest = max(valid_records, key=lambda r: r.knowable_at)
    return latest.score


def extract_macro_features(
    records: Sequence[MacroRecord],
    as_of: datetime,
    shock_window: timedelta = timedelta(days=1),
) -> tuple[float | None, bool, float]:
    """Extract CPI surprise, active shock flag, and shock magnitude as of `as_of`.

    Returns
    -------
    tuple[cpi_surprise, macro_shock_flag, shock_magnitude]
    """
    valid_records: list[MacroRecord] = []
    for r in records:
        assert_point_in_time(r.knowable_at, as_of)
        valid_records.append(r)

    if not valid_records:
        return None, False, 0.0

    # 1. Latest CPI surprise
    cpi_records = [r for r in valid_records if r.event_type.lower() == "cpi" and r.surprise is not None]
    latest_cpi_surprise = max(cpi_records, key=lambda r: r.knowable_at).surprise if cpi_records else None

    # 2. Macro shock flag: active if any event in the last `shock_window` is flagged as shock
    window_start = as_of - shock_window
    recent_shocks = [
        r for r in valid_records if r.knowable_at >= window_start and (r.is_shock or r.shock_magnitude > 0.0)
    ]

    shock_flag = len(recent_shocks) > 0
    max_magnitude = max((r.shock_magnitude for r in recent_shocks), default=0.0)

    return latest_cpi_surprise, shock_flag, max_magnitude


def extract_fundamentals(
    records: Sequence[FundamentalRecord],
    as_of: datetime,
) -> dict[str, float]:
    """Extract latest fundamental metrics as of `as_of`."""
    latest_by_metric: dict[str, tuple[datetime, float]] = {}

    for r in records:
        assert_point_in_time(r.knowable_at, as_of)
        if r.metric_name not in latest_by_metric or r.knowable_at > latest_by_metric[r.metric_name][0]:
            latest_by_metric[r.metric_name] = (r.knowable_at, r.value)

    return {k: v[1] for k, v in latest_by_metric.items()}
