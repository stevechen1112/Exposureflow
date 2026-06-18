from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.integrations.schemas import (
    Ga4PageMetricResponse,
    GscDataSummaryResponse,
    GscRowResponse,
    SerpSlotResponse,
    SerpSnapshotRequest,
    SerpSnapshotResponse,
    SyncStateResponse,
    SyncTriggerRequest,
    TechnicalIssueResponse,
)
from exposureflow_api.integrations.gsc_summary import get_gsc_data_summary
from exposureflow_api.jobs.service import enqueue_job
from exposureflow_api.models import (
    Ga4PageMetric,
    GscPerformanceRow,
    IntegrationSyncState,
    SerpQuerySnapshot,
    SerpSlot,
    TechnicalIssue,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.post("/gsc/sync")
async def trigger_gsc_sync(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="gsc.sync",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/ga4/sync")
async def trigger_ga4_sync(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="ga4.sync",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/bing/sync")
async def trigger_bing_sync(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="bing.sync",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/serp/snapshot", response_model=dict)
async def trigger_serp_snapshot(
    body: SerpSnapshotRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="serp.snapshot",
        site_id=body.site_id,
        input_json={
            "keyword": body.keyword,
            "country": body.country,
            "language": body.language,
            "device": body.device,
        },
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/tech-seo/crawl")
async def trigger_tech_seo_crawl(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="tech_seo.crawl",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/indexability/sitemap-health")
async def trigger_sitemap_health_check(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="indexability.sitemap_health",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/indexability/published-noindex")
async def trigger_published_noindex_check(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="indexability.published_noindex",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/indexability/coverage-check")
async def trigger_indexability_coverage_check(
    body: SyncTriggerRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="indexability.coverage_check",
        site_id=body.site_id,
        input_json=body.input_json,
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.get("/gsc/performance", response_model=list[GscRowResponse])
async def query_gsc_performance(
    site_id: UUID,
    query: str | None = None,
    page: str | None = None,
    limit: int = Query(default=100, le=1000),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> list[GscPerformanceRow]:
    _user, _membership, workspace_id = ctx
    stmt = select(GscPerformanceRow).where(
        GscPerformanceRow.workspace_id == workspace_id,
        GscPerformanceRow.site_id == site_id,
    )
    if query:
        stmt = stmt.where(GscPerformanceRow.query.ilike(f"%{query}%"))
    if page:
        stmt = stmt.where(GscPerformanceRow.page.ilike(f"%{page}%"))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/gsc/summary", response_model=GscDataSummaryResponse)
async def get_gsc_summary(
    site_id: UUID,
    top_queries: int = Query(default=5, ge=1, le=20),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> GscDataSummaryResponse:
    _user, _membership, workspace_id = ctx
    summary = await get_gsc_data_summary(
        db,
        workspace_id=workspace_id,
        site_id=site_id,
        top_queries_limit=top_queries,
    )
    return GscDataSummaryResponse.model_validate(summary)


@router.get("/ga4/pages", response_model=list[Ga4PageMetricResponse])
async def query_ga4_pages(
    site_id: UUID,
    page_path: str | None = None,
    limit: int = Query(default=100, le=1000),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> list[Ga4PageMetricResponse]:
    _user, _membership, workspace_id = ctx
    stmt = select(Ga4PageMetric).where(
        Ga4PageMetric.workspace_id == workspace_id,
        Ga4PageMetric.site_id == site_id,
    )
    if page_path:
        stmt = stmt.where(Ga4PageMetric.page_path.ilike(f"%{page_path}%"))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return [Ga4PageMetricResponse.model_validate(row) for row in rows]


@router.get("/serp/snapshots/{snapshot_id}", response_model=SerpSnapshotResponse)
async def get_serp_snapshot(
    snapshot_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> SerpSnapshotResponse:
    _user, _membership, workspace_id = ctx
    snap_result = await db.execute(
        select(SerpQuerySnapshot).where(
            SerpQuerySnapshot.id == snapshot_id,
            SerpQuerySnapshot.workspace_id == workspace_id,
        )
    )
    snapshot = snap_result.scalar_one_or_none()
    if snapshot is None:
        raise not_found("SERP snapshot")

    slots_result = await db.execute(
        select(SerpSlot).where(SerpSlot.snapshot_id == snapshot_id)
    )
    slots = list(slots_result.scalars().all())
    return SerpSnapshotResponse(
        id=snapshot.id,
        keyword=snapshot.keyword,
        country=snapshot.country,
        language=snapshot.language,
        device=snapshot.device,
        raw_provider=snapshot.raw_provider,
        slots=[SerpSlotResponse.model_validate(s) for s in slots],
    )


@router.get("/technical-issues", response_model=list[TechnicalIssueResponse])
async def list_technical_issues(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> list[TechnicalIssue]:
    _user, _membership, workspace_id = ctx
    result = await db.execute(
        select(TechnicalIssue).where(
            TechnicalIssue.workspace_id == workspace_id,
            TechnicalIssue.site_id == site_id,
            TechnicalIssue.status == "open",
        )
    )
    return list(result.scalars().all())


@router.get("/sync-states", response_model=list[SyncStateResponse])
async def list_sync_states(
    site_id: UUID | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SyncStateResponse]:
    _user, _membership, workspace_id = ctx
    stmt = select(IntegrationSyncState).where(IntegrationSyncState.workspace_id == workspace_id)
    if site_id:
        stmt = stmt.where(IntegrationSyncState.site_id == site_id)
    result = await db.execute(stmt)
    states = list(result.scalars().all())
    return [
        SyncStateResponse(
            provider=s.provider,
            site_id=s.site_id,
            last_synced_at=s.last_synced_at.isoformat() if s.last_synced_at else None,
            last_success_at=s.last_success_at.isoformat() if s.last_success_at else None,
            last_error=s.last_error,
            cursor_json=s.cursor_json,
        )
        for s in states
    ]
