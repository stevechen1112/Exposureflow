"""Shared helpers for integration sync jobs."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.crypto import decrypt_secret
from exposureflow_api.integrations.error_sanitizer import sanitize_sync_error
from exposureflow_api.models import (
    BingPerformanceRow,
    Ga4PageMetric,
    GscPerformanceRow,
    IntegrationCredential,
    IntegrationSyncState,
    JobRun,
    Site,
)


async def get_site(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> Site | None:
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


async def get_credential(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, provider: str
) -> IntegrationCredential | None:
    site_result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.workspace_id == workspace_id,
            IntegrationCredential.provider == provider,
            IntegrationCredential.status == "active",
            IntegrationCredential.site_id == site_id,
        )
    )
    site_credential = site_result.scalar_one_or_none()
    if site_credential is not None:
        return site_credential

    workspace_result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.workspace_id == workspace_id,
            IntegrationCredential.provider == provider,
            IntegrationCredential.status == "active",
            IntegrationCredential.site_id.is_(None),
        )
    )
    return workspace_result.scalar_one_or_none()


def decrypt_credential_payload(credential: IntegrationCredential) -> str:
    return decrypt_secret(credential.encrypted_payload)


async def get_or_create_sync_state(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, provider: str
) -> IntegrationSyncState:
    result = await db.execute(
        select(IntegrationSyncState).where(
            IntegrationSyncState.workspace_id == workspace_id,
            IntegrationSyncState.site_id == site_id,
            IntegrationSyncState.provider == provider,
        )
    )
    state = result.scalar_one_or_none()
    if state is None:
        state = IntegrationSyncState(
            workspace_id=workspace_id,
            site_id=site_id,
            provider=provider,
            cursor_json={},
        )
        db.add(state)
        await db.flush()
    return state


async def upsert_gsc_rows(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, rows: list
) -> int:
    if not rows:
        return 0
    values = [
        {
            "workspace_id": workspace_id,
            "site_id": site_id,
            "date": row.date,
            "query": row.query,
            "page": row.page,
            "country": row.country or "",
            "device": row.device or "",
            "impressions": row.impressions,
            "clicks": row.clicks,
            "ctr": row.ctr,
            "position": row.position,
        }
        for row in rows
    ]
    stmt = insert(GscPerformanceRow).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_gsc_row",
        set_={
            "impressions": stmt.excluded.impressions,
            "clicks": stmt.excluded.clicks,
            "ctr": stmt.excluded.ctr,
            "position": stmt.excluded.position,
        },
    )
    await db.execute(stmt)
    return len(values)


async def upsert_ga4_rows(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, rows: list
) -> int:
    if not rows:
        return 0
    values = [
        {
            "workspace_id": workspace_id,
            "site_id": site_id,
            "date": row.date,
            "page_path": row.page_path,
            "sessions": row.sessions,
            "engaged_sessions": row.engaged_sessions,
            "engagement_rate": row.engagement_rate,
            "conversions": row.conversions,
        }
        for row in rows
    ]
    stmt = insert(Ga4PageMetric).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_ga4_page",
        set_={
            "sessions": stmt.excluded.sessions,
            "engaged_sessions": stmt.excluded.engaged_sessions,
            "engagement_rate": stmt.excluded.engagement_rate,
            "conversions": stmt.excluded.conversions,
        },
    )
    await db.execute(stmt)
    return len(values)


async def upsert_bing_rows(
    db: AsyncSession, workspace_id: UUID, site_id: UUID, rows: list
) -> int:
    if not rows:
        return 0
    values = [
        {
            "workspace_id": workspace_id,
            "site_id": site_id,
            "date": row.date,
            "query": row.query,
            "page": row.page,
            "country": row.country or "",
            "device": row.device or "",
            "impressions": row.impressions,
            "clicks": row.clicks,
            "ctr": row.ctr,
            "position": row.position,
        }
        for row in rows
    ]
    stmt = insert(BingPerformanceRow).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_bing_row",
        set_={
            "impressions": stmt.excluded.impressions,
            "clicks": stmt.excluded.clicks,
            "ctr": stmt.excluded.ctr,
            "position": stmt.excluded.position,
        },
    )
    await db.execute(stmt)
    return len(values)


def parse_last_sync_date(cursor: dict) -> date | None:
    raw = cursor.get("last_synced_date")
    if raw is None:
        return None
    return date.fromisoformat(raw)


def mark_sync_success(
    state: IntegrationSyncState,
    *,
    last_date: date | None = None,
    extra: dict | None = None,
) -> None:
    now = datetime.now(UTC)
    state.last_synced_at = now
    state.last_success_at = now
    state.last_error = None
    if last_date is not None:
        state.cursor_json = {**state.cursor_json, "last_synced_date": last_date.isoformat()}
    if extra:
        state.cursor_json = {**state.cursor_json, **extra}


def mark_sync_failure(state: IntegrationSyncState, error: str | Exception) -> None:
    state.last_synced_at = datetime.now(UTC)
    state.last_error = sanitize_sync_error(error)


async def finalize_job_run(
    run: JobRun,
    *,
    success: bool,
    output: dict,
    provider: str | None = None,
    cost_cents: int = 0,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    run.completed_at = datetime.now(UTC)
    run.output_json = output
    run.provider = provider
    run.provider_cost_cents = cost_cents
    if success:
        run.status = "succeeded"
    else:
        run.status = "failed"
        run.error_code = error_code
        run.error_message = sanitize_sync_error(error_message) if error_message else None
