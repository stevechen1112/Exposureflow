"""Knowledge base service — brand profile, sources, facts."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.models.knowledge import (
    KnowledgeFact,
    KnowledgeSource,
    WorkspaceBrandProfile,
)


async def get_brand_profile(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID | None = None,
) -> WorkspaceBrandProfile | None:
    stmt = select(WorkspaceBrandProfile).where(
        WorkspaceBrandProfile.workspace_id == workspace_id,
    )
    if site_id:
        stmt = stmt.where(WorkspaceBrandProfile.site_id == site_id)
    result = await db.execute(stmt.order_by(WorkspaceBrandProfile.updated_at.desc()))
    return result.scalars().first()


async def upsert_brand_profile(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    site_id: UUID | None,
    owner_user_id: UUID | None,
    **fields,
) -> WorkspaceBrandProfile:
    existing = await get_brand_profile(db, workspace_id, site_id)
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        await db.flush()
        return existing
    row = WorkspaceBrandProfile(
        workspace_id=workspace_id,
        site_id=site_id,
        **fields,
    )
    db.add(row)
    await db.flush()
    return row


async def list_sources(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID | None = None,
    *,
    status: str | None = None,
) -> list[KnowledgeSource]:
    stmt = select(KnowledgeSource).where(KnowledgeSource.workspace_id == workspace_id)
    if site_id:
        stmt = stmt.where(KnowledgeSource.site_id == site_id)
    if status:
        stmt = stmt.where(KnowledgeSource.status == status)
    result = await db.execute(stmt.order_by(KnowledgeSource.updated_at.desc()))
    sources = list(result.scalars().all())
    # Eager-load fact counts for each source
    if sources:
        source_ids = [s.id for s in sources]
        from sqlalchemy import func
        from exposureflow_api.models.knowledge import KnowledgeFact
        fact_counts = await db.execute(
            select(KnowledgeFact.knowledge_source_id, func.count(KnowledgeFact.id))
            .where(KnowledgeFact.knowledge_source_id.in_(source_ids))
            .group_by(KnowledgeFact.knowledge_source_id)
        )
        counts = {row[0]: row[1] for row in fact_counts.all()}
        for s in sources:
            s._fact_count = counts.get(s.id, 0)
    return sources


async def create_source(
    db: AsyncSession,
    workspace_id: UUID,
    owner_user_id: UUID | None,
    **fields,
) -> KnowledgeSource:
    content_text = fields.pop("content_text", None)
    fields.pop("source_url", None)  # frontend alias, not a model field
    row = KnowledgeSource(workspace_id=workspace_id, owner_user_id=owner_user_id, **fields)
    db.add(row)
    await db.flush()
    if content_text:
        fact = KnowledgeFact(
            workspace_id=workspace_id,
            site_id=row.site_id,
            knowledge_source_id=row.id,
            fact_type="manual_input",
            subject=row.title,
            fact_text=content_text,
            market=row.market,
            language=row.language,
            status="draft",
        )
        db.add(fact)
        await db.flush()
    return row


async def get_source(db: AsyncSession, workspace_id: UUID, source_id: UUID) -> KnowledgeSource:
    row = await db.get(KnowledgeSource, source_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Knowledge source")
    return row


async def update_source(
    db: AsyncSession, workspace_id: UUID, source_id: UUID, updates: dict
) -> KnowledgeSource:
    row = await get_source(db, workspace_id, source_id)
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def approve_source(db: AsyncSession, workspace_id: UUID, source_id: UUID) -> KnowledgeSource:
    row = await get_source(db, workspace_id, source_id)
    row.status = "approved"
    row.version += 1
    await db.flush()
    return row


async def revoke_source(db: AsyncSession, workspace_id: UUID, source_id: UUID) -> KnowledgeSource:
    row = await get_source(db, workspace_id, source_id)
    row.status = "revoked"
    await db.flush()
    return row


async def list_facts(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID | None = None,
    *,
    fact_type: str | None = None,
    status: str | None = None,
    market: str | None = None,
    language: str | None = None,
) -> list[KnowledgeFact]:
    stmt = select(KnowledgeFact).where(KnowledgeFact.workspace_id == workspace_id)
    if site_id:
        stmt = stmt.where(KnowledgeFact.site_id == site_id)
    if fact_type:
        stmt = stmt.where(KnowledgeFact.fact_type == fact_type)
    if status:
        stmt = stmt.where(KnowledgeFact.status == status)
    if market:
        stmt = stmt.where(KnowledgeFact.market == market)
    if language:
        stmt = stmt.where(KnowledgeFact.language == language)
    result = await db.execute(stmt.order_by(KnowledgeFact.updated_at.desc()))
    return list(result.scalars().all())


async def create_fact(db: AsyncSession, workspace_id: UUID, **fields) -> KnowledgeFact:
    row = KnowledgeFact(workspace_id=workspace_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def get_fact(db: AsyncSession, workspace_id: UUID, fact_id: UUID) -> KnowledgeFact:
    row = await db.get(KnowledgeFact, fact_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Knowledge fact")
    return row


async def update_fact(
    db: AsyncSession, workspace_id: UUID, fact_id: UUID, updates: dict
) -> KnowledgeFact:
    row = await get_fact(db, workspace_id, fact_id)
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


def is_fact_usable(fact: KnowledgeFact, *, now: datetime | None = None) -> bool:
    if fact.status != "approved":
        return False
    if fact.expires_at and (now or datetime.now(timezone.utc)) >= fact.expires_at:
        return False
    return True
