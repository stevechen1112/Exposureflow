from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.content import service as content_service
from exposureflow_api.content.schemas import (
    BriefBuildRequest,
    ContentBriefResponse,
    ContentClaimResponse,
    GateResultResponse,
    GenerationRunCreate,
    GenerationRunResponse,
    RequestChangesRequest,
    ReviewActionRequest,
    SourcePackBuildRequest,
    SourcePackResponse,
)
from exposureflow_api.database import get_db
from exposureflow_api.execution.brief_builder import build_content_brief
from exposureflow_api.execution.source_pack import build_source_pack
from exposureflow_api.exposure.deps import get_site_in_workspace

router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.post("/source-packs/build", response_model=SourcePackResponse)
async def build_source_pack_endpoint(
    body: SourcePackBuildRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    result = await build_source_pack(
        db,
        workspace_id=workspace_id,
        site_id=body.site_id,
        opportunity_id=body.opportunity_id,
        execution_job_id=body.execution_job_id,
        market=body.market,
        language=body.language,
        brief_type=body.brief_type,
    )
    await db.commit()
    await db.refresh(result.source_pack)
    return result.source_pack


@router.get("/source-packs/{source_pack_id}", response_model=SourcePackResponse)
async def get_source_pack(
    source_pack_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await content_service.get_source_pack(db, workspace_id, source_pack_id)


@router.post("/briefs/build", response_model=ContentBriefResponse)
async def build_brief(
    body: BriefBuildRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    brief = await build_content_brief(
        db,
        workspace_id=workspace_id,
        site_id=body.site_id,
        opportunity_id=body.opportunity_id,
        source_pack_id=body.source_pack_id,
        decision_id=body.decision_id,
    )
    await db.commit()
    await db.refresh(brief)
    return brief


@router.get("/briefs/{brief_id}", response_model=ContentBriefResponse)
async def get_brief(
    brief_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await content_service.get_brief(db, workspace_id, brief_id)


@router.post("/generation-runs", response_model=GenerationRunResponse)
async def create_generation_run(
    body: GenerationRunCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await content_service.create_generation_run(
        db,
        workspace_id,
        site_id=body.site_id,
        execution_job_id=body.execution_job_id,
        content_brief_id=body.content_brief_id,
        generation_mode=body.generation_mode,
        review_level=body.review_level,
        auto_compile=body.auto_compile,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/generation-runs/{run_id}/compile", response_model=GenerationRunResponse)
async def compile_generation_run(
    run_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await content_service.compile_generation_run(db, workspace_id, run_id)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/generation-runs", response_model=list[GenerationRunResponse])
async def list_generation_runs(
    site_id: UUID,
    status: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    from sqlalchemy import select as sa_select
    from exposureflow_api.models.execution_content import ContentGenerationRun

    stmt = sa_select(ContentGenerationRun).where(
        ContentGenerationRun.workspace_id == workspace_id,
        ContentGenerationRun.site_id == site_id,
    )
    if status:
        stmt = stmt.where(ContentGenerationRun.status == status)
    stmt = stmt.order_by(ContentGenerationRun.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/generation-runs/{run_id}", response_model=GenerationRunResponse)
async def get_generation_run(
    run_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await content_service.get_generation_run(db, workspace_id, run_id)


@router.post("/generation-runs/{run_id}/verify-claims", response_model=GateResultResponse)
async def verify_claims(
    run_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    gate = await content_service.verify_generation_run_claims(db, workspace_id, run_id)
    await db.commit()
    await db.refresh(gate)
    return gate


@router.post("/generation-runs/{run_id}/publish-gate", response_model=GateResultResponse)
async def publish_gate(
    run_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    gate = await content_service.check_publish_gate(db, workspace_id, run_id)
    await db.commit()
    await db.refresh(gate)
    return gate


@router.post("/generation-runs/{run_id}/approve", response_model=GenerationRunResponse)
async def approve_generation_run(
    run_id: UUID,
    body: ReviewActionRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    row = await content_service.approve_generation_run(
        db,
        workspace_id,
        run_id,
        actor_user_id=user.id,
        rationale=body.rationale,
        override=body.override,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/generation-runs/{run_id}/request-changes", response_model=GenerationRunResponse)
async def request_changes(
    run_id: UUID,
    body: RequestChangesRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    row = await content_service.request_changes(
        db,
        workspace_id,
        run_id,
        actor_user_id=user.id,
        notes=body.notes,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/generation-runs/{run_id}/publish")
async def publish_wordpress(
    run_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _membership, workspace_id = ctx
    result = await content_service.publish_to_wordpress(
        db, workspace_id, run_id, actor_user_id=user.id
    )
    await db.commit()
    return result


@router.get("/generation-runs/{run_id}/claims", response_model=list[ContentClaimResponse])
async def list_run_claims(
    run_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await content_service.list_run_claims(db, workspace_id, run_id)


@router.get("/gate-results", response_model=list[GateResultResponse])
async def list_gate_results(
    execution_job_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await content_service.list_gate_results(
        db, workspace_id, execution_job_id=execution_job_id
    )
