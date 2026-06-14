"""Additional report generators for consultant delivery modes."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.decision import service as decision_service
from exposureflow_api.decision.outcomes import list_action_outcomes
from exposureflow_api.exposure.dashboard import build_dashboard_metrics
from exposureflow_api.models import TechnicalIssue
from exposureflow_api.reporting.monthly_report import build_monthly_exposure_markdown


async def build_audit_report_markdown(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    branding: dict | None = None,
) -> str:
    brand = branding or {}
    org = brand.get("organization_name", "ExposureFlow")
    metrics = await build_dashboard_metrics(db, workspace_id, site_id)
    issues = await db.execute(
        select(TechnicalIssue).where(
            TechnicalIssue.workspace_id == workspace_id,
            TechnicalIssue.site_id == site_id,
            TechnicalIssue.status == "open",
        ).limit(20)
    )
    issue_rows = list(issues.scalars().all())
    lines = [
        f"# {org} — SEO / 曝光 Audit",
        "",
        "## 現況摘要",
        "",
        f"- 28 天自然曝光：{metrics['total_impressions']:,}",
        f"- Query coverage：{metrics['query_coverage_count']}",
        f"- Critical 技術問題：{metrics['critical_blocker_count']}",
        f"- Open 機會：{metrics['open_opportunity_count']}",
        "",
        "## 技術問題（Open）",
        "",
    ]
    if issue_rows:
        for row in issue_rows:
            lines.append(f"- **{row.severity}** {row.issue_type} — {row.url or 'site-wide'}")
    else:
        lines.append("- 無 open 技術問題")
    lines.extend(["", "## 建議優先序", "", "1. 修復 critical/high 技術阻擋", "2. 處理 high score 機會", ""])
    return "\n".join(lines)


async def build_roadmap_report_markdown(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    branding: dict | None = None,
) -> str:
    brand = branding or {}
    org = brand.get("organization_name", "ExposureFlow")
    roadmaps = await decision_service.list_roadmaps(db, workspace_id, site_id)
    lines = [f"# {org} — Exposure Roadmap", ""]
    if not roadmaps:
        lines.append("尚無 roadmap，請先從 Decision Plane 建立。")
        return "\n".join(lines)
    for rm in roadmaps[:1]:
        _rm, items = await decision_service.get_roadmap_with_items(db, workspace_id, rm.id)
        lines.append(f"## {rm.title}（{rm.horizon_weeks} 週）")
        lines.append("")
        for item in items:
            lines.append(
                f"- W{item.week_number} · {item.title} — {item.status} "
                f"(client: {item.client_approval_status})"
            )
    return "\n".join(lines)


async def build_execution_tracker_markdown(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    branding: dict | None = None,
) -> str:
    brand = branding or {}
    org = brand.get("organization_name", "ExposureFlow")
    outcomes = await list_action_outcomes(db, workspace_id, site_id)
    lines = [f"# {org} — Execution Tracker", "", "## 已完成 / 進行中成果", ""]
    if not outcomes:
        lines.append("- 尚無已 approve 行動成果")
    else:
        for o in outcomes:
            lines.append(
                f"- {o.get('action_type')} · {o.get('keyword') or '—'} · "
                f"roadmap {o.get('roadmap_status')}"
            )
    return "\n".join(lines)


DELIVERY_BUILDERS = {
    "monthly_retainer": build_monthly_exposure_markdown,
    "audit": build_audit_report_markdown,
    "roadmap": build_roadmap_report_markdown,
    "execution_tracker": build_execution_tracker_markdown,
}

REPORT_TYPE_BY_MODE = {
    "monthly_retainer": "monthly_exposure",
    "audit": "audit",
    "roadmap": "roadmap",
    "execution_tracker": "client_summary",
}
