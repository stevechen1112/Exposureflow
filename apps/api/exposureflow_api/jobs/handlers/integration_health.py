"""Integration health check job handler."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import finalize_job_run, get_site
from exposureflow_api.models import IntegrationCredential, IntegrationSyncState, JobRun


async def run_integration_health_check(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required",
        )
        return

    site = await get_site(db, run.workspace_id, site_id)
    if site is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="SITE_NOT_FOUND",
            error_message="Site not found",
        )
        return

    creds = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.workspace_id == run.workspace_id,
            IntegrationCredential.status == "active",
            (IntegrationCredential.site_id == site_id)
            | (IntegrationCredential.site_id.is_(None)),
        )
    )
    states = await db.execute(
        select(IntegrationSyncState).where(
            IntegrationSyncState.workspace_id == run.workspace_id,
            IntegrationSyncState.site_id == site_id,
        )
    )
    credential_rows = list(creds.scalars().all())
    state_rows = list(states.scalars().all())

    providers_configured = sorted({c.provider for c in credential_rows})
    unhealthy = [
        {
            "provider": s.provider,
            "last_error": s.last_error,
            "last_success_at": s.last_success_at.isoformat() if s.last_success_at else None,
        }
        for s in state_rows
        if s.last_error
    ]

    await finalize_job_run(
        run,
        success=True,
        output={
            "site_id": str(site_id),
            "providers_configured": providers_configured,
            "unhealthy_providers": unhealthy,
            "healthy": len(unhealthy) == 0,
        },
        provider="integration",
    )
