"""Collect all ops health check results."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.ops_maintenance.checks import OpsCheckResult, check_api_health, check_content_pipeline
from exposureflow_api.ops_maintenance.checks import check_db_connectivity, check_delivery_backlog
from exposureflow_api.ops_maintenance.checks import check_failed_jobs, check_integration_errors
from exposureflow_api.ops_maintenance.checks import check_redis_connectivity, check_stuck_jobs, check_web_health

logger = logging.getLogger(__name__)

CheckFn = Callable[[AsyncSession], Awaitable[OpsCheckResult | list[OpsCheckResult]]]


async def _run_check(
    fn: CheckFn, db: AsyncSession, check_id: str
) -> list[OpsCheckResult]:
    try:
        out = await fn(db)
        if isinstance(out, list):
            return out
        return [out]
    except Exception as exc:  # noqa: BLE001
        logger.exception("ops check failed: %s", check_id)
        return [
            OpsCheckResult(
                check_id="ops.check_failed",
                category="infra",
                severity="critical",
                title=f"巡檢項目執行失敗：{check_id}",
                message=str(exc)[:500],
                recommended_action="查看 API logs 並修復 check 實作或環境",
                evidence={"failed_check": check_id, "error": str(exc)[:200]},
                action_type="manual",
            )
        ]


async def _run_no_db(fn: Callable[[], Awaitable[OpsCheckResult]], check_id: str) -> list[OpsCheckResult]:
    try:
        return [await fn()]
    except Exception as exc:  # noqa: BLE001
        logger.exception("ops check failed: %s", check_id)
        return [
            OpsCheckResult(
                check_id="ops.check_failed",
                category="infra",
                severity="critical",
                title=f"巡檢項目執行失敗：{check_id}",
                message=str(exc)[:500],
                recommended_action="查看 API logs",
                evidence={"failed_check": check_id},
                action_type="manual",
            )
        ]


async def collect_ops_health(db: AsyncSession) -> list[OpsCheckResult]:
    results: list[OpsCheckResult] = []
    results.extend(await _run_no_db(check_api_health, "infra.api_health"))
    results.extend(await _run_no_db(check_web_health, "infra.web_health"))
    results.extend(await _run_no_db(check_redis_connectivity, "infra.redis_connectivity"))
    results.extend(await _run_check(check_db_connectivity, db, "infra.db_connectivity"))
    results.extend(await _run_check(check_failed_jobs, db, "jobs.failed_24h"))
    results.extend(await _run_check(check_stuck_jobs, db, "jobs.queue_stuck"))
    results.extend(await _run_check(check_integration_errors, db, "integration"))
    results.extend(await _run_check(check_content_pipeline, db, "content"))
    results.extend(await _run_check(check_delivery_backlog, db, "delivery"))
    return results
