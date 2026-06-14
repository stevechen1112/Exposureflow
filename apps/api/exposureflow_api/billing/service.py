"""Billing service — plans seed, subscriptions, workspace transfer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.billing.plans import PLAN_DEFINITIONS
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.models.commercial import Plan, Subscription, WorkspaceBranding, WorkspaceTransfer
from exposureflow_api.models.tenant import Account, Organization, Workspace, WorkspaceMembership


async def seed_plans(db: AsyncSession) -> None:
    for spec in PLAN_DEFINITIONS:
        existing = await db.execute(select(Plan).where(Plan.plan_code == spec["plan_code"]))
        if existing.scalar_one_or_none() is not None:
            continue
        db.add(
            Plan(
                name=spec["name"],
                plan_code=spec["plan_code"],
                limits_json=spec["limits_json"],
                price_monthly_cents=spec["price_monthly_cents"],
                price_yearly_cents=spec["price_yearly_cents"],
                active=True,
            )
        )
    await db.flush()


async def get_plan_by_code(db: AsyncSession, plan_code: str) -> Plan | None:
    result = await db.execute(select(Plan).where(Plan.plan_code == plan_code, Plan.active.is_(True)))
    return result.scalar_one_or_none()


async def ensure_starter_subscription(db: AsyncSession, account_id: UUID) -> Subscription:
    existing = await db.execute(
        select(Subscription).where(Subscription.account_id == account_id).limit(1)
    )
    sub = existing.scalar_one_or_none()
    if sub:
        return sub
    plan = await get_plan_by_code(db, "starter")
    if plan is None:
        await seed_plans(db)
        plan = await get_plan_by_code(db, "starter")
    if plan is None:
        raise APIError(code="PLAN_MISSING", message="Starter plan not configured.", status_code=500)
    now = datetime.now(UTC)
    sub = Subscription(
        account_id=account_id,
        plan_id=plan.id,
        status="trialing",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        trial_end=now + timedelta(days=14),
    )
    db.add(sub)
    await db.flush()
    return sub


async def get_subscription_for_account(
    db: AsyncSession, account_id: UUID
) -> tuple[Subscription, Plan] | None:
    result = await db.execute(
        select(Subscription, Plan)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.account_id == account_id)
        .order_by(Subscription.updated_at.desc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    return row[0], row[1]


async def update_subscription_from_stripe(
    db: AsyncSession,
    account_id: UUID,
    *,
    stripe_subscription_id: str | None,
    status: str,
    plan_code: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> Subscription:
    sub_plan = await get_subscription_for_account(db, account_id)
    if sub_plan is None:
        await ensure_starter_subscription(db, account_id)
        sub_plan = await get_subscription_for_account(db, account_id)
        assert sub_plan is not None
    subscription, _plan = sub_plan
    subscription.stripe_subscription_id = stripe_subscription_id
    subscription.status = status
    if period_start:
        subscription.current_period_start = period_start
    if period_end:
        subscription.current_period_end = period_end
    if plan_code:
        plan = await get_plan_by_code(db, plan_code)
        if plan:
            subscription.plan_id = plan.id
    account = await db.get(Account, account_id)
    if account:
        account.billing_status = "active" if status in {"active", "trialing"} else status
    await db.flush()
    return subscription


async def transfer_workspace(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    to_account_id: UUID,
    to_organization_id: UUID,
    initiated_by: UUID,
) -> Workspace:
    workspace = await db.get(Workspace, workspace_id)
    if workspace is None:
        raise not_found("Workspace")
    to_org = await db.get(Organization, to_organization_id)
    if to_org is None or to_org.account_id != to_account_id:
        raise APIError(code="INVALID_TRANSFER", message="Target organization invalid.", status_code=400)
    from_account_id = workspace.account_id
    workspace.account_id = to_account_id
    workspace.organization_id = to_organization_id
    await db.execute(
        update(WorkspaceMembership)
        .where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.status == "active",
        )
        .values(status="revoked")
    )
    transfer = WorkspaceTransfer(
        workspace_id=workspace_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        to_organization_id=to_organization_id,
        initiated_by=initiated_by,
        status="completed",
    )
    db.add(transfer)
    await record_audit(
        db,
        action="workspace.transfer",
        target_type="workspace",
        target_id=str(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=initiated_by,
        metadata={
            "from_account_id": str(from_account_id),
            "to_account_id": str(to_account_id),
        },
    )
    await db.flush()
    return workspace


async def upsert_workspace_branding(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    organization_name: str,
    logo_url: str | None = None,
    primary_color: str | None = None,
    custom_domain: str | None = None,
    report_footer: str | None = None,
) -> WorkspaceBranding:
    result = await db.execute(
        select(WorkspaceBranding).where(WorkspaceBranding.workspace_id == workspace_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = WorkspaceBranding(
            workspace_id=workspace_id,
            organization_name=organization_name,
            logo_url=logo_url,
            primary_color=primary_color,
            custom_domain=custom_domain,
            report_footer=report_footer,
        )
        db.add(row)
    else:
        row.organization_name = organization_name
        row.logo_url = logo_url
        row.primary_color = primary_color
        row.custom_domain = custom_domain
        row.report_footer = report_footer
    await db.flush()
    return row
