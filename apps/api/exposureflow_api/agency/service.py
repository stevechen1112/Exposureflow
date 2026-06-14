"""Agency master dashboard — client workspace summaries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.billing.quota import count_monthly_usage, get_effective_limits
from exposureflow_api.exposure.dashboard import build_dashboard_metrics
from exposureflow_api.models import Site, Workspace
from exposureflow_api.models.reporting import Report


async def build_agency_dashboard(db: AsyncSession, account_id: UUID) -> dict:
    workspaces = await db.execute(
        select(Workspace).where(
            Workspace.account_id == account_id,
            Workspace.status == "active",
        )
    )
    ws_list = list(workspaces.scalars().all())
    limits = await get_effective_limits(db, account_id)
    clients: list[dict] = []

    for ws in ws_list:
        if ws.workspace_type == "agency_internal":
            continue
        sites = await db.execute(select(Site).where(Site.workspace_id == ws.id).limit(1))
        site = sites.scalar_one_or_none()
        exposure = None
        if site:
            exposure = await build_dashboard_metrics(db, ws.id, site.id)
        report_count = await db.execute(
            select(func.count()).select_from(Report).where(
                Report.workspace_id == ws.id,
                Report.status == "ready",
            )
        )
        serp_used = await count_monthly_usage(db, ws.id, "serp_snapshots")
        clients.append(
            {
                "workspace_id": str(ws.id),
                "name": ws.name,
                "client_name": ws.client_name,
                "workspace_type": ws.workspace_type,
                "total_impressions": exposure["total_impressions"] if exposure else 0,
                "impressions_delta_pct": exposure["impressions_delta_pct"] if exposure else 0,
                "open_opportunities": exposure["open_opportunity_count"] if exposure else 0,
                "ready_reports": int(report_count.scalar_one()),
                "serp_snapshots_used": serp_used,
            }
        )

    return {
        "account_id": str(account_id),
        "workspace_count": len(ws_list),
        "client_workspaces": clients,
        "plan_limits": limits,
    }
