"""Publish approved draft to WordPress."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content import service as content_service
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun


async def run_wordpress_publish_draft(db: AsyncSession, run: JobRun) -> None:
    run_id = (run.input_json or {}).get("generation_run_id")
    actor_user_id = (run.input_json or {}).get("actor_user_id")
    if not run_id or not actor_user_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_INPUT",
            error_message="generation_run_id and actor_user_id are required",
        )
        return
    try:
        result = await content_service.publish_generation_run(
            db,
            run.workspace_id,
            UUID(str(run_id)),
            actor_user_id=UUID(str(actor_user_id)),
            provider="wordpress",
        )
        await finalize_job_run(run, success=True, output=result)
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="WORDPRESS_PUBLISH_FAILED",
            error_message=str(exc),
        )
