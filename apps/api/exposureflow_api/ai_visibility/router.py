from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.ai_visibility import service
from exposureflow_api.ai_visibility.schemas import (
    AIProbeRunResponse,
    AIProbeSetCreate,
    AIProbeSetResponse,
    AIProbeSetUpdate,
    AICitationResponse,
    AssistedProbeRunRequest,
    BrandEntityCreate,
    BrandEntityResponse,
    BrandEntityUpdate,
    EntityCheckResponse,
    ManualImportRequest,
    SerpoRecordCreate,
    SerpoRecordResponse,
    VisibilityScoreResponse,
)
from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.models import (
    AIProbeRun,
    AIProbeSet,
    AICitation,
    BrandEntity,
    SerpoRecord,
    TopicCluster,
)

router = APIRouter(prefix="/api/v1/ai-visibility", tags=["ai-visibility"])


async def _validate_topic_cluster(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    topic_cluster_id: UUID | None,
) -> None:
    if topic_cluster_id is None:
        return
    cluster = await db.get(TopicCluster, topic_cluster_id)
    if (
        cluster is None
        or cluster.workspace_id != workspace_id
        or cluster.site_id != site_id
    ):
        raise not_found("Topic cluster")


@router.get("/probe-sets", response_model=list[AIProbeSetResponse])
async def list_probe_sets(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[AIProbeSet]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(AIProbeSet).where(
            AIProbeSet.workspace_id == workspace_id,
            AIProbeSet.site_id == site_id,
        )
    )
    return list(result.scalars().all())


