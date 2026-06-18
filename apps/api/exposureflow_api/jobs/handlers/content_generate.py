"""Generate grounded content draft from brief."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content import service as content_service
from exposureflow_api.content.repository import pipeline_params_from_brief
from exposureflow_api.execution.agents.orchestrator import run_generation_pipeline
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
        gen_run = await content_service.get_generation_run(db, run.workspace_id, UUID(str(run_id)))
        brief = await content_service.get_brief(db, run.workspace_id, gen_run.content_brief_id)
        mode = gen_run.generation_mode or brief.brief_json.get("generation_mode") or "grounded_llm"

        if mode == "grounded_llm":
            params = pipeline_params_from_brief(brief)
            state = await run_generation_pipeline(
                db,
                run.workspace_id,
                UUID(str(run_id)),
                keyword=params["keyword"] or "",
                node_type=params["node_type"] or "cluster",
                intent=params["intent"],
            )
            compiled = await content_service.get_generation_run(db, run.workspace_id, UUID(str(run_id)))
            await finalize_job_run(
                run,
                success=True,
                output={
                    "generation_run_id": str(compiled.id),
                    "status": compiled.status,
                    "pipeline_status": state.pipeline_status,
                    "seo_score": state.best_seo_score,
                },
            )
        else:
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
