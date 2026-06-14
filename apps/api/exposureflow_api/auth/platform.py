"""Platform-level authorization for internal admin operations."""

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.deps import get_current_user
from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.common.errors import APIError
from exposureflow_api.database import get_db
from exposureflow_api.models import WorkspaceMembership


async def require_platform_admin(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user.user_id,
            WorkspaceMembership.status == "active",
            WorkspaceMembership.role == "support_admin",
        ).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        return user

    raise APIError(
        code="PERMISSION_DENIED",
        message="Platform admin access required.",
        status_code=403,
    )
