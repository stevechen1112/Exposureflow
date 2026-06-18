"""Exposure opportunity priority aliases for content schedule filters."""

from __future__ import annotations

from datetime import datetime, timezone

# UI uses P0–P3 (keyword pyramid tier labels); DB stores critical/high/medium/low.
PRIORITY_FILTER_ALIASES: dict[str, list[str]] = {
    "P0": ["critical"],
    "P1": ["critical", "high"],
    "P2": ["medium"],
    "P3": ["low"],
}


def resolve_exposure_priorities(priority_filter: str) -> list[str]:
    key = (priority_filter or "").strip()
    if key in PRIORITY_FILTER_ALIASES:
        return PRIORITY_FILTER_ALIASES[key]
    return [key]


def articles_per_scheduled_run(articles_per_week: int, schedule_days: list[str]) -> int:
    """Distribute weekly article quota evenly across configured schedule days."""
    days = max(len(schedule_days or ["mon", "thu"]), 1)
    return max(1, (articles_per_week + days - 1) // days)


def schedule_already_ran_today(last_run_at: datetime | None) -> bool:
    if last_run_at is None:
        return False
    today = datetime.now(timezone.utc).date()
    return last_run_at.astimezone(timezone.utc).date() == today
