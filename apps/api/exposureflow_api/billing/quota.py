"""Quota enforcement from subscription plan limits."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.billing.plans import METRIC_TO_LIMIT_KEY
from exposureflow_api.common.errors import APIError
from exposureflow_api.models.commercial import Plan, Subscription, UsageEvent
from exposureflow_api.models.tenant import Account, Site, Workspace, WorkspaceMembership


async def assert_billing_active(db: AsyncSession, account_id: UUID) -> None:
    account = await db.get(Account, account_id)
    if account and account.billing_status in {"past_due", "canceled", "unpaid"}:
        raise APIError(
            code="BILLING_INACTIVE",
            message="Account billing is inactive; upgrade or update payment method.",
            status_code=402,
        )


async def get_account_subscription(
    db: AsyncSession, account_id: UUID
) -> tuple[Subscription, Plan] | None:
    result = await db.execute(
        select(Subscription, Plan)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.account_id == account_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    return row[0], row[1]


async def get_effective_limits(db: AsyncSession, account_id: UUID) -> dict:
    sub_plan = await get_account_subscription(db, account_id)
    if sub_plan is None:
        from exposureflow_api.billing.plans import PLAN_DEFINITIONS

        return dict(PLAN_DEFINITIONS[0]["limits_json"])
    subscription, plan = sub_plan
    limits = dict(plan.limits_json or {})
    if subscription.custom_limits_json:
        limits.update(subscription.custom_limits_json)
    return limits


async def count_monthly_usage(
    db: AsyncSession,
    workspace_id: UUID,
    metric: str,
) -> int:
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.coalesce(func.sum(UsageEvent.quantity), 0)).where(
            UsageEvent.workspace_id == workspace_id,
            UsageEvent.metric == metric,
            UsageEvent.created_at >= month_start,
        )
    )
    return int(result.scalar_one())


async def get_metric_limit(db: AsyncSession, account_id: UUID, metric: str) -> int:
    limits = await get_effective_limits(db, account_id)
    key = METRIC_TO_LIMIT_KEY.get(metric, metric)
    value = limits.get(key)
    if value is None:
        return 10_000
    if isinstance(value, bool):
        return 1 if value else 0
    return int(value)


async def check_quota(
    db: AsyncSession,
    workspace_id: UUID,
    metric: str,
    *,
    quantity: int = 1,
) -> None:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise APIError(code="NOT_FOUND", message="Workspace not found.", status_code=404)
    await assert_billing_active(db, ws.account_id)
    limit = await get_metric_limit(db, ws.account_id, metric)
    used = await count_monthly_usage(db, workspace_id, metric)
    if used + quantity > limit:
        raise APIError(
            code="QUOTA_EXCEEDED",
            message=f"Monthly quota exceeded for {metric}.",
            status_code=429,
            details={"metric": metric, "used": used, "limit": limit},
        )


async def check_workspace_limit(db: AsyncSession, account_id: UUID) -> None:
    await assert_billing_active(db, account_id)
    limits = await get_effective_limits(db, account_id)
    cap = int(limits.get("workspace_limit", 1))
    result = await db.execute(
        select(func.count()).select_from(Workspace).where(
            Workspace.account_id == account_id,
            Workspace.status != "deleted",
        )
    )
    count = int(result.scalar_one())
    if count >= cap:
        raise APIError(
            code="WORKSPACE_LIMIT",
            message="Workspace limit reached for current plan.",
            status_code=429,
            details={"used": count, "limit": cap},
        )


async def check_site_limit(db: AsyncSession, workspace_id: UUID) -> None:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        return
    await assert_billing_active(db, ws.account_id)
    limits = await get_effective_limits(db, ws.account_id)
    cap = int(limits.get("site_limit", 1))
    result = await db.execute(
        select(func.count()).select_from(Site).where(
            Site.workspace_id == workspace_id,
            Site.status != "deleted",
        )
    )
    count = int(result.scalar_one())
    if count >= cap:
        raise APIError(
            code="SITE_LIMIT",
            message="Site limit reached for current plan.",
            status_code=429,
            details={"used": count, "limit": cap},
        )


async def check_member_limit(db: AsyncSession, workspace_id: UUID) -> None:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        return
    await assert_billing_active(db, ws.account_id)
    limits = await get_effective_limits(db, ws.account_id)
    cap = int(limits.get("user_limit", 3))
    result = await db.execute(
        select(func.count(func.distinct(WorkspaceMembership.user_id)))
        .select_from(WorkspaceMembership)
        .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
        .where(
            Workspace.account_id == ws.account_id,
            WorkspaceMembership.status == "active",
        )
    )
    count = int(result.scalar_one())
    if count >= cap:
        raise APIError(
            code="USER_LIMIT",
            message="User limit reached for current plan.",
            status_code=429,
            details={"used": count, "limit": cap},
        )


async def usage_summary(db: AsyncSession, workspace_id: UUID) -> dict:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise APIError(code="NOT_FOUND", message="Workspace not found.", status_code=404)
    limits = await get_effective_limits(db, ws.account_id)
    metrics = list(METRIC_TO_LIMIT_KEY.keys())
    usage: dict[str, dict] = {}
    for metric in metrics:
        key = METRIC_TO_LIMIT_KEY[metric]
        limit = limits.get(key, 0)
        used = await count_monthly_usage(db, workspace_id, metric)
        usage[metric] = {"used": used, "limit": int(limit) if limit is not None else 0}
    return {"workspace_id": str(workspace_id), "metrics": usage, "limits": limits}
