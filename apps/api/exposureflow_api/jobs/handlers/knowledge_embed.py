"""Embed approved knowledge facts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.execution.capacity import check_capacity, record_usage_event
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.knowledge.retrieval import embed_fact
from exposureflow_api.models import JobRun, KnowledgeFact


async def run_knowledge_fact_embed(db: AsyncSession, run: JobRun) -> None:
    fact_id = (run.input_json or {}).get("fact_id")
    site_id = run.site_id
    try:
        await check_capacity(db, run.workspace_id, "knowledge_embedding", quantity=1)
        if fact_id:
            fact = await db.get(KnowledgeFact, UUID(str(fact_id)))
            if fact is None or fact.workspace_id != run.workspace_id:
                raise ValueError("Fact not found")
            await embed_fact(db, fact)
            count = 1
        else:
            stmt = select(KnowledgeFact).where(
                KnowledgeFact.workspace_id == run.workspace_id,
                KnowledgeFact.status == "approved",
            )
            if site_id:
                stmt = stmt.where(KnowledgeFact.site_id == site_id)
            facts = list((await db.execute(stmt)).scalars().all())
            count = 0
            for fact in facts:
                if (fact.metadata_json or {}).get("embedding"):
                    continue
                await embed_fact(db, fact)
                count += 1
        await record_usage_event(
            db,
            workspace_id=run.workspace_id,
            site_id=UUID(str(site_id)) if site_id else None,
            metric="knowledge_embedding",
            quantity=max(count, 1),
            idempotency_key=f"knowledge-embed:{run.id}",
        )
        await finalize_job_run(run, success=True, output={"facts_embedded": count})
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="EMBED_FAILED",
            error_message=str(exc),
        )
