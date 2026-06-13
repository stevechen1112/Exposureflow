from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext, decode_access_token
from exposureflow_api.common.errors import workspace_access_denied
from exposureflow_api.database import get_db
from exposureflow_api.models import WorkspaceMembership

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthContext:
    if credentials is None:
        raise workspace_access_denied()
    try:
        return decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise workspace_access_denied() from exc


async def get_workspace_membership(
    workspace_id: UUID,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMembership:
    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user.user_id,
            WorkspaceMembership.status == "active",
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise workspace_access_denied()
    return membership


async def require_workspace_access(
    x_workspace_id: str = Header(..., alias="X-Workspace-Id"),
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[AuthContext, WorkspaceMembership, UUID]:
    workspace_id = UUID(x_workspace_id)
    membership = await get_workspace_membership(workspace_id, user, db)
    return user, membership, workspace_id
