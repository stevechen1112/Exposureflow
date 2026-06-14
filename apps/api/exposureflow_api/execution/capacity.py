"""Usage events and workspace capacity controls."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import APIError
from exposureflow_api.models.commercial import UsageEvent
from exposureflow_api.models.tenant import Workspace

DEFAULT_MONTHLY_LIMITS: dict[str, int] = {
    "content_generation_runs": 50,
    "claim_verification_runs": 100,
    "knowledge_sources": 100,
    "knowledge_embedding": 5000,
    "llm_generation_tokens": 500_000,
}


async def _workspace_account_id(db: AsyncSession, workspace_id: UUID) -> UUID:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise APIError(
            code="NOT_FOUND",
            message="Workspace not found.",
            status_code=404,
        )
    return ws.account_id


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


async def check_capacity(
    db: AsyncSession,
    workspace_id: UUID,
    metric: str,
    *,
    quantity: int = 1,
    limit: int | None = None,
) -> None:
    cap = limit if limit is not None else DEFAULT_MONTHLY_LIMITS.get(metric, 10_000)
    used = await count_monthly_usage(db, workspace_id, metric)
    if used + quantity > cap:
        raise APIError(
            code="QUOTA_EXCEEDED",
            message=f"Monthly quota exceeded for {metric}.",
            status_code=429,
            details={"metric": metric, "used": used, "limit": cap},
        )


async def record_usage_event(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    metric: str,
    quantity: int = 1,
    site_id: UUID | None = None,
    provider: str | None = None,
    cost_cents: int = 0,
    idempotency_key: str,
) -> UsageEvent:
    account_id = await _workspace_account_id(db, workspace_id)
    existing = await db.execute(
        select(UsageEvent).where(UsageEvent.idempotency_key == idempotency_key)
    )
    row = existing.scalar_one_or_none()
    if row:
        return row

    event = UsageEvent(
        account_id=account_id,
        workspace_id=workspace_id,
        site_id=site_id,
        metric=metric,
        quantity=quantity,
        provider=provider,
        cost_cents=cost_cents,
        idempotency_key=idempotency_key,
    )
    db.add(event)
    await db.flush()
    return event
