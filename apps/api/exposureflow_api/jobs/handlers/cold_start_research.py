"""Cold-start keyword research — seeds pyramid nodes as needs_review."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun
from exposureflow_api.models.strategy import KeywordPyramidNode


async def run_cold_start_research(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE_ID",
            error_message="site_id is required",
        )
        return

    payload = run.input_json or {}
    seed_keywords = payload.get("seed_keywords") or []
    market = payload.get("market")
    language = payload.get("language")
    if not seed_keywords:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SEED_KEYWORDS",
            error_message="seed_keywords required for cold-start research",
        )
        return

    created = 0
    for kw in seed_keywords:
        db.add(
            KeywordPyramidNode(
                workspace_id=run.workspace_id,
                site_id=UUID(str(site_id)),
                keyword=str(kw).strip(),
                node_type="cluster",
                target_market=market,
                language=language,
                business_fit_status="needs_review",
                priority=4,
                created_by="system",
                evidence_json={"source": "cold_start_research", "job_run_id": str(run.id)},
            )
        )
        created += 1

    await finalize_job_run(
        run,
        success=True,
        output={"keywords_created": created, "status": "needs_review"},
    )
