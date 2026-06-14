from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext, decode_access_token
from exposureflow_api.common.errors import workspace_access_denied
from exposureflow_api.database import get_db
from exposureflow_api.models import WorkspaceMembership
from exposureflow_api.config import settings
from exposureflow_api.security.ip_allowlist import ensure_ip_allowed
from exposureflow_api.security.settings import get_or_create_security_settings
from exposureflow_api.models import UserSecurity

security = HTTPBearer(auto_error=False)


def _client_ip(request: Request) -> str | None:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


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
    request: Request,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id"),
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[AuthContext, WorkspaceMembership, UUID]:
    workspace_id = UUID(x_workspace_id)
    membership = await get_workspace_membership(workspace_id, user, db)
    await ensure_ip_allowed(db, workspace_id, _client_ip(request))
    sec_settings = await get_or_create_security_settings(db, workspace_id)
    if sec_settings.require_2fa:
        user_security = await db.get(UserSecurity, user.user_id)
        if user_security is None or not user_security.totp_enabled:
            from exposureflow_api.common.errors import APIError

            raise APIError(
                code="2FA_REQUIRED",
                message="Two-factor authentication is required for this workspace.",
                status_code=403,
            )
        if "2fa" not in user.amr:
            from exposureflow_api.common.errors import APIError

            raise APIError(
                code="2FA_STEP_UP_REQUIRED",
                message="Re-authenticate with 2FA for this workspace.",
                status_code=403,
            )
    return user, membership, workspace_id
