from datetime import UTC, datetime
from uuid import UUID

import pyotp
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.deps import get_current_user
from exposureflow_api.auth.jwt import AuthContext, create_access_token
from exposureflow_api.auth.permissions import role_has_permission
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.crypto import encrypt_secret
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.database import get_db
from exposureflow_api.models import ImpersonationSession, User, UserSecurity, WorkspaceMembership

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TwoFactorSetupResponse:
    result = await db.execute(select(User).where(User.id == user_ctx.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise not_found("User")

    secret = pyotp.random_base32()
    security = await db.get(UserSecurity, user.id)
    if security is None:
        security = UserSecurity(user_id=user.id)
        db.add(security)
    security.totp_secret_encrypted = encrypt_secret(secret)
    await db.commit()

    totp = pyotp.TOTP(secret)
    return TwoFactorSetupResponse(
        secret=secret,
        provisioning_uri=totp.provisioning_uri(name=user.email, issuer_name="ExposureFlow"),
    )


@router.post("/2fa/verify")
async def verify_two_factor(
    body: TwoFactorVerifyRequest,
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    from exposureflow_api.common.crypto import decrypt_secret

    security = await db.get(UserSecurity, user_ctx.user_id)
    if security is None or security.totp_secret_encrypted is None:
        raise APIError(code="2FA_NOT_CONFIGURED", message="2FA not configured.", status_code=400)

    secret = decrypt_secret(security.totp_secret_encrypted)
    if not pyotp.TOTP(secret).verify(body.code, valid_window=1):
        raise APIError(code="2FA_INVALID", message="Invalid verification code.", status_code=400)

    security.totp_enabled = True
    await record_audit(
        db,
        action="auth.2fa_enabled",
        target_type="user",
        target_id=str(user_ctx.user_id),
        actor_user_id=user_ctx.user_id,
    )
    await db.commit()
    return {"enabled": True}


class ImpersonationRequest(BaseModel):
    target_user_id: UUID
    workspace_id: UUID | None = None
    reason: str = Field(min_length=10, max_length=500)


class ImpersonationResponse(BaseModel):
    access_token: str
    impersonation_session_id: UUID


@router.post("/impersonate", response_model=ImpersonationResponse)
async def impersonate_user(
    body: ImpersonationRequest,
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImpersonationResponse:
    if body.workspace_id is not None:
        membership = await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == body.workspace_id,
                WorkspaceMembership.user_id == user_ctx.user_id,
                WorkspaceMembership.status == "active",
            )
        )
        actor_membership = membership.scalar_one_or_none()
        if actor_membership is None or not role_has_permission(actor_membership.role, "impersonate"):
            raise APIError(code="PERMISSION_DENIED", message="Impersonation not allowed.", status_code=403)
    else:
        support = await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.user_id == user_ctx.user_id,
                WorkspaceMembership.role == "support_admin",
            )
        )
        if support.scalar_one_or_none() is None:
            raise APIError(code="PERMISSION_DENIED", message="Support admin required.", status_code=403)

    target = await db.get(User, body.target_user_id)
    if target is None:
        raise not_found("User")

    audit = await record_audit(
        db,
        action="support.impersonation_started",
        target_type="user",
        target_id=str(target.id),
        workspace_id=body.workspace_id,
        actor_user_id=user_ctx.user_id,
        metadata={"reason": body.reason},
    )
    session = ImpersonationSession(
        support_user_id=user_ctx.user_id,
        target_user_id=target.id,
        workspace_id=body.workspace_id,
        reason=body.reason,
        started_at=datetime.now(UTC),
        audit_log_id=audit.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    token = create_access_token(target.id, target.email, target.name)
    return ImpersonationResponse(access_token=token, impersonation_session_id=session.id)