@router.post("/probe-sets", response_model=AIProbeSetResponse)
async def create_probe_set(
    body: AIProbeSetCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> AIProbeSet:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    await _validate_topic_cluster(db, workspace_id, body.site_id, body.topic_cluster_id)
    probe_set = AIProbeSet(
        workspace_id=workspace_id,
        site_id=body.site_id,
        name=body.name,
        prompts_json=body.prompts_json,
        surfaces_json=body.surfaces_json,
        topic_cluster_id=body.topic_cluster_id,
        schedule=body.schedule,
        active=body.active,
    )
    db.add(probe_set)
    await db.commit()
    await db.refresh(probe_set)
    return probe_set


@router.patch("/probe-sets/{probe_set_id}", response_model=AIProbeSetResponse)
async def update_probe_set(
    probe_set_id: UUID,
    body: AIProbeSetUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> AIProbeSet:
    _user, _membership, workspace_id = ctx
    probe_set = await db.get(AIProbeSet, probe_set_id)
    if probe_set is None or probe_set.workspace_id != workspace_id:
        raise not_found("AI probe set")
    if body.name is not None:
        probe_set.name = body.name
    if body.prompts_json is not None:
        probe_set.prompts_json = body.prompts_json
    if body.surfaces_json is not None:
        probe_set.surfaces_json = body.surfaces_json
    if body.topic_cluster_id is not None:
        await _validate_topic_cluster(db, workspace_id, probe_set.site_id, body.topic_cluster_id)
        probe_set.topic_cluster_id = body.topic_cluster_id
    if body.schedule is not None:
        probe_set.schedule = body.schedule
    if body.active is not None:
        probe_set.active = body.active
    await db.commit()
    await db.refresh(probe_set)
    return probe_set


@router.get("/probe-sets/{probe_set_id}/visibility-score", response_model=VisibilityScoreResponse)
async def get_visibility_score(
    probe_set_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> VisibilityScoreResponse:
    _user, _membership, workspace_id = ctx
    metrics = await service.probe_set_visibility_score(db, workspace_id, probe_set_id)
    return VisibilityScoreResponse(
        visibility_score=metrics.visibility_score,
        total_runs=metrics.total_runs,
        our_brand_mention_rate=metrics.our_brand_mention_rate,
        our_url_citation_rate=metrics.our_url_citation_rate,
        competitor_mention_rate=metrics.competitor_mention_rate,
    )


@router.post("/runs/assisted", response_model=AIProbeRunResponse)
async def submit_assisted_run(
    body: AssistedProbeRunRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> AIProbeRun:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    await service.validate_probe_set(db, workspace_id, body.site_id, body.probe_set_id)
    run = await service.record_probe_run(
        db,
        workspace_id=workspace_id,
        site_id=body.site_id,
        probe_set_id=body.probe_set_id,
        probe_mode="assisted_manual",
        surface=body.surface,
        prompt=body.prompt,
        answer_text=body.answer_text,
        cited_urls=body.cited_urls,
        mentioned_brands=body.mentioned_brands,
        competitor_mentions=body.competitor_mentions,
        sentiment=body.sentiment,
        run_at=body.run_at,
    )
    await db.commit()
    await db.refresh(run)
    return run


@router.post("/runs/import")
async def import_runs(
    body: ManualImportRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    runs = await service.import_probe_runs(
        db,
        workspace_id,
        body.site_id,
        body.probe_set_id,
        format=body.format,
        csv_content=body.csv_content,
        rows=body.rows,
    )
    await db.commit()
    return {"runs_imported": len(runs)}


@router.get("/runs", response_model=list[AIProbeRunResponse])
async def list_runs(
    site_id: UUID,
    probe_set_id: UUID | None = None,
    limit: int = Query(default=50, le=200),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[AIProbeRun]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    stmt = select(AIProbeRun).where(
        AIProbeRun.workspace_id == workspace_id,
        AIProbeRun.site_id == site_id,
    )
    if probe_set_id:
        stmt = stmt.where(AIProbeRun.probe_set_id == probe_set_id)
    result = await db.execute(stmt.order_by(AIProbeRun.run_at.desc()).limit(limit))
    return list(result.scalars().all())


@router.get("/citations", response_model=list[AICitationResponse])
async def list_citations(
    site_id: UUID,
    limit: int = Query(default=100, le=500),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[AICitation]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(AICitation)
        .where(
            AICitation.workspace_id == workspace_id,
            AICitation.site_id == site_id,
        )
        .order_by(AICitation.captured_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/brand-entities", response_model=list[BrandEntityResponse])
async def list_brand_entities(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[BrandEntity]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(BrandEntity).where(
            BrandEntity.workspace_id == workspace_id,
            BrandEntity.site_id == site_id,
        )
    )
    return list(result.scalars().all())


@router.post("/brand-entities", response_model=BrandEntityResponse)
async def create_brand_entity(
    body: BrandEntityCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> BrandEntity:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    entity = BrandEntity(
        workspace_id=workspace_id,
        site_id=body.site_id,
        canonical_name=body.canonical_name,
        aliases_json=body.aliases_json,
        description=body.description,
        official_profiles_json=body.official_profiles_json,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity


@router.patch("/brand-entities/{entity_id}", response_model=BrandEntityResponse)
async def update_brand_entity(
    entity_id: UUID,
    body: BrandEntityUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> BrandEntity:
    _user, _membership, workspace_id = ctx
    entity = await db.get(BrandEntity, entity_id)
    if entity is None or entity.workspace_id != workspace_id:
        raise not_found("Brand entity")
    if body.canonical_name is not None:
        entity.canonical_name = body.canonical_name
    if body.aliases_json is not None:
        entity.aliases_json = body.aliases_json
    if body.description is not None:
        entity.description = body.description
    if body.official_profiles_json is not None:
        entity.official_profiles_json = body.official_profiles_json
    await db.commit()
    await db.refresh(entity)
    return entity


@router.post("/entity-check", response_model=EntityCheckResponse)
async def entity_check(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> EntityCheckResponse:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await service.run_entity_check(db, workspace_id, site_id)
    await db.commit()
    return EntityCheckResponse(**result)


@router.get("/serpo-records", response_model=list[SerpoRecordResponse])
async def list_serpo_records(
    site_id: UUID,
    limit: int = Query(default=50, le=200),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SerpoRecord]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(SerpoRecord)
        .where(
            SerpoRecord.workspace_id == workspace_id,
            SerpoRecord.site_id == site_id,
        )
        .order_by(SerpoRecord.captured_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.post("/serpo-records", response_model=SerpoRecordResponse)
async def capture_serpo(
    body: SerpoRecordCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> SerpoRecord:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    record = await service.capture_serpo_snapshot(
        db,
        workspace_id,
        body.site_id,
        brand_query=body.brand_query,
        keyword=body.keyword,
        surface=body.surface,
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/opportunities/generate")
async def generate_ai_opportunities(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.generate_ai_opportunities(db, workspace_id, site_id)
    await db.commit()
    return {"opportunities_created": count}
