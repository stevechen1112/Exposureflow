"""Ingest knowledge source metadata into facts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.knowledge.service import get_source
from exposureflow_api.models import JobRun, KnowledgeFact


async def run_knowledge_source_ingest(db: AsyncSession, run: JobRun) -> None:
    source_id = (run.input_json or {}).get("knowledge_source_id")
    facts = (run.input_json or {}).get("facts") or []
    if not source_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SOURCE_ID",
            error_message="knowledge_source_id is required",
        )
        return
    try:
        source = await get_source(db, run.workspace_id, UUID(str(source_id)))
        created = 0
        for item in facts:
            db.add(
                KnowledgeFact(
                    workspace_id=run.workspace_id,
                    site_id=source.site_id,
                    knowledge_source_id=source.id,
                    fact_type=str(item.get("fact_type", "product")),
                    subject=str(item.get("subject", "")),
                    fact_text=str(item.get("fact_text", "")),
                    market=item.get("market"),
                    language=item.get("language"),
                    status="draft",
                    metadata_json=item.get("metadata_json") or {},
                )
            )
            created += 1
        await finalize_job_run(run, success=True, output={"facts_created": created})
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="INGEST_FAILED",
            error_message=str(exc),
        )
