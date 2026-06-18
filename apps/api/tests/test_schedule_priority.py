"""Tests for schedule priority mapping and batch helpers."""

from datetime import datetime, timezone

from exposureflow_api.content.schedule_priority import (
    articles_per_scheduled_run,
    resolve_exposure_priorities,
    schedule_already_ran_today,
)


def test_resolve_p1_maps_to_critical_and_high() -> None:
    assert resolve_exposure_priorities("P1") == ["critical", "high"]


def test_resolve_raw_priority_passthrough() -> None:
    assert resolve_exposure_priorities("high") == ["high"]


def test_articles_per_scheduled_run_distributes_weekly_quota() -> None:
    assert articles_per_scheduled_run(4, ["mon", "thu"]) == 2


def test_schedule_already_ran_today() -> None:
    now = datetime.now(timezone.utc)
    assert schedule_already_ran_today(now) is True
    assert schedule_already_ran_today(None) is False
