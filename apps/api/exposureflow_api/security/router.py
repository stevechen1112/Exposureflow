from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.models import AuditLog
from exposureflow_api.models.security_compliance import DataExportRequest, SecurityEvent
from exposureflow_api.security.credential_rotation import rotate_integration_credential
from exposureflow_api.security.data_deletion import purge_workspace_data, request_workspace_deletion
from exposureflow_api.security.data_export import create_export_request
from exposureflow_api.security.retention import apply_retention_policy
from exposureflow_api.security.schemas import (
    AuditLogResponse,
    DataExportResponse,
    SecurityEventResponse,
    SecuritySettingsResponse,
    SecuritySettingsUpdate,
    SsoConfigUpdate,
    SsoLoginRequest,
)
from exposureflow_api.security.settings import get_or_create_security_settings
from exposureflow_api.security.sso import initiate_sso_login, update_sso_config

router = APIRouter(prefix="/api/v1/security", tags=["security"])


@router.get("/settings", response_model=SecuritySettingsResponse)
async def get_settings(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> SecuritySettingsResponse:
    _user, _membership, workspace_id = ctx
    settings = await get_or_create_security_settings(db, workspace_id)
    return SecuritySettingsResponse(
        workspace_id=settings.workspace_id,
        require_2fa=settings.require_2fa,
        sso_enabled=settings.sso_enabled,
        saml_entity_id=settings.saml_entity_id,
        saml_sso_url=settings.saml_sso_url,
        ip_allowlist=list(settings.ip_allowlist or []),
        retention_days=settings.retention_days,
        deletion_status=settings.deletion_status,
    )


@router.put("/settings", response_model=SecuritySettingsResponse)
async def update_settings(
    body: SecuritySettingsUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
) -> SecuritySettingsResponse:
    user, _membership, workspace_id = ctx
    settings = await get_or_create_security_settings(db, workspace_id)
    if body.require_2fa is not None:
        settings.require_2fa = body.require_2fa
    if body.ip_allowlist is not None:
        settings.ip_allowlist = body.ip_allowlist
    if body.retention_days is not None:
        settings.retention_days = body.retention_days
    await record_audit(
        db,
        action="security.settings_updated",
        target_type="workspace",
        target_id=str(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )
    await db.flush()
    await db.commit()
    settings = await get_or_create_security_settings(db, workspace_id)
    return SecuritySettingsResponse(
        workspace_id=settings.workspace_id,
        require_2fa=settings.require_2fa,
        sso_enabled=settings.sso_enabled,
        saml_entity_id=settings.saml_entity_id,
        saml_sso_url=settings.saml_sso_url,
        ip_allowlist=list(settings.ip_allowlist or []),
        retention_days=settings.retention_days,
        deletion_status=settings.deletion_status,
    )


@router.put("/sso")
async def configure_sso(
    body: SsoConfigUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    result = await update_sso_config(
        db,
        workspace_id,
        sso_enabled=body.sso_enabled,
        saml_entity_id=body.saml_entity_id,
        saml_sso_url=body.saml_sso_url,
        saml_certificate=body.saml_certificate,
    )
    await record_audit(
        db,
        action="security.sso_updated",
        target_type="workspace",
        target_id=str(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
        metadata={"sso_enabled": body.sso_enabled},
    )
    await db.commit()
    return result


@router.post("/sso/login")
async def sso_login(
    body: SsoLoginRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await initiate_sso_login(db, workspace_id, body.email)


@router.post("/data-export", response_model=DataExportResponse)
async def export_data(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
) -> DataExportResponse:
    user, _membership, workspace_id = ctx
    export_req = await create_export_request(db, workspace_id=workspace_id, requested_by=user.user_id)
    await record_audit(
        db,
        action="security.data_export",
        target_type="data_export_request",
        target_id=str(export_req.id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(export_req)
    return export_req


@router.get("/data-export/{export_id}", response_model=DataExportResponse)
async def get_export(
    export_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> DataExportResponse:
    _user, _membership, workspace_id = ctx
    row = await db.get(DataExportRequest, export_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("DataExportRequest")
    return row


@router.post("/deletion-request")
async def request_deletion(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
):
    user, membership, workspace_id = ctx
    if membership.role != "owner":
        from exposureflow_api.common.errors import APIError

        raise APIError(code="FORBIDDEN", message="Only owners can request deletion.", status_code=403)
    settings = await request_workspace_deletion(
        db, workspace_id=workspace_id, actor_user_id=user.user_id
    )
    await db.commit()
    return {"deletion_status": settings.deletion_status}


@router.post("/purge")
async def purge_data(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
):
    user, membership, workspace_id = ctx
    if membership.role != "owner":
        from exposureflow_api.common.errors import APIError

        raise APIError(code="FORBIDDEN", message="Only owners can purge data.", status_code=403)
    await purge_workspace_data(db, workspace_id=workspace_id, actor_user_id=user.user_id)
    await db.commit()
    return {"status": "purged"}


@router.post("/retention/apply")
async def apply_retention(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
):
    user, membership, workspace_id = ctx
    if membership.role != "owner":
        from exposureflow_api.common.errors import APIError

        raise APIError(code="FORBIDDEN", message="Only owners can apply retention.", status_code=403)
    result = await apply_retention_policy(db, workspace_id)
    await db.commit()
    return result


@router.get("/events", response_model=list[SecurityEventResponse])
async def list_security_events(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SecurityEvent]:
    _user, _membership, workspace_id = ctx
    result = await db.execute(
        select(SecurityEvent)
        .where(SecurityEvent.workspace_id == workspace_id)
        .order_by(SecurityEvent.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLog]:
    _user, _membership, workspace_id = ctx
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    )
    return list(result.scalars().all())


@router.post("/credentials/{credential_id}/rotate")
async def rotate_credential(
    credential_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    credential = await rotate_integration_credential(
        db,
        credential_id=credential_id,
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )
    await db.commit()
    return {"id": str(credential.id), "key_version": credential.key_version}
