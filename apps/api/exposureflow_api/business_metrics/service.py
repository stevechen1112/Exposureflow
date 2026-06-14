"""Business operations metrics (EF-1403)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.billing.quota import get_account_subscription
from exposureflow_api.internal_admin.service import _activation_score, _workspace_milestones, onboarding_funnel
from exposureflow_api.models import (
    ActionCandidate,
    ActionDecision,
    JobRun,
    Report,
    Subscription,
    Workspace,
)
from exposureflow_api.models.commercial import Plan


async def compute_business_metrics(db: AsyncSession, *, days: int = 30) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    workspaces = list(
        (await db.execute(select(Workspace).where(Workspace.status == "active"))).scalars().all()
    )
    total_ws = len(workspaces)

    funnel = await onboarding_funnel(db)
    activation_rate = round(funnel.fully_activated / funnel.total_workspaces, 4) if funnel.total_workspaces else 0.0
    gsc_sync_rate = round(funnel.first_gsc_sync / funnel.total_workspaces, 4) if funnel.total_workspaces else 0.0

    approved = int(
        (
            await db.execute(
                select(func.count()).select_from(ActionDecision).where(ActionDecision.decision == "approved")
            )
        ).scalar_one()
    )
    candidates = int((await db.execute(select(func.count()).select_from(ActionCandidate))).scalar_one())
    opportunity_approved_rate = round(approved / candidates, 4) if candidates else 0.0

    ws_with_reports = int(
        (
            await db.execute(
                select(func.count(func.distinct(Report.workspace_id))).where(Report.status == "ready")
            )
        ).scalar_one()
    )
    report_generated_rate = round(ws_with_reports / total_ws, 4) if total_ws else 0.0

    active_ws_ids = set(
        (
            await db.execute(
                select(JobRun.workspace_id).where(JobRun.created_at >= since).distinct()
            )
        ).scalars().all()
    )
    monthly_active_workspaces = len(active_ws_ids)

    prev_active = set(
        (
            await db.execute(
                select(JobRun.workspace_id).where(
                    JobRun.created_at >= prev_since,
                    JobRun.created_at < since,
                ).distinct()
            )
        ).scalars().all()
    )
    retained = len(active_ws_ids & prev_active) if prev_active else 0
    retention_rate = round(retained / len(prev_active), 4) if prev_active else None

    # Provider cost per workspace
    cost_rows = list(
        (await db.execute(select(JobRun).where(JobRun.created_at >= since, JobRun.provider.isnot(None)))).scalars().all()
    )
    total_cost = sum(r.provider_cost_cents or 0 for r in cost_rows)
    provider_cost_per_workspace = round(total_cost / total_ws, 2) if total_ws else 0.0

    # Gross margin by plan (simplified: MRR - estimated provider cost allocation)
    plan_metrics: list[dict] = []
    plans = list((await db.execute(select(Plan).where(Plan.active.is_(True)))).scalars().all())
    for plan in plans:
        subs = list(
            (
                await db.execute(
                    select(Subscription).where(Subscription.plan_id == plan.id, Subscription.status == "active")
                )
            ).scalars().all()
        )
        mrr_cents = len(subs) * plan.price_monthly_cents
        ws_for_plan = 0
        for sub in subs:
            ws_count = int(
                (
                    await db.execute(
                        select(func.count()).select_from(Workspace).where(
                            Workspace.account_id == sub.account_id,
                            Workspace.status == "active",
                        )
                    )
                ).scalar_one()
            )
            ws_for_plan += ws_count
        allocated_cost = provider_cost_per_workspace * ws_for_plan if ws_for_plan else 0
        gross_margin_cents = mrr_cents - int(allocated_cost)
        plan_metrics.append(
            {
                "plan_code": plan.plan_code,
                "active_subscriptions": len(subs),
                "mrr_cents": mrr_cents,
                "estimated_provider_cost_cents": int(allocated_cost),
                "gross_margin_cents": gross_margin_cents,
            }
        )

    # Expansion revenue proxy: accounts with custom_limits or multiple workspaces
    expansion_accounts = 0
    for ws in workspaces:
        sub_plan = await get_account_subscription(db, ws.account_id)
        if sub_plan and sub_plan[0].custom_limits_json:
            expansion_accounts += 1
    expansion_revenue_proxy = expansion_accounts

    # Activation score distribution
    scores: list[int] = []
    for ws in workspaces[:200]:
        milestones = await _workspace_milestones(db, ws.id)
        scores.append(_activation_score(milestones))
    avg_activation_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    return {
        "period_days": days,
        "computed_at": datetime.now(UTC).isoformat(),
        "product_activation_rate": activation_rate,
        "workspace_gsc_sync_rate": gsc_sync_rate,
        "opportunity_approved_rate": opportunity_approved_rate,
        "report_generated_rate": report_generated_rate,
        "monthly_active_workspaces": monthly_active_workspaces,
        "retention_rate": retention_rate,
        "expansion_revenue_accounts": expansion_revenue_proxy,
        "provider_cost_per_workspace_cents": provider_cost_per_workspace,
        "average_activation_score": avg_activation_score,
        "gross_margin_by_plan": plan_metrics,
        "funnel": funnel.model_dump(),
    }
