"""Workspace-scoped knowledge fact retrieval."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.knowledge.embeddings import cosine_similarity, embed_text
from exposureflow_api.knowledge.service import is_fact_usable
from exposureflow_api.models.knowledge import KnowledgeFact


async def embed_fact(db: AsyncSession, fact: KnowledgeFact) -> KnowledgeFact:
    vector = embed_text(f"{fact.subject}\n{fact.fact_text}")
    fact.metadata_json = {
        **(fact.metadata_json or {}),
        "embedding_dims": len(vector),
        "embedding_model": "deterministic_v1",
    }
    # Store in metadata for ORM/tests; migration 012 adds pgvector column for Postgres queries.
    fact.metadata_json["embedding"] = vector
    await db.flush()
    return fact


async def search_facts(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID | None,
    query: str,
    limit: int = 10,
    market: str | None = None,
    language: str | None = None,
    min_similarity: float = 0.78,
) -> list[tuple[KnowledgeFact, float]]:
    stmt = select(KnowledgeFact).where(
        KnowledgeFact.workspace_id == workspace_id,
        KnowledgeFact.status == "approved",
    )
    if site_id:
        stmt = stmt.where(KnowledgeFact.site_id == site_id)
    if market:
        stmt = stmt.where(KnowledgeFact.market == market)
    if language:
        stmt = stmt.where(KnowledgeFact.language == language)
    result = await db.execute(stmt)
    query_vec = embed_text(query)
    scored: list[tuple[KnowledgeFact, float]] = []
    for fact in result.scalars().all():
        if not is_fact_usable(fact):
            continue
        stored = (fact.metadata_json or {}).get("embedding")
        if not stored:
            continue
        sim = cosine_similarity(query_vec, stored)
        if sim >= min_similarity:
            scored.append((fact, sim))
    scored.sort(key=lambda x: -x[1])
    return scored[:limit]
