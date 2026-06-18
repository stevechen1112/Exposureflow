from exposureflow_api.jobs.celery_app import celery_app
from exposureflow_api.jobs.service import execute_job_run_sync


@celery_app.task(name="exposureflow_api.jobs.tasks.execute_job_run", bind=True, max_retries=3)
def execute_job_run(self, job_run_id: str) -> None:
    try:
        execute_job_run_sync(job_run_id)
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="exposureflow_api.jobs.tasks.execute_scheduled_batch", bind=True, max_retries=2)
def execute_scheduled_batch(self) -> dict:
    """Celery Beat task: run scheduled batch content generation for all enabled schedules."""
    import asyncio
    from datetime import datetime, timezone

    from exposureflow_api.database import async_session_factory
    from exposureflow_api.content import schedule_service
    from exposureflow_api.content.schedule_priority import (
        articles_per_scheduled_run,
        schedule_already_ran_today,
    )

    WEEKDAY_MAP = {
        "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    }

    async def _run():
        async with async_session_factory() as db:
            from sqlalchemy import select
            from exposureflow_api.models.content_schedule import ContentSchedule

            result = await db.execute(
                select(ContentSchedule).where(ContentSchedule.enabled == True)  # noqa: E712
            )
            schedules = list(result.scalars().all())

            today = datetime.now(timezone.utc).weekday()
            triggered = 0
            skipped = 0
            skipped_not_today = 0
            skipped_already_today = 0
            errors: list[str] = []

            for schedule in schedules:
                days = schedule.schedule_days_json or ["mon", "thu"]
                allowed = {WEEKDAY_MAP.get(d, -1) for d in days}
                if today not in allowed:
                    skipped_not_today += 1
                    continue

                if schedule_already_ran_today(schedule.last_run_at):
                    skipped_already_today += 1
                    continue

                count = articles_per_scheduled_run(schedule.articles_per_week, days)
                try:
                    t, s, _ = await schedule_service.trigger_batch_generation(
                        db,
                        schedule.workspace_id,
                        site_id=schedule.site_id,
                        count=count,
                        priority_filter=schedule.priority_filter,
                    )
                    triggered += t
                    skipped += s
                except Exception as exc:
                    errors.append(f"site={schedule.site_id}: {exc}")

            await db.commit()
            return {
                "schedules_processed": len(schedules),
                "skipped_not_today": skipped_not_today,
                "skipped_already_today": skipped_already_today,
                "total_triggered": triggered,
                "total_skipped": skipped,
                "errors": errors,
            }

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=300) from exc


@celery_app.task(name="exposureflow_api.jobs.tasks.enqueue_sitemap_health_checks", bind=True, max_retries=2)
def enqueue_sitemap_health_checks(self) -> dict:
    """Celery Beat: enqueue GSC sitemap health audit for all sites with GSC credentials."""
    import asyncio
    from datetime import datetime, timezone

    from sqlalchemy import select

    from exposureflow_api.database import async_session_factory
    from exposureflow_api.jobs.service import enqueue_job
    from exposureflow_api.models import IntegrationCredential

    async def _run() -> dict:
        async with async_session_factory() as db:
            result = await db.execute(
                select(IntegrationCredential).where(
                    IntegrationCredential.provider == "gsc",
                    IntegrationCredential.status == "active",
                    IntegrationCredential.site_id.is_not(None),
                )
            )
            credentials = list(result.scalars().all())
            enqueued = 0
            errors: list[str] = []
            today = datetime.now(timezone.utc).date().isoformat()
            for cred in credentials:
                try:
                    await enqueue_job(
                        db,
                        workspace_id=cred.workspace_id,
                        job_type="indexability.sitemap_health",
                        site_id=cred.site_id,
                        idempotency_key=f"sitemap-health:{cred.workspace_id}:{cred.site_id}:{today}",
                    )
                    enqueued += 1
                except Exception as exc:
                    errors.append(f"site={cred.site_id}: {exc}")
            await db.commit()
            return {"sites_with_gsc": len(credentials), "enqueued": enqueued, "errors": errors}

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=300) from exc


@celery_app.task(name="exposureflow_api.jobs.tasks.enqueue_published_noindex_checks", bind=True, max_retries=2)
def enqueue_published_noindex_checks(self) -> dict:
    """Celery Beat: daily noindex/robots audit for sites with live published content."""
    import asyncio
    from datetime import datetime, timezone

    from sqlalchemy import select

    from exposureflow_api.database import async_session_factory
    from exposureflow_api.jobs.service import enqueue_job
    from exposureflow_api.models.execution_content import ContentGenerationRun

    async def _run() -> dict:
        async with async_session_factory() as db:
            result = await db.execute(
                select(ContentGenerationRun.workspace_id, ContentGenerationRun.site_id)
                .where(ContentGenerationRun.status == "published")
                .distinct()
            )
            site_pairs = list(result.all())
            enqueued = 0
            errors: list[str] = []
            today = datetime.now(timezone.utc).date().isoformat()
            for workspace_id, site_id in site_pairs:
                try:
                    await enqueue_job(
                        db,
                        workspace_id=workspace_id,
                        job_type="indexability.published_noindex",
                        site_id=site_id,
                        idempotency_key=f"published-noindex:{workspace_id}:{site_id}:{today}",
                    )
                    enqueued += 1
                except Exception as exc:
                    errors.append(f"site={site_id}: {exc}")
            await db.commit()
            return {
                "sites_with_published_content": len(site_pairs),
                "enqueued": enqueued,
                "errors": errors,
            }

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=300) from exc


@celery_app.task(name="exposureflow_api.jobs.tasks.enqueue_indexability_coverage_checks", bind=True, max_retries=2)
def enqueue_indexability_coverage_checks(self) -> dict:
    """Celery Beat: weekly OG-013 coverage check for sites with GSC credentials."""
    import asyncio
    from datetime import datetime, timezone

    from sqlalchemy import select

    from exposureflow_api.database import async_session_factory
    from exposureflow_api.jobs.service import enqueue_job
    from exposureflow_api.models import IntegrationCredential

    async def _run() -> dict:
        async with async_session_factory() as db:
            result = await db.execute(
                select(IntegrationCredential).where(
                    IntegrationCredential.provider == "gsc",
                    IntegrationCredential.status == "active",
                    IntegrationCredential.site_id.is_not(None),
                )
            )
            credentials = list(result.scalars().all())
            enqueued = 0
            errors: list[str] = []
            week_key = datetime.now(timezone.utc).date().isocalendar()
            idem_suffix = f"{week_key.year}-W{week_key.week:02d}"
            for cred in credentials:
                try:
                    await enqueue_job(
                        db,
                        workspace_id=cred.workspace_id,
                        job_type="indexability.coverage_check",
                        site_id=cred.site_id,
                        idempotency_key=(
                            f"coverage-check:{cred.workspace_id}:{cred.site_id}:{idem_suffix}"
                        ),
                    )
                    enqueued += 1
                except Exception as exc:
                    errors.append(f"site={cred.site_id}: {exc}")
            await db.commit()
            return {"sites_with_gsc": len(credentials), "enqueued": enqueued, "errors": errors}

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=300) from exc
