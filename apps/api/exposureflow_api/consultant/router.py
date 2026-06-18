"""Consultant work queue API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission, role_has_permission
from exposureflow_api.consultant import service
from exposureflow_api.consultant.schemas import ConsultantInboxResponse
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.models.tenant import Workspace

router = APIRouter(prefix="/api/v1/consultant", tags=["consultant"])


@router.get("/inbox", response_model=ConsultantInboxResponse)
async def get_consultant_inbox(
    site_id: UUID | None = Query(default=None),
    scope: str = Query(default="workspace", pattern="^(workspace|account)$"),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> ConsultantInboxResponse:
    user, membership, workspace_id = ctx
    if scope == "account":
        ws = await db.get(Workspace, workspace_id)
        if ws is None:
            from exposureflow_api.common.errors import not_found

            raise not_found("Workspace")
        include_all = role_has_permission(membership.role, "agency:read")
        return await service.build_account_consultant_inbox(
            db,
            user_id=user.user_id,
            account_id=ws.account_id,
            include_all_account_clients=include_all,
        )
    if site_id is not None:
        await get_site_in_workspace(db, workspace_id, site_id)
    return await service.build_consultant_inbox(db, workspace_id, site_id=site_id)
