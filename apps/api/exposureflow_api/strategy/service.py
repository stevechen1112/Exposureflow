"""Strategy layer service — intake, scope, keyword pyramid, delivery commitment."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.common.audit import record_audit
from exposureflow_api.models.strategy import (
    BusinessIntake,
    DeliveryCommitment,
    KeywordPyramidNode,
    ProductServiceScope,
)
from exposureflow_api.strategy.business_fit import evaluate_site_keyword_fit


async def list_intakes(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> list[BusinessIntake]:
    result = await db.execute(
        select(BusinessIntake)
        .where(
            BusinessIntake.workspace_id == workspace_id,
            BusinessIntake.site_id == site_id,
        )
        .order_by(BusinessIntake.created_at.desc())
    )
    return list(result.scalars().all())


async def create_intake(
    db: AsyncSession, workspace_id: UUID, **fields
) -> BusinessIntake:
    row = BusinessIntake(workspace_id=workspace_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def get_intake(db: AsyncSession, workspace_id: UUID, intake_id: UUID) -> BusinessIntake:
    row = await db.get(BusinessIntake, intake_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Business intake")
    return row


async def update_intake(
    db: AsyncSession, workspace_id: UUID, intake_id: UUID, updates: dict
) -> BusinessIntake:
    row = await get_intake(db, workspace_id, intake_id)
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def approve_intake(
    db: AsyncSession, workspace_id: UUID, intake_id: UUID, user_id: UUID
) -> BusinessIntake:
    row = await get_intake(db, workspace_id, intake_id)
    row.status = "approved"
    row.approved_by = user_id
    row.approved_at = datetime.now(timezone.utc)
    await record_audit(
        db,
        action="strategy.intake.approve",
        target_type="business_intake",
        target_id=str(intake_id),
        workspace_id=workspace_id,
        actor_user_id=user_id,
    )
    await db.flush()
    return row


async def list_product_scopes(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    status: str | None = None,
) -> list[ProductServiceScope]:
    stmt = select(ProductServiceScope).where(
        ProductServiceScope.workspace_id == workspace_id,
        ProductServiceScope.site_id == site_id,
    )
    if status:
        stmt = stmt.where(ProductServiceScope.status == status)
    result = await db.execute(stmt.order_by(ProductServiceScope.priority.desc()))
    return list(result.scalars().all())


async def create_product_scope(
    db: AsyncSession, workspace_id: UUID, **fields
) -> ProductServiceScope:
    row = ProductServiceScope(workspace_id=workspace_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def get_product_scope(
    db: AsyncSession, workspace_id: UUID, scope_id: UUID
) -> ProductServiceScope:
    row = await db.get(ProductServiceScope, scope_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Product service scope")
    return row


async def update_product_scope(
    db: AsyncSession, workspace_id: UUID, scope_id: UUID, updates: dict
) -> ProductServiceScope:
    row = await get_product_scope(db, workspace_id, scope_id)
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def list_keyword_pyramid(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    status: str | None = None,
    market: str | None = None,
    language: str | None = None,
) -> list[KeywordPyramidNode]:
    stmt = select(KeywordPyramidNode).where(
        KeywordPyramidNode.workspace_id == workspace_id,
        KeywordPyramidNode.site_id == site_id,
    )
    if status:
        stmt = stmt.where(KeywordPyramidNode.business_fit_status == status)
    if market:
        stmt = stmt.where(KeywordPyramidNode.target_market == market)
    if language:
        stmt = stmt.where(KeywordPyramidNode.language == language)
    result = await db.execute(stmt.order_by(KeywordPyramidNode.priority.desc()))
    return list(result.scalars().all())


async def create_keyword_node(
    db: AsyncSession, workspace_id: UUID, **fields
) -> KeywordPyramidNode:
    row = KeywordPyramidNode(workspace_id=workspace_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def get_keyword_node(
    db: AsyncSession, workspace_id: UUID, node_id: UUID
) -> KeywordPyramidNode:
    row = await db.get(KeywordPyramidNode, node_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Keyword pyramid node")
    return row


async def update_keyword_node(
    db: AsyncSession, workspace_id: UUID, node_id: UUID, updates: dict
) -> KeywordPyramidNode:
    row = await get_keyword_node(db, workspace_id, node_id)
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def approve_keyword_node(
    db: AsyncSession, workspace_id: UUID, node_id: UUID, user_id: UUID
) -> KeywordPyramidNode:
    row = await get_keyword_node(db, workspace_id, node_id)
    row.approved_by = user_id
    row.approved_at = datetime.now(timezone.utc)
    if row.business_fit_status == "needs_review":
        row.business_fit_status = "in_scope"
    await record_audit(
        db,
        action="strategy.keyword_pyramid.approve",
        target_type="keyword_pyramid_node",
        target_id=str(node_id),
        workspace_id=workspace_id,
        actor_user_id=user_id,
    )
    await db.flush()
    return row


async def list_delivery_commitments(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> list[DeliveryCommitment]:
    result = await db.execute(
        select(DeliveryCommitment)
        .where(
            DeliveryCommitment.workspace_id == workspace_id,
            DeliveryCommitment.site_id == site_id,
        )
        .order_by(DeliveryCommitment.effective_from.desc())
    )
    return list(result.scalars().all())


async def create_delivery_commitment(
    db: AsyncSession, workspace_id: UUID, **fields
) -> DeliveryCommitment:
    row = DeliveryCommitment(workspace_id=workspace_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def get_delivery_commitment(
    db: AsyncSession, workspace_id: UUID, commitment_id: UUID
) -> DeliveryCommitment:
    row = await db.get(DeliveryCommitment, commitment_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Delivery commitment")
    return row


async def update_delivery_commitment(
    db: AsyncSession, workspace_id: UUID, commitment_id: UUID, updates: dict
) -> DeliveryCommitment:
    row = await get_delivery_commitment(db, workspace_id, commitment_id)
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def evaluate_business_fit(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, keyword: str
):
    return await evaluate_site_keyword_fit(db, workspace_id, site_id, keyword)
