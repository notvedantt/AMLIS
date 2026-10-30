"""Data integrity gate for AMLIS (T0.6).

Rejects stale quotes, corrupt or insane price ranges, and cross-source discrepancies.
Provides detailed reasons for any rejected feed or record.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from libs.config import get_feature_schema
from libs.contracts.models import OHLCVBar


class IntegrityCheckResult(BaseModel):
    """Result of an integrity check on an individual market data bar."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: bool
    failure_reasons: tuple[str, ...] = ()
    symbol: str
    timestamp: datetime


class CrossSourceCheckResult(BaseModel):
    """Result of comparing quotes from two independent sources at the same timestamp."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: bool
    discrepancy_pct: float = Field(ge=0.0)
    failure_reason: str | None = None
    symbol: str
    timestamp: datetime


class DataIntegrityGate:
    """Deterministic gate that screens market data feeds before entry into store or pipeline."""

    def __init__(
        self,
        max_staleness_seconds: float | None = None,
        max_single_bar_change_pct: float = 0.50,  # 50% max jump per bar
        max_cross_source_discrepancy_pct: float = 0.02,  # 2% max discrepancy
    ) -> None:
        if max_staleness_seconds is None:
            # Fall back to single source of truth from feature schema
            self.max_staleness = timedelta(seconds=float(get_feature_schema().staleness_max_seconds))
        else:
            self.max_staleness = timedelta(seconds=max_staleness_seconds)

        self.max_single_bar_change_pct = max_single_bar_change_pct
        self.max_cross_source_discrepancy_pct = max_cross_source_discrepancy_pct

    def check_bar(
        self,
        bar: OHLCVBar,
        as_of: datetime,
        prev_bar: OHLCVBar | None = None,
    ) -> IntegrityCheckResult:
        """Evaluate a single OHLCVBar against staleness, range, and jump sanity checks."""
        reasons: list[str] = []

        # 1. Look-ahead / future knowledge sanity
        if bar.knowable_at > as_of:
            reasons.append(
                f"Bar knowable_at {bar.knowable_at.isoformat()} is in future of {as_of.isoformat()}"
            )

        # 2. Staleness check
        if as_of - bar.knowable_at > self.max_staleness:
            age_s = (as_of - bar.knowable_at).total_seconds()
            reasons.append(
                f"Bar is stale: age {age_s:.1f}s exceeds limit {self.max_staleness.total_seconds():.1f}s"
            )

        # 3. Non-positive price / volume sanity
        if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
            reasons.append(
                f"Non-positive price (open={bar.open}, high={bar.high}, low={bar.low}, close={bar.close})"
            )

        if bar.volume < 0:
            reasons.append(f"Negative volume detected ({bar.volume})")

        # 4. Inverted bounds sanity
        if bar.high < bar.low:
            reasons.append(f"Inverted high/low range: high {bar.high} < low {bar.low}")
        if bar.high < bar.open or bar.high < bar.close:
            reasons.append(f"High {bar.high} is less than open {bar.open} or close {bar.close}")
        if bar.low > bar.open or bar.low > bar.close:
            reasons.append(f"Low {bar.low} is greater than open {bar.open} or close {bar.close}")

        # 5. Extreme jump relative to previous bar
        if prev_bar is not None and prev_bar.close > 0:
            change_pct = abs(bar.close - prev_bar.close) / prev_bar.close
            if change_pct > self.max_single_bar_change_pct:
                reasons.append(
                    f"Extreme price jump: {change_pct * 100:.1f}% change exceeds limit "
                    f"{self.max_single_bar_change_pct * 100:.1f}%"
                )

        passed = len(reasons) == 0
        return IntegrityCheckResult(
            passed=passed,
            failure_reasons=tuple(reasons),
            symbol=bar.symbol,
            timestamp=bar.timestamp,
        )

    def check_cross_source(
        self,
        primary_bar: OHLCVBar,
        secondary_bar: OHLCVBar,
    ) -> CrossSourceCheckResult:
        """Compare two bars from different sources for the same symbol and timestamp."""
        if primary_bar.symbol != secondary_bar.symbol:
            raise ValueError(
                f"Cannot cross-check bars with different symbols: {primary_bar.symbol} vs "
                f"{secondary_bar.symbol}"
            )
        if primary_bar.timestamp != secondary_bar.timestamp:
            raise ValueError(
                "Cannot cross-check bars with different timestamps: "
                f"{primary_bar.timestamp} vs {secondary_bar.timestamp}"
            )

        avg_close = (primary_bar.close + secondary_bar.close) / 2.0
        if avg_close <= 0:
            return CrossSourceCheckResult(
                passed=False,
                discrepancy_pct=1.0,
                failure_reason="Non-positive average close price in cross-source check",
                symbol=primary_bar.symbol,
                timestamp=primary_bar.timestamp,
            )

        discrepancy = abs(primary_bar.close - secondary_bar.close) / avg_close
        passed = discrepancy <= self.max_cross_source_discrepancy_pct
        failure_reason = None
        if not passed:
            failure_reason = (
                f"Cross-source close price discrepancy {discrepancy * 100:.2f}% exceeds limit "
                f"{self.max_cross_source_discrepancy_pct * 100:.2f}% "
                f"({primary_bar.close} vs {secondary_bar.close})"
            )

        return CrossSourceCheckResult(
            passed=passed,
            discrepancy_pct=discrepancy,
            failure_reason=failure_reason,
            symbol=primary_bar.symbol,
            timestamp=primary_bar.timestamp,
        )

    def filter_bars(
        self,
        bars: Iterable[OHLCVBar],
        as_of: datetime,
    ) -> tuple[tuple[OHLCVBar, ...], tuple[IntegrityCheckResult, ...]]:
        """Filter a stream of bars, returning (accepted_bars, rejected_results)."""
        accepted: list[OHLCVBar] = []
        rejected: list[IntegrityCheckResult] = []
        prev_bar: OHLCVBar | None = None

        for bar in bars:
            res = self.check_bar(bar, as_of=as_of, prev_bar=prev_bar)
            if res.passed:
                accepted.append(bar)
                prev_bar = bar
            else:
                rejected.append(res)

        return tuple(accepted), tuple(rejected)
