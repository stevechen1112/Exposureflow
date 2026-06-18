"""Consultant work queue — unified actionable items across sites."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.consultant import action_hints
from exposureflow_api.consultant.schemas import (
    ConsultantInboxItem,
    ConsultantInboxResponse,
    ConsultantInboxSite,
    ConsultantInboxSummary,
    ConsultantInboxWorkspace,
)
from exposureflow_api.models import (
    ExposureOpportunity,
    IntegrationSyncState,
    Site,
    TechnicalIssue,
)
from exposureflow_api.models.decision import ActionCandidate, RoadmapItem
from exposureflow_api.models.execution_content import ContentGenerationRun
from exposureflow_api.models.strategy import KeywordPyramidNode
from exposureflow_api.models.topic import TopicNode
from exposureflow_api.consultant.workspace_scope import list_client_workspaces_for_account

_URGENT_CATEGORIES = frozenset({"technical", "content", "sync", "indexability", "decision"})
_GSC_SITEMAP_PREFIX = "gsc_sitemap_"
_CONTENT_REVIEW_STATUSES = ("needs_review", "needs_changes", "claim_verified", "claim_blocked", "draft")

_ROOT_CAUSE_LABELS = {
    "localhost_urls": "Sitemap 含 localhost — 請修正目標站 base URL",
    "wrong_domain": "Sitemap 網域錯誤 — 請檢查站點 URL 設定",
    "content_ok_gsc_stale": "Live sitemap 正常，GSC 可能尚未重抓",
    "fetch_failed": "無法抓取 sitemap — 請確認公開可連線",
    "xml_invalid_or_empty": "Sitemap XML 無效或為空",
    "unsafe_url": "Sitemap URL 與站點網域不符",
}

_GSC_ISSUE_TITLES = {
    "gsc_sitemap_unreachable": "GSC Sitemap 無法抓取",
    "gsc_sitemap_missing": "GSC 未提交 Sitemap",
    "gsc_sitemap_api_error": "GSC Sitemap API 錯誤",
}


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _bucket_item(item: ConsultantInboxItem) -> str:
    """Urgent = blocking now; in_progress = active work; monitoring = strategy backlog."""
    if item.priority in {"critical", "high"} and item.category in _URGENT_CATEGORIES:
        return "urgent"
    if item.category == "roadmap" and item.priority == "high":
        return "in_progress"
    return "monitoring"


def _site_path(workspace_id: UUID, site_id: UUID, subpath: str) -> str:
    return f"/app/{workspace_id}/sites/{site_id}/{subpath}"


def _root_cause_summary(evidence: dict | None, recommended_action: str | None) -> str | None:
    diagnosis = (evidence or {}).get("live_diagnosis") or {}
    root_cause = diagnosis.get("root_cause") or (evidence or {}).get("root_cause")
    if root_cause:
        return _ROOT_CAUSE_LABELS.get(root_cause, recommended_action)
    return recommended_action


async def build_consultant_inbox(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    site_id: UUID | None = None,
) -> ConsultantInboxResponse:
    stmt = select(Site).where(Site.workspace_id == workspace_id).order_by(Site.site_name)
    if site_id:
        stmt = stmt.where(Site.id == site_id)
    sites = list((await db.execute(stmt)).scalars().all())

    items: list[ConsultantInboxItem] = []
    sites_with_gsc_tech: set[UUID] = set()

    for site in sites:
        ws = workspace_id
        sid = site.id

        tech_result = await db.execute(
            select(TechnicalIssue)
            .where(
                TechnicalIssue.workspace_id == ws,
                TechnicalIssue.site_id == sid,
                TechnicalIssue.status == "open",
            )
            .order_by(TechnicalIssue.last_seen_at.desc())
        )
        for issue in tech_result.scalars().all():
            if issue.issue_type.startswith(_GSC_SITEMAP_PREFIX):
                sites_with_gsc_tech.add(sid)
            evidence_summary = _root_cause_summary(issue.evidence_json, issue.recommended_action)
            title = _GSC_ISSUE_TITLES.get(issue.issue_type, f"技術問題：{issue.issue_type}")
            items.append(
                ConsultantInboxItem(
                    id=f"tech-{issue.id}",
                    category="technical",
                    priority="critical" if issue.severity == "critical" else "high",
                    title=title,
                    detail=issue.description,
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "technical-issues"),
                    source_type="technical_issue",
                    source_id=str(issue.id),
                    created_at=_iso(issue.first_seen_at),
                    evidence_summary=evidence_summary,
                    action_hint=action_hints.hint_for_technical(
                        issue.issue_type, issue.recommended_action, evidence_summary
                    ),
                )
            )

        cand_result = await db.execute(
            select(ActionCandidate)
            .where(
                ActionCandidate.workspace_id == ws,
                ActionCandidate.site_id == sid,
                ActionCandidate.decision_status == "pending",
            )
            .order_by(ActionCandidate.rank_score.desc())
            .limit(20)
        )
        for cand in cand_result.scalars().all():
            ev_rule = (cand.evidence_json or {}).get("rule_id", "")
            if sid in sites_with_gsc_tech and cand.action_type == "fix_indexability" and str(ev_rule).startswith("OG-SITEMAP"):
                continue
            items.append(
                ConsultantInboxItem(
                    id=f"cand-{cand.id}",
                    category="decision",
                    priority="critical" if cand.risk_level == "high" else "high",
                    title=f"待決策：{cand.action_type}",
                    detail="機會佇列有待核准行動",
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "opportunities"),
                    source_type="action_candidate",
                    source_id=str(cand.id),
                    created_at=_iso(cand.created_at),
                    action_hint=action_hints.hint_for_decision(cand.action_type),
                )
            )

        gen_result = await db.execute(
            select(ContentGenerationRun)
            .where(
                ContentGenerationRun.workspace_id == ws,
                ContentGenerationRun.site_id == sid,
                ContentGenerationRun.status.in_(_CONTENT_REVIEW_STATUSES),
            )
            .order_by(ContentGenerationRun.updated_at.desc())
            .limit(20)
        )
        for run in gen_result.scalars().all():
            status_labels = {
                "needs_review": ("待審核內容", "critical"),
                "needs_changes": ("內容需修改", "high"),
                "claim_verified": ("Claims 已驗證，待審核發布", "high"),
                "claim_blocked": ("Claims 未通過，需修改", "high"),
                "draft": ("草稿待處理", "medium"),
            }
            title, priority = status_labels.get(run.status, (f"內容：{run.status}", "medium"))
            items.append(
                ConsultantInboxItem(
                    id=f"gen-{run.id}",
                    category="content",
                    priority=priority,
                    title=title,
                    detail=f"{run.generation_mode} · {run.status}",
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "content-review"),
                    source_type="generation_run",
                    source_id=str(run.id),
                    created_at=_iso(run.updated_at),
                    action_hint=action_hints.hint_for_content(run.status),
                )
            )

        kw_result = await db.execute(
            select(KeywordPyramidNode)
            .where(
                KeywordPyramidNode.workspace_id == ws,
                KeywordPyramidNode.site_id == sid,
                KeywordPyramidNode.business_fit_status == "in_scope",
                KeywordPyramidNode.approved_at.is_(None),
            )
            .order_by(KeywordPyramidNode.priority)
            .limit(10)
        )
        for node in kw_result.scalars().all():
            items.append(
                ConsultantInboxItem(
                    id=f"kw-{node.id}",
                    category="strategy",
                    priority="medium",
                    title=f"待核准關鍵字：{node.keyword}",
                    detail=f"{node.node_type} · 關鍵字金字塔",
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "keyword-pyramid"),
                    source_type="keyword_pyramid",
                    source_id=str(node.id),
                    created_at=_iso(node.created_at),
                    action_hint=action_hints.hint_for_keyword_pyramid(node.keyword, node.node_type),
                )
            )

        gap_result = await db.execute(
            select(TopicNode)
            .where(
                TopicNode.workspace_id == ws,
                TopicNode.site_id == sid,
                TopicNode.status == "gap",
                TopicNode.impressions > 0,
            )
            .order_by(TopicNode.impressions.desc())
            .limit(5)
        )
        for node in gap_result.scalars().all():
            items.append(
                ConsultantInboxItem(
                    id=f"gap-{node.id}",
                    category="strategy",
                    priority="medium",
                    title=f"覆蓋缺口：{node.keyword}",
                    detail="Topic Cluster 尚未覆蓋",
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "exposure-map"),
                    source_type="topic_gap",
                    source_id=str(node.id),
                    created_at=_iso(node.created_at),
                    action_hint=action_hints.hint_for_topic_gap(node.keyword, int(node.impressions or 0)),
                )
            )

        opp_result = await db.execute(
            select(ExposureOpportunity)
            .where(
                ExposureOpportunity.workspace_id == ws,
                ExposureOpportunity.site_id == sid,
                ExposureOpportunity.status == "open",
                ExposureOpportunity.opportunity_type.in_(["fix_indexability", "technical_fix"]),
            )
            .order_by(ExposureOpportunity.total_opportunity_score.desc())
            .limit(10)
        )
        for opp in opp_result.scalars().all():
            rule_id = (opp.evidence_json or {}).get("rule_id", "")
            if sid in sites_with_gsc_tech and str(rule_id).startswith("OG-SITEMAP"):
                continue
            ev_summary = _root_cause_summary(opp.evidence_json, None)
            items.append(
                ConsultantInboxItem(
                    id=f"opp-{opp.id}",
                    category="indexability",
                    priority=opp.priority if opp.priority in {"critical", "high"} else "high",
                    title=f"索引修復：{rule_id or opp.opportunity_type}",
                    detail=opp.reason,
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "opportunities"),
                    source_type="exposure_opportunity",
                    source_id=str(opp.id),
                    created_at=_iso(opp.created_at),
                    evidence_summary=ev_summary,
                    action_hint=action_hints.hint_for_indexability(str(rule_id), ev_summary),
                )
            )

        sync_result = await db.execute(
            select(IntegrationSyncState)
            .where(
                IntegrationSyncState.workspace_id == ws,
                IntegrationSyncState.site_id == sid,
                IntegrationSyncState.last_error.isnot(None),
            )
        )
        for sync in sync_result.scalars().all():
            items.append(
                ConsultantInboxItem(
                    id=f"sync-{sync.provider}-{sid}",
                    category="sync",
                    priority="critical",
                    title=f"同步失敗：{sync.provider}",
                    detail=sync.last_error or "Integration sync error",
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=f"/app/{ws}/settings/integrations",
                    source_type="sync_state",
                    source_id=f"{sync.provider}:{sid}",
                    created_at=_iso(sync.last_synced_at),
                    action_hint=action_hints.hint_for_sync(sync.provider),
                )
            )

        roadmap_result = await db.execute(
            select(RoadmapItem)
            .where(
                RoadmapItem.workspace_id == ws,
                RoadmapItem.site_id == sid,
                RoadmapItem.status.in_(["in_progress", "active", "planned"]),
            )
            .order_by(RoadmapItem.due_date.asc().nullslast())
            .limit(10)
        )
        for item in roadmap_result.scalars().all():
            items.append(
                ConsultantInboxItem(
                    id=f"roadmap-{item.id}",
                    category="roadmap",
                    priority="medium" if item.status == "planned" else "high",
                    title=f"路線圖：{item.title}",
                    detail=f"第 {item.week_number} 週 · {item.status}",
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "roadmap"),
                    source_type="roadmap_item",
                    source_id=str(item.id),
                    created_at=_iso(item.created_at),
                    action_hint=action_hints.hint_for_roadmap(
                        item.title, item.status, item.week_number
                    ),
                )
            )

        open_opp_result = await db.execute(
            select(ExposureOpportunity)
            .where(
                ExposureOpportunity.workspace_id == ws,
                ExposureOpportunity.site_id == sid,
                ExposureOpportunity.status == "open",
                ExposureOpportunity.opportunity_type.notin_(["fix_indexability", "technical_fix"]),
            )
            .order_by(ExposureOpportunity.total_opportunity_score.desc())
            .limit(5)
        )
        for opp in open_opp_result.scalars().all():
            label = opp.keyword or opp.opportunity_type
            items.append(
                ConsultantInboxItem(
                    id=f"open-{opp.id}",
                    category="opportunity",
                    priority="medium",
                    title=f"開放機會：{label}",
                    detail=opp.reason[:120] if opp.reason else opp.opportunity_type,
                    site_id=str(sid),
                    site_name=site.site_name,
                    site_domain=site.domain,
                    action_path=_site_path(ws, sid, "opportunities"),
                    source_type="exposure_opportunity",
                    source_id=str(opp.id),
                    created_at=_iso(opp.created_at),
                    action_hint=action_hints.hint_for_open_opportunity(label),
                )
            )

    urgent: list[ConsultantInboxItem] = []
    in_progress: list[ConsultantInboxItem] = []
    monitoring: list[ConsultantInboxItem] = []

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda i: (priority_order.get(i.priority, 9), i.created_at or ""))

    for item in items:
        bucket = _bucket_item(item)
        if bucket == "urgent":
            urgent.append(item)
        elif bucket == "in_progress":
            in_progress.append(item)
        else:
            monitoring.append(item)

    summary = ConsultantInboxSummary(
        urgent=len(urgent),
        in_progress=len(in_progress),
        monitoring=len(monitoring),
        total=len(items),
    )
    site_list = [
        ConsultantInboxSite(id=str(s.id), site_name=s.site_name, domain=s.domain) for s in sites
    ]
    return ConsultantInboxResponse(
        scope="workspace",
        summary=summary,
        sites=site_list,
        urgent=urgent,
        in_progress=in_progress,
        monitoring=monitoring,
    )


def _workspace_label(name: str, client_name: str | None) -> str:
    return client_name or name


async def build_account_consultant_inbox(
    db: AsyncSession,
    *,
    user_id: UUID,
    account_id: UUID,
    include_all_account_clients: bool = False,
) -> ConsultantInboxResponse:
    """Aggregate consultant todos across client workspaces in the account."""
    client_workspaces = await list_client_workspaces_for_account(
        db,
        account_id=account_id,
        user_id=user_id,
        include_all_account_clients=include_all_account_clients,
    )

    merged_items: list[ConsultantInboxItem] = []
    all_sites: list[ConsultantInboxSite] = []
    workspace_rows: list[ConsultantInboxWorkspace] = []

    for ws in client_workspaces:
        inbox = await build_consultant_inbox(db, ws.id)
        label = _workspace_label(ws.name, ws.client_name)
        primary = inbox.sites[0] if inbox.sites else None
        workspace_rows.append(
            ConsultantInboxWorkspace(
                id=str(ws.id),
                name=ws.name,
                client_name=ws.client_name,
                workspace_type=ws.workspace_type,
                urgent=inbox.summary.urgent,
                total=inbox.summary.total,
                primary_site_id=primary.id if primary else None,
                primary_site_domain=primary.domain if primary else None,
            )
        )
        for site in inbox.sites:
            all_sites.append(
                ConsultantInboxSite(
                    id=site.id,
                    site_name=site.site_name,
                    domain=site.domain,
                    workspace_id=str(ws.id),
                )
            )
        for bucket in (inbox.urgent, inbox.in_progress, inbox.monitoring):
            for item in bucket:
                merged_items.append(
                    item.model_copy(
                        update={
                            "id": f"{ws.id}:{item.id}",
                            "workspace_id": str(ws.id),
                            "workspace_label": label,
                        }
                    )
                )

    urgent: list[ConsultantInboxItem] = []
    in_progress: list[ConsultantInboxItem] = []
    monitoring: list[ConsultantInboxItem] = []
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    merged_items.sort(key=lambda i: (priority_order.get(i.priority, 9), i.created_at or ""))
    for item in merged_items:
        bucket = _bucket_item(item)
        if bucket == "urgent":
            urgent.append(item)
        elif bucket == "in_progress":
            in_progress.append(item)
        else:
            monitoring.append(item)

    summary = ConsultantInboxSummary(
        urgent=len(urgent),
        in_progress=len(in_progress),
        monitoring=len(monitoring),
        total=len(merged_items),
    )
    return ConsultantInboxResponse(
        scope="account",
        summary=summary,
        sites=all_sites,
        workspaces=workspace_rows,
        urgent=urgent,
        in_progress=in_progress,
        monitoring=monitoring,
    )
