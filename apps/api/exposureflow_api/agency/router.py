from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.agency.service import build_agency_dashboard
from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.database import get_db
from exposureflow_api.models.tenant import Workspace

router = APIRouter(prefix="/api/v1/agency", tags=["agency"])


@router.get("/dashboard")
async def agency_dashboard(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("agency:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _membership, workspace_id = ctx
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        from exposureflow_api.common.errors import not_found

        raise not_found("Workspace")
    return await build_agency_dashboard(
        db,
        ws.account_id,
        user_id=user.user_id,
        include_all_account_clients=True,
    )
