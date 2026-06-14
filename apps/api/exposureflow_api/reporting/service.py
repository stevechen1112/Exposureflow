"""Client approval and deliverable mutations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.models import RoadmapItem


async def set_roadmap_client_approval(
    db: AsyncSession,
    workspace_id: UUID,
    item_id: UUID,
    *,
    site_id: UUID,
    approval: str,
    actor_user_id: UUID,
    note: str | None = None,
) -> RoadmapItem:
    if approval not in {"approved", "rejected", "pending"}:
        raise APIError(code="INVALID_APPROVAL", message="approval must be approved/rejected/pending", status_code=400)
    item = await db.get(RoadmapItem, item_id)
    if item is None or item.workspace_id != workspace_id:
        raise not_found("Roadmap item")
    if item.site_id != site_id:
        raise APIError(
            code="SITE_MISMATCH",
            message="Roadmap item does not belong to the specified site",
            status_code=403,
        )
    item.client_approval_status = approval
    await record_audit(
        db,
        action=f"client.roadmap_item.{approval}",
        target_type="roadmap_item",
        target_id=str(item_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"note": note},
    )
    await db.flush()
    return item
