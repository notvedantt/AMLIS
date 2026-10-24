"""Seed of the permanent leakage-regression suite (T0.11). Every service adds its own tests here."""

from datetime import UTC, datetime, timedelta

import pytest

from libs.common.pit import LookAheadError, assert_point_in_time

T = datetime(2026, 1, 5, 12, tzinfo=UTC)


def test_past_data_is_allowed() -> None:
    assert_point_in_time(T - timedelta(minutes=1), T)


def test_future_data_fails_the_build() -> None:
    with pytest.raises(LookAheadError):
        assert_point_in_time(T + timedelta(seconds=1), T)
