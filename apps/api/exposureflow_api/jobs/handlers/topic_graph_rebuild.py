"""Topic graph rebuild job handler."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import finalize_job_run, get_site
from exposureflow_api.models import JobRun
from exposureflow_api.topics import service


async def run_topic_graph_rebuild(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for topic_graph.rebuild",
        )
        return

    site = await get_site(db, run.workspace_id, site_id)
    if site is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="SITE_NOT_FOUND",
            error_message="Site not found",
        )
        return

    try:
        graph = await service.rebuild_topic_graph(db, run.workspace_id, site_id)
        cannibal = await service.run_cannibalization_detection(db, run.workspace_id, site_id)
        links = await service.generate_internal_links_for_site(db, run.workspace_id, site_id)
        await finalize_job_run(
            run,
            success=True,
            output={
                **graph,
                "cannibalization_cases": cannibal,
                "internal_link_suggestions": links,
            },
        )
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="TOPIC_GRAPH_REBUILD_FAILED",
            error_message=str(exc),
        )
