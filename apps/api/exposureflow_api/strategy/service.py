"""Strategy layer service — intake, scope, keyword pyramid, delivery commitment."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found, validation_error
from exposureflow_api.common.audit import record_audit
from exposureflow_api.models.strategy import (
    BusinessConstraintRule,
    BusinessIntake,
    DeliveryCommitment,
    KeywordPyramidNode,
    ProductServiceScope,
)
from exposureflow_api.strategy.business_fit import evaluate_site_keyword_fit
from exposureflow_api.strategy.intake_impact import apply_intake_impact, preview_intake_impact
from exposureflow_api.strategy.keyword_research import infer_funnel_stage, infer_keyword_level
from exposureflow_api.strategy.keyword_utils import normalize_keyword
from exposureflow_api.strategy.pyramid_topic_bridge import link_pyramid_node_to_topic_graph, sync_site_pyramid_links


def _intake_content_fields(intake: BusinessIntake) -> dict:
    return {
        "company_summary": intake.company_summary,
        "market_notes": intake.market_notes,
        "customer_segments_json": list(intake.customer_segments_json or []),
        "domestic_markets_json": list(intake.domestic_markets_json or []),
        "export_markets_json": list(intake.export_markets_json or []),
        "sales_regions_json": list(intake.sales_regions_json or []),
        "strategic_goals_json": list(intake.strategic_goals_json or []),
        "constraints_json": list(intake.constraints_json or []),
    }


async def _next_version_number(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> int:
    result = await db.execute(
        select(BusinessIntake.version_number)
        .where(
            BusinessIntake.workspace_id == workspace_id,
            BusinessIntake.site_id == site_id,
        )
        .order_by(BusinessIntake.version_number.desc())
        .limit(1)
    )
    current = result.scalar_one_or_none()
    return int(current or 0) + 1


async def _get_site_draft(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> BusinessIntake | None:
    result = await db.execute(
        select(BusinessIntake).where(
            BusinessIntake.workspace_id == workspace_id,
            BusinessIntake.site_id == site_id,
            BusinessIntake.status == "draft",
        )
    )
    return result.scalar_one_or_none()


async def list_intakes(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> list[BusinessIntake]:
    result = await db.execute(
        select(BusinessIntake)
        .where(
            BusinessIntake.workspace_id == workspace_id,
            BusinessIntake.site_id == site_id,
        )
        .order_by(BusinessIntake.version_number.desc(), BusinessIntake.created_at.desc())
    )
    return list(result.scalars().all())


async def get_current_intake(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> BusinessIntake | None:
    result = await db.execute(
        select(BusinessIntake).where(
            BusinessIntake.workspace_id == workspace_id,
            BusinessIntake.site_id == site_id,
            BusinessIntake.is_current.is_(True),
            BusinessIntake.status == "approved",
        )
    )
    return result.scalar_one_or_none()


async def create_intake(
    db: AsyncSession, workspace_id: UUID, **fields
) -> BusinessIntake:
    site_id = fields["site_id"]
    if await get_current_intake(db, workspace_id, site_id) is not None:
        raise validation_error(
            "Site already has a current approved intake. Fork a new version instead.",
            code="INTAKE_CURRENT_EXISTS",
        )
    if await _get_site_draft(db, workspace_id, site_id) is not None:
        raise validation_error(
            "A draft intake already exists for this site. Edit the draft instead.",
            code="INTAKE_DRAFT_EXISTS",
        )
    version_number = await _next_version_number(db, workspace_id, site_id)
    row = BusinessIntake(
        workspace_id=workspace_id,
        version_number=version_number,
        **fields,
    )
    db.add(row)
    await db.flush()
    return row


async def fork_intake(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, parent: BusinessIntake
) -> BusinessIntake:
    if parent.status not in ("approved", "archived"):
        raise validation_error("Only approved intakes can be forked.", code="INTAKE_FORK_INVALID")
    if await _get_site_draft(db, workspace_id, site_id) is not None:
        raise validation_error(
            "A draft intake already exists for this site.",
            code="INTAKE_DRAFT_EXISTS",
        )
    version_number = await _next_version_number(db, workspace_id, site_id)
    row = BusinessIntake(
        workspace_id=workspace_id,
        site_id=site_id,
        status="draft",
        version_number=version_number,
        parent_intake_id=parent.id,
        is_current=False,
        **_intake_content_fields(parent),
    )
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
    if row.status != "draft":
        raise validation_error(
            "Only draft intakes can be edited.",
            code="INTAKE_NOT_EDITABLE",
        )
    for key, value in updates.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def preview_intake(
    db: AsyncSession, workspace_id: UUID, intake_id: UUID
) -> dict:
    row = await get_intake(db, workspace_id, intake_id)
    if row.status != "draft":
        raise validation_error(
            "Impact preview is only available for draft intakes.",
            code="INTAKE_NOT_PREVIEWABLE",
        )
    previous = None
    if row.parent_intake_id:
        previous = await get_intake(db, workspace_id, row.parent_intake_id)
    elif (current := await get_current_intake(db, workspace_id, row.site_id)) and current.id != row.id:
        previous = current
    preview = await preview_intake_impact(
        db, workspace_id, row.site_id, row, previous=previous
    )
    return {
        "keywords_to_add": preview.keywords_to_add,
        "keywords_to_block": preview.keywords_to_block,
        "constraint_rules_to_upsert": preview.constraint_rules_to_upsert,
        "scopes_to_upsert": preview.scopes_to_upsert,
        "opportunities_affected": preview.opportunities_affected,
        "opportunity_samples": preview.opportunity_samples,
        "changes_summary": preview.changes_summary,
    }


async def approve_intake(
    db: AsyncSession, workspace_id: UUID, intake_id: UUID, user_id: UUID
) -> tuple[BusinessIntake, dict]:
    row = await get_intake(db, workspace_id, intake_id)
    if row.status != "draft":
        raise validation_error(
            "Only draft intakes can be approved.",
            code="INTAKE_NOT_APPROVABLE",
        )

    current = await get_current_intake(db, workspace_id, row.site_id)
    if current is not None and current.id != row.id:
        current.status = "archived"
        current.is_current = False
        current.archived_at = datetime.now(timezone.utc)

    row.status = "approved"
    row.is_current = True
    row.approved_by = user_id
    row.approved_at = datetime.now(timezone.utc)

    impact = await apply_intake_impact(
        db,
        workspace_id,
        row.site_id,
        row,
        user_id=user_id,
    )

    await record_audit(
        db,
        action="strategy.intake.approve",
        target_type="business_intake",
        target_id=str(intake_id),
        workspace_id=workspace_id,
        actor_user_id=user_id,
        metadata={
            "version_number": row.version_number,
            "keywords_created": impact.keywords_created,
            "keywords_updated": impact.keywords_updated,
            "constraint_rules_synced": impact.constraint_rules_synced,
            "opportunities_rescored": impact.opportunities_rescored,
        },
    )
    await db.flush()
    return row, {
        "scope_id": impact.scope_id,
        "keywords_created": impact.keywords_created,
        "keywords_updated": impact.keywords_updated,
        "constraint_rules_synced": impact.constraint_rules_synced,
        "opportunities_rescored": impact.opportunities_rescored,
    }


async def reapply_current_intake(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, user_id: UUID
) -> tuple[BusinessIntake, dict]:
    row = await get_current_intake(db, workspace_id, site_id)
    if row is None:
        raise not_found("Current business intake")
    impact = await apply_intake_impact(
        db,
        workspace_id,
        site_id,
        row,
        user_id=user_id,
    )
    await record_audit(
        db,
        action="strategy.intake.reapply",
        target_type="business_intake",
        target_id=str(row.id),
        workspace_id=workspace_id,
        actor_user_id=user_id,
        metadata={
            "version_number": row.version_number,
            "keywords_created": impact.keywords_created,
            "keywords_updated": impact.keywords_updated,
            "constraint_rules_synced": impact.constraint_rules_synced,
            "opportunities_rescored": impact.opportunities_rescored,
        },
    )
    await db.flush()
    return row, {
        "scope_id": impact.scope_id,
        "keywords_created": impact.keywords_created,
        "keywords_updated": impact.keywords_updated,
        "constraint_rules_synced": impact.constraint_rules_synced,
        "opportunities_rescored": impact.opportunities_rescored,
    }


async def list_constraint_rules(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    active_only: bool = True,
) -> list[BusinessConstraintRule]:
    stmt = select(BusinessConstraintRule).where(
        BusinessConstraintRule.workspace_id == workspace_id,
        BusinessConstraintRule.site_id == site_id,
    )
    if active_only:
        stmt = stmt.where(BusinessConstraintRule.is_active.is_(True))
    result = await db.execute(stmt.order_by(BusinessConstraintRule.created_at.desc()))
    return list(result.scalars().all())


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
    node_type = fields.get("node_type") or "pillar"
    if not fields.get("keyword_level"):
        fields["keyword_level"] = infer_keyword_level(str(node_type))
    if not fields.get("funnel_stage") and fields.get("intent"):
        fields["funnel_stage"] = infer_funnel_stage(fields.get("intent"), str(node_type))
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
        setattr(row, key, value)
    await db.flush()
    return row


async def approve_keyword_node(
    db: AsyncSession, workspace_id: UUID, node_id: UUID, user_id: UUID
) -> KeywordPyramidNode:
    row = await get_keyword_node(db, workspace_id, node_id)
    row.approved_by = user_id
    row.approved_at = datetime.now(timezone.utc)
    if row.business_fit_status in ("needs_review", "out_of_scope"):
        row.business_fit_status = "in_scope"
    if not row.keyword_level:
        row.keyword_level = infer_keyword_level(row.node_type)
    await link_pyramid_node_to_topic_graph(db, row)
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


async def delete_keyword_node(
    db: AsyncSession, workspace_id: UUID, node_id: UUID, user_id: UUID
) -> None:
    row = await get_keyword_node(db, workspace_id, node_id)
    children = await db.execute(
        select(KeywordPyramidNode).where(KeywordPyramidNode.parent_id == row.id)
    )
    for child in children.scalars().all():
        child.parent_id = None
    await db.delete(row)
    await record_audit(
        db,
        action="strategy.keyword_pyramid.delete",
        target_type="keyword_pyramid_node",
        target_id=str(node_id),
        workspace_id=workspace_id,
        actor_user_id=user_id,
        metadata={"keyword": row.keyword, "node_type": row.node_type},
    )
    await db.flush()


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
    # Deactivate any existing active commitments for same site
    from sqlalchemy import update
    await db.execute(
        update(DeliveryCommitment)
        .where(
            DeliveryCommitment.workspace_id == workspace_id,
            DeliveryCommitment.site_id == fields.get("site_id"),
            DeliveryCommitment.status == "active",
        )
        .values(status="archived")
    )
    row = DeliveryCommitment(workspace_id=workspace_id, status="active", **fields)
    db.add(row)
    await db.flush()
    return row


async def deactivate_delivery_commitment(
    db: AsyncSession, workspace_id: UUID, commitment_id: UUID
) -> DeliveryCommitment:
    from exposureflow_api.common.errors import not_found
    row = await db.get(DeliveryCommitment, commitment_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Delivery commitment")
    row.status = "archived"
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


async def bulk_import_keyword_nodes(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    rows: list[dict],
    *,
    created_by: str = "consultant",
) -> dict[str, int | list[str]]:
    existing = await list_keyword_pyramid(db, workspace_id, site_id)
    by_keyword = {normalize_keyword(node.keyword): node for node in existing}
    created = 0
    skipped = 0
    errors: list[str] = []

    for index, raw in enumerate(rows, start=1):
        keyword = str(raw.get("keyword") or "").strip()
        if not keyword:
            errors.append(f"row {index}: empty keyword")
            continue
        key = normalize_keyword(keyword)
        if key in by_keyword:
            skipped += 1
            continue

        parent_id = raw.get("parent_id")
        parent_keyword = raw.get("parent_keyword")
        if not parent_id and parent_keyword:
            parent = by_keyword.get(normalize_keyword(str(parent_keyword)))
            if parent:
                parent_id = parent.id

        node_type = str(raw.get("node_type") or "pillar")
        row = KeywordPyramidNode(
            workspace_id=workspace_id,
            site_id=site_id,
            keyword=keyword,
            node_type=node_type,
            parent_id=parent_id,
            product_service_scope_id=raw.get("product_service_scope_id"),
            intent=raw.get("intent"),
            target_market=raw.get("target_market"),
            language=raw.get("language"),
            keyword_level=raw.get("keyword_level") or infer_keyword_level(node_type),
            funnel_stage=raw.get("funnel_stage")
            or infer_funnel_stage(raw.get("intent"), node_type),
            is_target=bool(raw.get("is_target")),
            business_fit_status=str(raw.get("business_fit_status") or "needs_review"),
            priority=int(raw.get("priority") or 3),
            created_by=created_by,
            evidence_json=dict(raw.get("evidence_json") or {}),
        )
        db.add(row)
        await db.flush()
        by_keyword[key] = row
        created += 1

    return {"created": created, "skipped": skipped, "errors": errors}


async def sync_pyramid_topic_bridge(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> dict[str, int]:
    return await sync_site_pyramid_links(db, workspace_id, site_id)
