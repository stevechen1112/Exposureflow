from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext, create_access_token
from exposureflow_api.auth.platform import require_platform_admin
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.internal_admin import service as admin_service
from exposureflow_api.internal_admin.schemas import (
    AccountOverview,
    ActivationRow,
    AuditLogOverview,
    FeatureFlagsUpdate,
    ImpersonateRequest,
    IntegrationHealthRow,
    JobRunOverview,
    OnboardingFunnel,
    ProviderCostRow,
    SyncStateOverview,
    UserOverview,
    WorkspaceOverview,
)
from exposureflow_api.models import ImpersonationSession, User
from exposureflow_api.models.product_ops import PlatformStatusIncident, SupportTicket
from exposureflow_api.notifications.schemas import (
    StatusIncidentCreate,
    StatusIncidentResponse,
    StatusIncidentUpdate,
    SupportTicketResponse,
)

router = APIRouter(prefix="/api/v1/internal", tags=["internal-admin"])


@router.get("/workspaces", response_model=list[WorkspaceOverview])
async def internal_list_workspaces(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceOverview]:
    return await admin_service.list_workspaces(db)


@router.get("/accounts", response_model=list[AccountOverview])
async def internal_list_accounts(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AccountOverview]:
    return await admin_service.list_accounts(db)


@router.get("/users", response_model=list[UserOverview])
async def internal_search_users(
    email: str | None = None,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserOverview]:
    return await admin_service.search_users(db, email=email)


@router.get("/jobs", response_model=list[JobRunOverview])
async def internal_list_jobs(
    workspace_id: UUID | None = None,
    status: str | None = None,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[JobRunOverview]:
    return await admin_service.list_job_runs(db, workspace_id=workspace_id, status=status)


@router.get("/sync-states", response_model=list[SyncStateOverview])
async def internal_list_sync_states(
    workspace_id: UUID | None = None,
    failing_only: bool = False,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[SyncStateOverview]:
    return await admin_service.list_sync_states(db, workspace_id=workspace_id, failing_only=failing_only)


@router.get("/audit-logs", response_model=list[AuditLogOverview])
async def internal_list_audit_logs(
    workspace_id: UUID | None = None,
    action_prefix: str | None = None,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogOverview]:
    return await admin_service.list_audit_logs(db, workspace_id=workspace_id, action_prefix=action_prefix)


@router.patch("/workspaces/{workspace_id}/feature-flags", response_model=WorkspaceOverview)
async def internal_update_feature_flags(
    workspace_id: UUID,
    body: FeatureFlagsUpdate,
    admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceOverview:
    await admin_service.update_feature_flags(db, workspace_id, body.feature_flags)
    await record_audit(
        db,
        action="internal.feature_flags_updated",
        target_type="workspace",
        target_id=str(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=admin.user_id,
        metadata={"feature_flags": body.feature_flags},
    )
    await db.commit()
    rows = await admin_service.list_workspaces(db, limit=1000)
    match = next((r for r in rows if r.id == workspace_id), None)
    if match is None:
        raise not_found("Workspace")
    return match


@router.get("/workspaces/{workspace_id}/usage")
async def internal_workspace_usage(
    workspace_id: UUID,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await admin_service.workspace_usage(db, workspace_id)


@router.post("/impersonate")
async def internal_impersonate(
    body: ImpersonateRequest,
    admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    target = await db.get(User, body.target_user_id)
    if target is None:
        raise not_found("User")
    audit = await record_audit(
        db,
        action="support.impersonation_started",
        target_type="user",
        target_id=str(target.id),
        workspace_id=body.workspace_id,
        actor_user_id=admin.user_id,
        metadata={"reason": body.reason, "via": "internal_admin"},
    )
    session = ImpersonationSession(
        support_user_id=admin.user_id,
        target_user_id=target.id,
        workspace_id=body.workspace_id,
        reason=body.reason,
        started_at=datetime.now(UTC),
        audit_log_id=audit.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    token = create_access_token(
        target.id,
        target.email,
        target.name,
        impersonated_by=admin.user_id,
        impersonation_session_id=session.id,
        expire_minutes=60,
    )
    return {"access_token": token, "impersonation_session_id": str(session.id)}


@router.get("/cs/activation", response_model=list[ActivationRow])
async def internal_cs_activation(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ActivationRow]:
    return await admin_service.activation_dashboard(db)


@router.get("/cs/onboarding-funnel", response_model=OnboardingFunnel)
async def internal_cs_funnel(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> OnboardingFunnel:
    return await admin_service.onboarding_funnel(db)


@router.get("/integration-health", response_model=list[IntegrationHealthRow])
async def internal_integration_health(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[IntegrationHealthRow]:
    return await admin_service.integration_health(db)


@router.get("/provider-costs", response_model=list[ProviderCostRow])
async def internal_provider_costs(
    days: int = 30,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderCostRow]:
    return await admin_service.provider_costs(db, days=days)


@router.get("/support/tickets", response_model=list[SupportTicketResponse])
async def internal_list_support_tickets(
    workspace_id: UUID | None = None,
    admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[SupportTicketResponse]:
    stmt = select(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(200)
    if workspace_id:
        stmt = stmt.where(SupportTicket.workspace_id == workspace_id)
    result = await db.execute(stmt)
    tickets = list(result.scalars().all())
    await record_audit(
        db,
        action="internal.support_tickets_listed",
        target_type="support_ticket",
        target_id=None,
        actor_user_id=admin.user_id,
        metadata={"workspace_id": str(workspace_id) if workspace_id else None, "count": len(tickets)},
    )
    await db.commit()
    return tickets


@router.get("/status/incidents", response_model=list[StatusIncidentResponse])
async def internal_list_incidents(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[StatusIncidentResponse]:
    result = await db.execute(
        select(PlatformStatusIncident).order_by(PlatformStatusIncident.started_at.desc()).limit(50)
    )
    return list(result.scalars().all())


@router.post("/status/incidents", response_model=StatusIncidentResponse)
async def internal_create_incident(
    body: StatusIncidentCreate,
    admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> StatusIncidentResponse:
    row = PlatformStatusIncident(
        title=body.title,
        summary=body.summary,
        status=body.status,
        severity=body.severity,
        affected_components_json=body.affected_components,
        is_public=body.is_public,
        started_at=datetime.now(UTC),
    )
    db.add(row)
    await db.flush()
    await record_audit(
        db,
        action="internal.status_incident_created",
        target_type="status_incident",
        target_id=str(row.id),
        actor_user_id=admin.user_id,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/status/incidents/{incident_id}", response_model=StatusIncidentResponse)
async def internal_update_incident(
    incident_id: UUID,
    body: StatusIncidentUpdate,
    admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> StatusIncidentResponse:
    row = await db.get(PlatformStatusIncident, incident_id)
    if row is None:
        raise not_found("Status incident")
    if body.status is not None:
        row.status = body.status
    if body.summary is not None:
        row.summary = body.summary
    if body.severity is not None:
        row.severity = body.severity
    if body.is_public is not None:
        row.is_public = body.is_public
    if body.resolved:
        row.status = "resolved"
        row.resolved_at = datetime.now(UTC)
    await record_audit(
        db,
        action="internal.status_incident_updated",
        target_type="status_incident",
        target_id=str(incident_id),
        actor_user_id=admin.user_id,
    )
    await db.commit()
    await db.refresh(row)
    return row
