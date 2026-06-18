"""Content schedule service — CRUD + batch generation trigger."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.models.content_schedule import ContentSchedule
from exposureflow_api.models.decision import ActionCandidate, ActionDecision
from exposureflow_api.models.exposure import ExposureOpportunity
from exposureflow_api.execution.source_pack import build_source_pack
from exposureflow_api.execution.brief_builder import build_content_brief
from exposureflow_api.models.execution_content import ExecutionJob
from exposureflow_api.execution.action_router import is_content_generation_action
from exposureflow_api.content.schedule_priority import resolve_exposure_priorities
from exposureflow_api.content.service import create_generation_run

logger = logging.getLogger(__name__)


async def get_schedule(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> ContentSchedule | None:
    result = await db.execute(
        select(ContentSchedule).where(
            ContentSchedule.workspace_id == workspace_id,
            ContentSchedule.site_id == site_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_schedule(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    site_id: UUID,
    enabled: bool = False,
    articles_per_week: int = 2,
    priority_filter: str = "P1",
    schedule_days_json: list[str] | None = None,
    auto_approve_threshold: int | None = None,
) -> ContentSchedule:
    existing = await get_schedule(db, workspace_id, site_id)
    if existing:
        existing.enabled = enabled
        existing.articles_per_week = articles_per_week
        existing.priority_filter = priority_filter
        if schedule_days_json is not None:
            existing.schedule_days_json = schedule_days_json
        existing.auto_approve_threshold = auto_approve_threshold
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return existing

    row = ContentSchedule(
        workspace_id=workspace_id,
        site_id=site_id,
        enabled=enabled,
        articles_per_week=articles_per_week,
        priority_filter=priority_filter,
        schedule_days_json=schedule_days_json or ["mon", "thu"],
        auto_approve_threshold=auto_approve_threshold,
    )
    db.add(row)
    await db.flush()
    return row


async def update_schedule(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    **fields,
) -> ContentSchedule:
    existing = await get_schedule(db, workspace_id, site_id)
    if existing is None:
        raise not_found("Content schedule")
    for key, value in fields.items():
        if value is not None and hasattr(existing, key):
            setattr(existing, key, value)
    existing.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return existing


async def _pick_approved_candidates(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    count: int,
    priority_filter: str,
) -> list[ActionCandidate]:
    """Pick top N approved candidates matching priority filter, ordered by rank_score desc.

    Uses a single JOIN query to avoid N+1 on ExposureOpportunity.
    """
    priorities = resolve_exposure_priorities(priority_filter)
    result = await db.execute(
        select(ActionCandidate)
        .join(ExposureOpportunity, ActionCandidate.opportunity_id == ExposureOpportunity.id)
        .where(
            ActionCandidate.workspace_id == workspace_id,
            ActionCandidate.site_id == site_id,
            ActionCandidate.decision_status == "approved",
            ExposureOpportunity.priority.in_(priorities),
        )
        .order_by(ActionCandidate.rank_score.desc())
        .limit(count)
    )
    return list(result.scalars().all())


async def trigger_batch_generation(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    site_id: UUID,
    count: int = 2,
    priority_filter: str = "P1",
) -> tuple[int, int, list[UUID]]:
    """Pick top N approved candidates and trigger full generation pipeline for each.

    Returns (triggered, skipped, list_of_generation_run_ids).
    """
    candidates = await _pick_approved_candidates(
        db, workspace_id, site_id, count, priority_filter
    )

    triggered = 0
    skipped = 0
    run_ids: list[UUID] = []

    for candidate in candidates:
        if not is_content_generation_action(candidate.action_type):
            skipped += 1
            continue
        try:
            # Step 1: Build Source Pack
            sp_result = await build_source_pack(
                db,
                workspace_id=workspace_id,
                site_id=site_id,
                opportunity_id=candidate.opportunity_id,
                market="tw",
                language="zh-TW",
            )
            source_pack = sp_result.source_pack

            # Step 2: Build Content Brief
            brief = await build_content_brief(
                db,
                workspace_id=workspace_id,
                site_id=site_id,
                opportunity_id=candidate.opportunity_id,
                source_pack_id=source_pack.id,
            )

            # Step 3: Create Execution Job
            decision_result = await db.execute(
                select(ActionDecision.id)
                .where(
                    ActionDecision.workspace_id == workspace_id,
                    ActionDecision.candidate_id == candidate.id,
                    ActionDecision.decision == "approve",
                )
                .order_by(ActionDecision.created_at.desc())
                .limit(1)
            )
            decision_id = decision_result.scalar_one_or_none()
            job = ExecutionJob(
                workspace_id=workspace_id,
                site_id=site_id,
                opportunity_id=candidate.opportunity_id,
                decision_id=decision_id,
                job_type="content_generation",
                executor_type="content_engine",
                status="queued",
                input_json={
                    "candidate_id": str(candidate.id),
                    "opportunity_id": str(candidate.opportunity_id),
                    "action_type": candidate.action_type,
                    "source_pack_id": str(source_pack.id),
                    "brief_id": str(brief.id),
                },
            )
            db.add(job)
            await db.flush()

            # Step 4: Create Generation Run via service (runs LLM pipeline)
            run = await create_generation_run(
                db,
                workspace_id,
                site_id=site_id,
                execution_job_id=job.id,
                content_brief_id=brief.id,
                generation_mode=brief.brief_json.get("generation_mode", "grounded_llm"),
                review_level=brief.brief_json.get("review_policy", "editor_review"),
                auto_compile=False,
            )

            run_ids.append(run.id)
            triggered += 1
        except Exception as exc:
            logger.warning(
                "Batch generation failed for candidate=%s opportunity=%s: %s",
                candidate.id, candidate.opportunity_id, exc
            )
            skipped += 1
            continue

    # Update last_run_at on schedule
    schedule = await get_schedule(db, workspace_id, site_id)
    if schedule:
        schedule.last_run_at = datetime.now(timezone.utc)
        await db.flush()

    return triggered, skipped, run_ids
