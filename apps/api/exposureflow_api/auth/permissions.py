"""RBAC permission matrix for workspace-scoped operations."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.deps import get_current_user, get_workspace_membership, require_workspace_access
from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.common.errors import APIError
from exposureflow_api.database import get_db
from exposureflow_api.models import WorkspaceMembership

ROLE_RANK: dict[str, int] = {
    "client_viewer": 10,
    "analyst": 20,
    "editor": 30,
    "strategist": 40,
    "billing_admin": 45,
    "admin": 50,
    "owner": 60,
    "support_admin": 70,
}

PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "workspace:read",
        "workspace:write",
        "site:read",
        "site:write",
        "member:read",
        "member:write",
        "invitation:write",
        "integration:read",
        "integration:write",
        "job:read",
        "job:write",
        "api_key:write",
        "billing:read",
        "impersonate",
        "client:approve",
    },
    "admin": {
        "workspace:read",
        "workspace:write",
        "site:read",
        "site:write",
        "member:read",
        "member:write",
        "invitation:write",
        "integration:read",
        "integration:write",
        "job:read",
        "job:write",
        "api_key:write",
        "billing:read",
        "client:approve",
    },
    "client_viewer": {
        "workspace:read",
        "site:read",
        "client:approve",
    },
    "strategist": {
        "workspace:read",
        "site:read",
        "site:write",
        "member:read",
        "integration:read",
        "job:read",
        "job:write",
        "client:approve",
    },
    "editor": {
        "workspace:read",
        "site:read",
        "site:write",
        "job:read",
        "client:approve",
    },
    "analyst": {
        "workspace:read",
        "site:read",
        "job:read",
    },
    "billing_admin": {
        "workspace:read",
        "billing:read",
    },
    "support_admin": {
        "workspace:read",
        "site:read",
        "member:read",
        "impersonate",
    },
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, set())


def require_permission(permission: str) -> Callable[..., Any]:
    async def _check(
        ctx: tuple[AuthContext, WorkspaceMembership, UUID] = Depends(require_workspace_access),
    ) -> tuple[AuthContext, WorkspaceMembership, UUID]:
        _user, membership, workspace_id = ctx
        if not role_has_permission(membership.role, permission):
            raise APIError(
                code="PERMISSION_DENIED",
                message=f"Role '{membership.role}' cannot perform '{permission}'.",
                status_code=403,
            )
        return ctx

    return _check


def require_min_role(min_role: str) -> Callable[..., Any]:
    min_rank = ROLE_RANK[min_role]

    async def _check(
        workspace_id: UUID,
        user: AuthContext = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> WorkspaceMembership:
        membership = await get_workspace_membership(workspace_id, user, db)
        if ROLE_RANK.get(membership.role, 0) < min_rank:
            raise APIError(
                code="PERMISSION_DENIED",
                message=f"Minimum role '{min_role}' required.",
                status_code=403,
            )
        return membership

    return _check
