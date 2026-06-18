"""Scheduled batch content generation handler."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content import schedule_service
from exposureflow_api.content.schedule_priority import (
    articles_per_scheduled_run,
    schedule_already_ran_today,
)
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun
from exposureflow_api.models.content_schedule import ContentSchedule

WEEKDAY_MAP: dict[str, int] = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}


def _is_scheduled_today(schedule: ContentSchedule) -> bool:
    """Check if today's weekday is in the schedule's configured days."""
    today = datetime.now(timezone.utc).weekday()  # 0=Mon..6=Sun
    days = schedule.schedule_days_json or ["mon", "thu"]
    allowed = {WEEKDAY_MAP.get(d, -1) for d in days}
    return today in allowed


async def run_content_scheduled_batch(db: AsyncSession, run: JobRun) -> None:
    """Run scheduled batch generation for all enabled schedules.

    Iterates all enabled ContentSchedule rows and triggers batch generation
    for each site that has approved candidates ready AND today is a scheduled day.
    """
    result = await db.execute(
        select(ContentSchedule).where(ContentSchedule.enabled == True)  # noqa: E712
    )
    schedules = list(result.scalars().all())

    total_triggered = 0
    total_skipped = 0
    skipped_not_today = 0
    skipped_already_today = 0
    errors: list[str] = []

    for schedule in schedules:
        if not _is_scheduled_today(schedule):
            skipped_not_today += 1
            continue

        if schedule_already_ran_today(schedule.last_run_at):
            skipped_already_today += 1
            continue

        days = schedule.schedule_days_json or ["mon", "thu"]
        count = articles_per_scheduled_run(schedule.articles_per_week, days)

        try:
            triggered, skipped, _run_ids = await schedule_service.trigger_batch_generation(
                db,
                schedule.workspace_id,
                site_id=schedule.site_id,
                count=count,
                priority_filter=schedule.priority_filter,
            )
            total_triggered += triggered
            total_skipped += skipped
        except Exception as exc:
            errors.append(f"site={schedule.site_id}: {exc}")

    await finalize_job_run(
        run,
        success=len(errors) == 0,
        output={
            "schedules_processed": len(schedules),
            "skipped_not_today": skipped_not_today,
            "skipped_already_today": skipped_already_today,
            "total_triggered": total_triggered,
            "total_skipped": total_skipped,
            "errors": errors,
        },
        error_code="PARTIAL_FAILURE" if errors else None,
        error_message="; ".join(errors) if errors else None,
    )
