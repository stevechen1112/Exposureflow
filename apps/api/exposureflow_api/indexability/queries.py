"""Query published live article URLs from content generation runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.execution_content import ContentGenerationRun, ExecutionJob


@dataclass(frozen=True)
class PublishedUrlRecord:
    url: str
    published_at: datetime
    generation_run_id: UUID


def _parse_live_post_url(job: ExecutionJob) -> str | None:
    output = job.output_json or {}
    if output.get("contentflow_site_status") != "published":
        return None
    post_url = output.get("contentflow_post_url")
    if isinstance(post_url, str) and post_url.strip():
        return post_url.strip()
    return None


def _parse_live_published_at(job: ExecutionJob, run: ContentGenerationRun) -> datetime:
    output = job.output_json or {}
    raw = output.get("contentflow_live_published_at")
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        except ValueError:
            pass
    if job.updated_at:
        return job.updated_at
    return run.updated_at


async def list_live_published_urls(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    days_back: int = 30,
    limit: int = 50,
) -> list[PublishedUrlRecord]:
    cutoff = datetime.now(UTC) - timedelta(days=days_back)
    result = await db.execute(
        select(ContentGenerationRun, ExecutionJob)
        .join(ExecutionJob, ContentGenerationRun.execution_job_id == ExecutionJob.id)
        .where(
            ContentGenerationRun.workspace_id == workspace_id,
            ContentGenerationRun.site_id == site_id,
            ContentGenerationRun.status == "published",
            ContentGenerationRun.updated_at >= cutoff,
        )
        .order_by(ContentGenerationRun.updated_at.desc())
        .limit(limit)
    )
    records: list[PublishedUrlRecord] = []
    seen_urls: set[str] = set()
    for run, job in result.all():
        post_url = _parse_live_post_url(job)
        if not post_url or post_url in seen_urls:
            continue
        seen_urls.add(post_url)
        records.append(
            PublishedUrlRecord(
                url=post_url,
                published_at=_parse_live_published_at(job, run),
                generation_run_id=run.id,
            )
        )
    return records
