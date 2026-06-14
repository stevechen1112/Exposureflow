"""Monthly exposure report content builder."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.ai_visibility.dashboard import build_ai_visibility_dashboard
from exposureflow_api.decision.outcomes import list_action_outcomes
from exposureflow_api.exposure.dashboard import build_dashboard_metrics


async def build_monthly_exposure_markdown(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    period_start: date | None = None,
    period_end: date | None = None,
    branding: dict | None = None,
) -> str:
    end = period_end or date.today().replace(day=1) - timedelta(days=1)
    start = period_start or end.replace(day=1)
    brand = branding or {}
    org_name = brand.get("organization_name", "ExposureFlow")

    metrics = await build_dashboard_metrics(db, workspace_id, site_id)
    ai = await build_ai_visibility_dashboard(db, workspace_id, site_id)
    outcomes = await list_action_outcomes(db, workspace_id, site_id)

    lines = [
        f"# {org_name} — 自然曝光月報",
        "",
        f"**期間**：{start.isoformat()} — {end.isoformat()}",
        "",
        "## Executive Summary",
        "",
        f"本期自然曝光 **{metrics['total_impressions']:,}**（MoM {metrics['impressions_delta_pct']:+.1f}%）。",
        f"Open 機會 {metrics['open_opportunity_count']} 項；Critical 技術阻擋 {metrics['critical_blocker_count']} 項。",
        "",
        "## 自然曝光 KPI",
        "",
        f"- Query coverage：{metrics['query_coverage_count']}",
        f"- Indexed assets：{metrics['indexed_asset_count']}",
        f"- Top 3 / 10 / 20：{metrics['top_3_count']} / {metrics['top_10_count']} / {metrics['top_20_count']}",
        f"- SERP slot 達成：{metrics['serp_slot_count']}",
        "",
        "## Topic Cluster 表現",
        "",
    ]
    if metrics["topic_cluster_performance"]:
        for row in metrics["topic_cluster_performance"]:
            lines.append(
                f"- **{row['name']}**：曝光 {row['total_impressions']:,}；"
                f"覆蓋 {row['coverage_score']:.1f}；AI {row['ai_visibility_score']:.1f}"
            )
    else:
        lines.append("- （尚無 cluster 資料）")

    lines.extend(
        [
            "",
            "## AI 能見度",
            "",
            f"- Citations：{ai['citation_count']}",
            f"- 品牌提及：{ai['brand_mention_count']}",
            f"- 競品提及：{ai['competitor_mention_count']}",
            "",
            "## 行動成果",
            "",
        ]
    )
    if outcomes:
        for o in outcomes[:10]:
            lines.append(
                f"- {o.get('action_type')} / {o.get('keyword') or '—'}："
                f"roadmap {o.get('roadmap_status')}"
            )
    else:
        lines.append("- （尚無已追蹤成果）")

    lines.extend(
        [
            "",
            "## 下月 Roadmap 建議",
            "",
            "- 優先處理 high/critical 機會佇列項目",
            "- 延續 SERP 版位缺口與 AI citation 提升行動",
            "",
        ]
    )
    return "\n".join(lines)
