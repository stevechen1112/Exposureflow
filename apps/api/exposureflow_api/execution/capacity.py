"""Usage events and workspace capacity controls."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.billing import quota as billing_quota
from exposureflow_api.common.errors import APIError
from exposureflow_api.models.commercial import UsageEvent
from exposureflow_api.models.tenant import Workspace


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
    return await billing_quota.count_monthly_usage(db, workspace_id, metric)


async def check_capacity(
    db: AsyncSession,
    workspace_id: UUID,
    metric: str,
    *,
    quantity: int = 1,
    limit: int | None = None,
) -> None:
    if limit is not None:
        used = await count_monthly_usage(db, workspace_id, metric)
        if used + quantity > limit:
            raise APIError(
                code="QUOTA_EXCEEDED",
                message=f"Monthly quota exceeded for {metric}.",
                status_code=429,
                details={"metric": metric, "used": used, "limit": limit},
            )
        return
    await billing_quota.check_quota(db, workspace_id, metric, quantity=quantity)


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
