"""Rule-based ops health checks — no LLM judgment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import httpx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.config import settings
from exposureflow_api.models import (
    ContentGenerationRun,
    IntegrationCredential,
    IntegrationSyncState,
    JobRun,
    Site,
    Workspace,
)

Severity = Literal["pass", "warn", "critical"]

FAILED_JOBS_WARN = 3
FAILED_JOBS_CRITICAL = 10
QUEUED_STUCK_MINUTES = 30
QUEUED_STUCK_CRITICAL_MINUTES = 120
RUNNING_STUCK_MINUTES = 60
RUNNING_STUCK_CRITICAL_MINUTES = 240
GSC_STALE_HOURS = 48
CONTENT_QUEUED_STALE_MINUTES = 30
CONTENT_REVIEW_STALE_DAYS = 7


@dataclass
class OpsCheckResult:
    check_id: str
    category: str
    severity: Severity
    title: str
    message: str
    recommended_action: str
    workspace_id: UUID | None = None
    site_id: UUID | None = None
    evidence: dict = field(default_factory=dict)
    action_type: str | None = None


def _pass(check_id: str, category: str, title: str) -> OpsCheckResult:
    return OpsCheckResult(
        check_id=check_id,
        category=category,
        severity="pass",
        title=title,
        message="正常",
        recommended_action="無需處理",
    )


async def check_db_connectivity(db: AsyncSession) -> OpsCheckResult:
    try:
        await db.execute(text("SELECT 1"))
        return _pass("infra.db_connectivity", "infra", "資料庫連線")
    except Exception as exc:  # noqa: BLE001
        return OpsCheckResult(
            check_id="infra.db_connectivity",
            category="infra",
            severity="critical",
            title="資料庫無法連線",
            message=str(exc)[:500],
            recommended_action="檢查 DATABASE_URL、Postgres container 與 migration 狀態",
            evidence={"error": str(exc)[:200]},
            action_type="manual",
        )


async def check_redis_connectivity() -> OpsCheckResult:
    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        client.ping()
        return _pass("infra.redis_connectivity", "infra", "Redis 連線")
    except Exception as exc:  # noqa: BLE001
        return OpsCheckResult(
            check_id="infra.redis_connectivity",
            category="infra",
            severity="critical",
            title="Redis 無法連線",
            message=str(exc)[:500],
            recommended_action="檢查 REDIS_URL 與 Redis container",
            evidence={"error": str(exc)[:200]},
            action_type="manual",
        )


async def check_api_health() -> OpsCheckResult:
    url = f"{settings.api_base_url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            return _pass("infra.api_health", "infra", "API health")
        return OpsCheckResult(
            check_id="infra.api_health",
            category="infra",
            severity="critical",
            title="API health 異常",
            message=f"GET {url} → HTTP {resp.status_code}",
            recommended_action="檢查 API container logs 與 /health",
            evidence={"status_code": resp.status_code, "url": url},
            action_type="manual",
        )
    except Exception as exc:  # noqa: BLE001
        return OpsCheckResult(
            check_id="infra.api_health",
            category="infra",
            severity="critical",
            title="API health 無法連線",
            message=str(exc)[:500],
            recommended_action="確認 API 服務是否 running",
            evidence={"url": url, "error": str(exc)[:200]},
            action_type="manual",
        )


async def check_web_health() -> OpsCheckResult:
    url = settings.app_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            return _pass("infra.web_health", "infra", "Web 首頁")
        return OpsCheckResult(
            check_id="infra.web_health",
            category="infra",
            severity="critical",
            title="Web 首頁異常",
            message=f"GET {url} → HTTP {resp.status_code}",
            recommended_action="檢查 Web container 與 Caddy 路由",
            evidence={"status_code": resp.status_code, "url": url},
            action_type="manual",
        )
    except Exception as exc:  # noqa: BLE001
        return OpsCheckResult(
            check_id="infra.web_health",
            category="infra",
            severity="critical",
            title="Web 無法連線",
            message=str(exc)[:500],
            recommended_action="確認 Next.js 服務是否 running",
            evidence={"url": url, "error": str(exc)[:200]},
            action_type="manual",
        )


async def check_failed_jobs(db: AsyncSession) -> OpsCheckResult:
    since = datetime.now(UTC) - timedelta(hours=24)
    count = int(
        (
            await db.execute(
                select(func.count()).select_from(JobRun).where(
                    JobRun.status == "failed",
                    JobRun.created_at >= since,
                )
            )
        ).scalar_one()
    )
    if count >= FAILED_JOBS_CRITICAL:
        sev: Severity = "critical"
    elif count >= FAILED_JOBS_WARN:
        sev = "warn"
    else:
        return _pass("jobs.failed_24h", "jobs", "24h failed jobs")
    return OpsCheckResult(
        check_id="jobs.failed_24h",
        category="jobs",
        severity=sev,
        title=f"24 小時內 {count} 筆 job 失敗",
        message=f"過去 24 小時 failed job 數：{count}",
        recommended_action="到 Internal Admin → Jobs 檢視 error_code；transient 錯誤可 safe retry",
        evidence={"failed_count_24h": count},
        action_type="manual",
    )


async def check_stuck_jobs(db: AsyncSession) -> list[OpsCheckResult]:
    now = datetime.now(UTC)
    queued_cutoff = now - timedelta(minutes=QUEUED_STUCK_MINUTES)
    queued_critical_cutoff = now - timedelta(minutes=QUEUED_STUCK_CRITICAL_MINUTES)
    running_cutoff = now - timedelta(minutes=RUNNING_STUCK_MINUTES)
    running_critical_cutoff = now - timedelta(minutes=RUNNING_STUCK_CRITICAL_MINUTES)

    queued = list(
        (
            await db.execute(
                select(JobRun).where(
                    JobRun.status == "queued",
                    JobRun.created_at <= queued_cutoff,
                )
            )
        ).scalars().all()
    )
    running = list(
        (
            await db.execute(
                select(JobRun).where(
                    JobRun.status == "running",
                    JobRun.started_at.isnot(None),
                    JobRun.started_at <= running_cutoff,
                )
            )
        ).scalars().all()
    )

    results: list[OpsCheckResult] = []
    if queued:
        oldest = min(r.created_at for r in queued)
        age_min = int((now - oldest).total_seconds() / 60)
        sev: Severity = "critical" if oldest <= queued_critical_cutoff else "warn"
        results.append(
            OpsCheckResult(
                check_id="jobs.queue_stuck",
                category="jobs",
                severity=sev,
                title=f"{len(queued)} 筆 job 排隊過久",
                message=f"最久 queued {age_min} 分鐘",
                recommended_action="檢查 Celery worker 是否 running；查看 queue backlog",
                evidence={"queued_count": len(queued), "oldest_age_minutes": age_min},
                action_type="manual",
            )
        )
    else:
        results.append(_pass("jobs.queue_stuck", "jobs", "Job queue 無停滯"))

    if running:
        oldest = min(r.started_at for r in running if r.started_at)
        age_min = int((now - oldest).total_seconds() / 60)
        sev = "critical" if oldest <= running_critical_cutoff else "warn"
        results.append(
            OpsCheckResult(
                check_id="jobs.running_stuck",
                category="jobs",
                severity=sev,
                title=f"{len(running)} 筆 job running 超時",
                message=f"最久 running {age_min} 分鐘",
                recommended_action="檢查 worker logs；必要時 cancel 卡住的 run",
                evidence={"running_count": len(running), "oldest_age_minutes": age_min},
                action_type="manual",
            )
        )
    else:
        results.append(_pass("jobs.running_stuck", "jobs", "無 running 超時 job"))

    return results


async def check_integration_errors(db: AsyncSession) -> list[OpsCheckResult]:
    rows = list((await db.execute(select(IntegrationSyncState))).scalars().all())
    failing = [r for r in rows if r.last_error]
    stale_cutoff = datetime.now(UTC) - timedelta(hours=GSC_STALE_HOURS)
    gsc_stale = [
        r
        for r in rows
        if r.provider == "gsc"
        and not r.last_error
        and (r.last_success_at is None or r.last_success_at < stale_cutoff)
    ]

    results: list[OpsCheckResult] = []
    if failing:
        results.append(
            OpsCheckResult(
                check_id="integration.gsc_error",
                category="integration",
                severity="warn" if len(failing) < 5 else "critical",
                title=f"{len(failing)} 個整合同步錯誤",
                message="IntegrationSyncState.last_error 不為空",
                recommended_action="到 Integrations / Internal Admin 查看 provider 錯誤並重試 sync",
                evidence={
                    "failing_count": len(failing),
                    "sample": [
                        {
                            "provider": r.provider,
                            "workspace_id": str(r.workspace_id),
                            "site_id": str(r.site_id) if r.site_id else None,
                            "last_error": (r.last_error or "")[:120],
                        }
                        for r in failing[:5]
                    ],
                },
                action_type="manual",
            )
        )
    else:
        results.append(_pass("integration.gsc_error", "integration", "整合同步無 error"))

    if gsc_stale:
        results.append(
            OpsCheckResult(
                check_id="integration.gsc_stale",
                category="integration",
                severity="warn",
                title=f"{len(gsc_stale)} 個 GSC 同步過舊",
                message=f"GSC last sync 超過 {GSC_STALE_HOURS} 小時",
                recommended_action="觸發 GSC sync 或檢查 OAuth 憑證",
                evidence={"stale_count": len(gsc_stale)},
                action_type="manual",
            )
        )
    else:
        results.append(_pass("integration.gsc_stale", "integration", "GSC 同步時效正常"))

    active_sites = list(
        (await db.execute(select(Site).where(Site.status == "active"))).scalars().all()
    )
    creds = list(
        (
            await db.execute(
                select(IntegrationCredential).where(
                    IntegrationCredential.provider == "gsc",
                    IntegrationCredential.status == "active",
                )
            )
        ).scalars().all()
    )
    sites_with_gsc = {c.site_id for c in creds if c.site_id}
    missing = [s for s in active_sites if s.id not in sites_with_gsc]
    if missing:
        results.append(
            OpsCheckResult(
                check_id="integration.credential_missing",
                category="integration",
                severity="warn",
                title=f"{len(missing)} 個 active site 缺少 GSC 憑證",
                message="active site 無 GSC credential",
                recommended_action="顧問到 Integrations 代客戶連 GSC",
                evidence={"missing_site_count": len(missing)},
                action_type="open_inbox",
            )
        )
    else:
        results.append(_pass("integration.credential_missing", "integration", "GSC 憑證覆蓋正常"))

    return results


async def check_content_pipeline(db: AsyncSession) -> list[OpsCheckResult]:
    now = datetime.now(UTC)
    queued_cutoff = now - timedelta(minutes=CONTENT_QUEUED_STALE_MINUTES)
    review_cutoff = now - timedelta(days=CONTENT_REVIEW_STALE_DAYS)

    queued_stale = int(
        (
            await db.execute(
                select(func.count()).select_from(ContentGenerationRun).where(
                    ContentGenerationRun.status == "queued",
                    ContentGenerationRun.created_at <= queued_cutoff,
                )
            )
        ).scalar_one()
    )
    failed = int(
        (
            await db.execute(
                select(func.count()).select_from(ContentGenerationRun).where(
                    ContentGenerationRun.status == "failed",
                    ContentGenerationRun.updated_at >= now - timedelta(hours=24),
                )
            )
        ).scalar_one()
    )
    review_stale = int(
        (
            await db.execute(
                select(func.count()).select_from(ContentGenerationRun).where(
                    ContentGenerationRun.status == "needs_review",
                    ContentGenerationRun.updated_at <= review_cutoff,
                )
            )
        ).scalar_one()
    )

    results: list[OpsCheckResult] = []
    if queued_stale:
        results.append(
            OpsCheckResult(
                check_id="content.queued_stale",
                category="content",
                severity="warn",
                title=f"{queued_stale} 筆內容生成排隊過久",
                message=f"queued 超過 {CONTENT_QUEUED_STALE_MINUTES} 分鐘",
                recommended_action="檢查 content pipeline worker 與 LLM quota",
                evidence={"queued_stale_count": queued_stale},
                action_type="manual",
            )
        )
    else:
        results.append(_pass("content.queued_stale", "content", "內容 queue 正常"))

    if failed:
        results.append(
            OpsCheckResult(
                check_id="content.pipeline_failed",
                category="content",
                severity="warn" if failed < 5 else "critical",
                title=f"24h 內 {failed} 筆內容生成失敗",
                message="ContentGenerationRun status=failed",
                recommended_action="到內容審核 / job detail 查看錯誤；可 retry transient failures",
                evidence={"failed_24h": failed},
                action_type="manual",
            )
        )
    else:
        results.append(_pass("content.pipeline_failed", "content", "內容生成無近期失敗"))

    if review_stale:
        results.append(
            OpsCheckResult(
                check_id="delivery.content_review_stale",
                category="delivery",
                severity="warn",
                title=f"{review_stale} 筆內容待審超過 {CONTENT_REVIEW_STALE_DAYS} 天",
                message="needs_review 停滯",
                recommended_action="顧問到內容審核頁處理積壓",
                evidence={"review_stale_count": review_stale},
                action_type="open_inbox",
            )
        )
    else:
        results.append(_pass("delivery.content_review_stale", "delivery", "內容審核無長期積壓"))

    return results


async def check_delivery_backlog(db: AsyncSession) -> list[OpsCheckResult]:
    """Lightweight delivery signals without full consultant inbox build."""
    from exposureflow_api.models import ActionCandidate, TechnicalIssue

    open_technical = int(
        (
            await db.execute(
                select(func.count()).select_from(TechnicalIssue).where(TechnicalIssue.status == "open")
            )
        ).scalar_one()
    )
    pending_decisions = int(
        (
            await db.execute(
                select(func.count()).select_from(ActionCandidate).where(
                    ActionCandidate.decision_status == "pending"
                )
            )
        ).scalar_one()
    )
    active_workspaces = int(
        (
            await db.execute(
                select(func.count()).select_from(Workspace).where(Workspace.status == "active")
            )
        ).scalar_one()
    )

    results: list[OpsCheckResult] = []
    if open_technical >= 10:
        results.append(
            OpsCheckResult(
                check_id="delivery.urgent_inbox_aging",
                category="delivery",
                severity="warn",
                title=f"{open_technical} 個開放技術問題",
                message="TechnicalIssue status=open 數量偏高",
                recommended_action="顧問優先處理 critical/high 技術問題",
                evidence={"open_technical_count": open_technical},
                action_type="open_inbox",
            )
        )
    else:
        results.append(_pass("delivery.urgent_inbox_aging", "delivery", "技術問題積壓可控"))

    if pending_decisions >= 20:
        results.append(
            OpsCheckResult(
                check_id="delivery.strategy_backlog_growth",
                category="delivery",
                severity="warn",
                title=f"{pending_decisions} 筆待核准決策",
                message="ActionCandidate pending 數量偏高",
                recommended_action="顧問到機會佇列核准或拒絕",
                evidence={"pending_decisions": pending_decisions, "active_workspaces": active_workspaces},
                action_type="open_inbox",
            )
        )
    else:
        results.append(_pass("delivery.strategy_backlog_growth", "delivery", "決策待辦正常"))

    return results
