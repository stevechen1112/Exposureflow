"""Generate grounded content draft from brief."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content import service as content_service
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun


async def run_content_generate_grounded_draft(db: AsyncSession, run: JobRun) -> None:
    input_json = run.input_json or {}
    run_id = input_json.get("generation_run_id")
    if not run_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_GENERATION_RUN_ID",
            error_message="generation_run_id is required",
        )
        return
    try:
        compiled = await content_service.compile_generation_run(
            db, run.workspace_id, UUID(str(run_id))
        )
        await finalize_job_run(
            run,
            success=True,
            output={"generation_run_id": str(compiled.id), "status": compiled.status},
        )
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="COMPILE_FAILED",
            error_message=str(exc),
        )
