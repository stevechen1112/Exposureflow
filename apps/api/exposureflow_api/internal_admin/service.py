"""Platform-wide internal admin queries — no credential secrets exposed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.billing.quota import get_account_subscription, usage_summary
from exposureflow_api.common.errors import not_found
from exposureflow_api.internal_admin.schemas import (
    AccountOverview,
    ActivationRow,
    AuditLogOverview,
    IntegrationHealthRow,
    JobRunOverview,
    OnboardingFunnel,
    ProviderCostRow,
    SyncStateOverview,
    UserOverview,
    WorkspaceOverview,
)
from exposureflow_api.models import (
    Account,
    ActionDecision,
    AuditLog,
    ExposureOpportunity,
    IntegrationSyncState,
    JobRun,
    Report,
    Site,
    User,
    Workspace,
    WorkspaceMembership,
)


async def list_workspaces(db: AsyncSession, *, limit: int = 100) -> list[WorkspaceOverview]:
    ws_rows = await db.execute(
        select(Workspace).where(Workspace.status != "deleted").order_by(Workspace.created_at.desc()).limit(limit)
    )
    workspaces = list(ws_rows.scalars().all())
    out: list[WorkspaceOverview] = []
    for ws in workspaces:
        account = await db.get(Account, ws.account_id)
        member_count = int(
            (
                await db.execute(
                    select(func.count()).select_from(WorkspaceMembership).where(
                        WorkspaceMembership.workspace_id == ws.id,
                        WorkspaceMembership.status == "active",
                    )
                )
            ).scalar_one()
        )
        site_count = int(
            (await db.execute(select(func.count()).select_from(Site).where(Site.workspace_id == ws.id))).scalar_one()
        )
        sub_plan = await get_account_subscription(db, ws.account_id) if account else None
        out.append(
            WorkspaceOverview(
                id=ws.id,
                name=ws.name,
                account_id=ws.account_id,
                account_name=account.name if account else "",
                workspace_type=ws.workspace_type,
                status=ws.status,
                member_count=member_count,
                site_count=site_count,
                subscription_status=sub_plan[0].status if sub_plan else None,
                plan_code=sub_plan[1].plan_code if sub_plan else None,
                billing_status=account.billing_status if account else None,
                feature_flags=ws.feature_flags or {},
                created_at=ws.created_at,
            )
        )
    return out


async def list_accounts(db: AsyncSession, *, limit: int = 100) -> list[AccountOverview]:
    rows = await db.execute(select(Account).order_by(Account.created_at.desc()).limit(limit))
    out: list[AccountOverview] = []
    for account in rows.scalars().all():
        ws_count = int(
            (
                await db.execute(
                    select(func.count()).select_from(Workspace).where(
                        Workspace.account_id == account.id,
                        Workspace.status != "deleted",
                    )
                )
            ).scalar_one()
        )
        sub_plan = await get_account_subscription(db, account.id)
        out.append(
            AccountOverview(
                id=account.id,
                name=account.name,
                account_type=account.account_type,
                billing_status=account.billing_status,
                workspace_count=ws_count,
                subscription_status=sub_plan[0].status if sub_plan else None,
                plan_code=sub_plan[1].plan_code if sub_plan else None,
                created_at=account.created_at,
            )
        )
    return out


async def search_users(db: AsyncSession, *, email: str | None = None, limit: int = 50) -> list[UserOverview]:
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if email:
        stmt = select(User).where(User.email.ilike(f"%{email}%")).order_by(User.created_at.desc()).limit(limit)
    users = list((await db.execute(stmt)).scalars().all())
    out: list[UserOverview] = []
    for user in users:
        memberships = list(
            (
                await db.execute(
                    select(WorkspaceMembership, Workspace.name)
                    .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
                    .where(WorkspaceMembership.user_id == user.id)
                )
            ).all()
        )
        out.append(
            UserOverview(
                id=user.id,
                email=user.email,
                name=user.name,
                status=user.status,
                memberships=[
                    {"workspace_id": str(m.workspace_id), "workspace_name": name, "role": m.role, "status": m.status}
                    for m, name in memberships
                ],
                created_at=user.created_at,
            )
        )
    return out


async def list_job_runs(
    db: AsyncSession,
    *,
    workspace_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[JobRunOverview]:
    stmt = select(JobRun).order_by(JobRun.created_at.desc()).limit(limit)
    if workspace_id:
        stmt = stmt.where(JobRun.workspace_id == workspace_id)
    if status:
        stmt = stmt.where(JobRun.status == status)
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        JobRunOverview(
            id=r.id,
            workspace_id=r.workspace_id,
            site_id=r.site_id,
            job_type=r.job_type,
            status=r.status,
            provider=r.provider,
            provider_cost_cents=r.provider_cost_cents,
            error_code=r.error_code,
            error_message=r.error_message,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in rows
    ]


async def list_sync_states(
    db: AsyncSession,
    *,
    workspace_id: UUID | None = None,
    failing_only: bool = False,
    limit: int = 200,
) -> list[SyncStateOverview]:
    stmt = select(IntegrationSyncState).order_by(IntegrationSyncState.updated_at.desc()).limit(limit)
    if workspace_id:
        stmt = stmt.where(IntegrationSyncState.workspace_id == workspace_id)
    if failing_only:
        stmt = stmt.where(IntegrationSyncState.last_error.isnot(None))
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        SyncStateOverview(
            id=r.id,
            workspace_id=r.workspace_id,
            site_id=r.site_id,
            provider=r.provider,
            last_synced_at=r.last_synced_at,
            last_success_at=r.last_success_at,
            last_error=r.last_error,
        )
        for r in rows
    ]


async def list_audit_logs(
    db: AsyncSession,
    *,
    workspace_id: UUID | None = None,
    action_prefix: str | None = None,
    limit: int = 200,
) -> list[AuditLogOverview]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if workspace_id:
        stmt = stmt.where(AuditLog.workspace_id == workspace_id)
    if action_prefix:
        stmt = stmt.where(AuditLog.action.like(f"{action_prefix}%"))
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        AuditLogOverview(
            id=r.id,
            workspace_id=r.workspace_id,
            account_id=r.account_id,
            actor_user_id=r.actor_user_id,
            action=r.action,
            target_type=r.target_type,
            target_id=r.target_id,
            metadata_json=r.metadata_json or {},
            created_at=r.created_at,
        )
        for r in rows
    ]


async def update_feature_flags(db: AsyncSession, workspace_id: UUID, flags: dict) -> Workspace:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise not_found("Workspace")
    merged = dict(ws.feature_flags or {})
    merged.update(flags)
    ws.feature_flags = merged
    await db.flush()
    return ws


async def workspace_usage(db: AsyncSession, workspace_id: UUID) -> dict:
    return await usage_summary(db, workspace_id)


async def _workspace_milestones(db: AsyncSession, workspace_id: UUID) -> dict:
    site_count = int(
        (await db.execute(select(func.count()).select_from(Site).where(Site.workspace_id == workspace_id))).scalar_one()
    )
    gsc_sync = int(
        (
            await db.execute(
                select(func.count()).select_from(IntegrationSyncState).where(
                    IntegrationSyncState.workspace_id == workspace_id,
                    IntegrationSyncState.provider == "gsc",
                    IntegrationSyncState.last_success_at.isnot(None),
                )
            )
        ).scalar_one()
    )
    opp_count = int(
        (
            await db.execute(
                select(func.count()).select_from(ExposureOpportunity).where(
                    ExposureOpportunity.workspace_id == workspace_id
                )
            )
        ).scalar_one()
    )
    report_count = int(
        (
            await db.execute(
                select(func.count()).select_from(Report).where(
                    Report.workspace_id == workspace_id,
                    Report.status == "ready",
                )
            )
        ).scalar_one()
    )
    approved_decisions = int(
        (
            await db.execute(
                select(func.count()).select_from(ActionDecision).where(
                    ActionDecision.workspace_id == workspace_id,
                    ActionDecision.decision == "approved",
                )
            )
        ).scalar_one()
    )
    return {
        "has_site": site_count > 0,
        "first_gsc_sync": gsc_sync > 0,
        "first_opportunity": opp_count > 0,
        "first_report": report_count > 0,
        "first_approved_decision": approved_decisions > 0,
    }


def _activation_score(milestones: dict) -> int:
    weights = ["has_site", "first_gsc_sync", "first_opportunity", "first_report", "first_approved_decision"]
    return int(sum(20 for key in weights if milestones.get(key)))


def _churn_risk(score: int, last_activity: datetime | None) -> str:
    if score >= 80:
        return "low"
    if last_activity is None:
        return "high"
    if last_activity < datetime.now(UTC) - timedelta(days=14):
        return "high"
    if score < 40:
        return "high"
    return "medium"


async def activation_dashboard(db: AsyncSession, *, limit: int = 100) -> list[ActivationRow]:
    workspaces = list(
        (await db.execute(select(Workspace).where(Workspace.status == "active").limit(limit))).scalars().all()
    )
    rows: list[ActivationRow] = []
    for ws in workspaces:
        account = await db.get(Account, ws.account_id)
        milestones = await _workspace_milestones(db, ws.id)
        score = _activation_score(milestones)
        last_job = (
            await db.execute(
                select(JobRun.created_at)
                .where(JobRun.workspace_id == ws.id)
                .order_by(JobRun.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        rows.append(
            ActivationRow(
                workspace_id=ws.id,
                workspace_name=ws.name,
                account_name=account.name if account else "",
                activation_score=score,
                milestones=milestones,
                last_activity_at=last_job,
                churn_risk=_churn_risk(score, last_job),
            )
        )
    rows.sort(key=lambda r: (r.churn_risk != "high", r.activation_score))
    return rows


async def onboarding_funnel(db: AsyncSession) -> OnboardingFunnel:
    workspaces = list(
        (await db.execute(select(Workspace).where(Workspace.status == "active"))).scalars().all()
    )
    total = len(workspaces)
    counts = {"has_site": 0, "first_gsc_sync": 0, "first_opportunity": 0, "first_report": 0, "first_approved_decision": 0}
    fully = 0
    for ws in workspaces:
        m = await _workspace_milestones(db, ws.id)
        for key in counts:
            if m.get(key):
                counts[key] += 1
        if all(m.get(k) for k in counts):
            fully += 1
    return OnboardingFunnel(
        total_workspaces=total,
        has_site=counts["has_site"],
        first_gsc_sync=counts["first_gsc_sync"],
        first_opportunity=counts["first_opportunity"],
        first_report=counts["first_report"],
        first_approved_decision=counts["first_approved_decision"],
        fully_activated=fully,
    )


async def integration_health(db: AsyncSession) -> list[IntegrationHealthRow]:
    stale_before = datetime.now(UTC) - timedelta(days=3)
    rows = list((await db.execute(select(IntegrationSyncState))).scalars().all())
    by_provider: dict[str, IntegrationHealthRow] = {}
    for row in rows:
        bucket = by_provider.setdefault(
            row.provider,
            IntegrationHealthRow(provider=row.provider, total=0, healthy=0, failing=0, stale=0),
        )
        bucket.total += 1
        if row.last_error:
            bucket.failing += 1
        elif row.last_success_at and row.last_success_at >= stale_before:
            bucket.healthy += 1
        else:
            bucket.stale += 1
    return sorted(by_provider.values(), key=lambda r: r.provider)


async def provider_costs(db: AsyncSession, *, days: int = 30) -> list[ProviderCostRow]:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = list(
        (
            await db.execute(
                select(JobRun).where(JobRun.created_at >= since, JobRun.provider.isnot(None))
            )
        ).scalars().all()
    )
    by_provider: dict[str, ProviderCostRow] = {}
    for row in rows:
        provider = row.provider or "unknown"
        bucket = by_provider.setdefault(
            provider,
            ProviderCostRow(provider=provider, job_count=0, total_cost_cents=0, failed_jobs=0),
        )
        bucket.job_count += 1
        bucket.total_cost_cents += row.provider_cost_cents or 0
        if row.status == "failed":
            bucket.failed_jobs += 1
    return sorted(by_provider.values(), key=lambda r: -r.total_cost_cents)
