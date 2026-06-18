from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import APIError
from exposureflow_api.database import get_db
from exposureflow_api.decision import service
from exposureflow_api.decision.schemas import (
    ActionCandidateResponse,
    ActionDecisionResponse,
    DecisionRequest,
    RoadmapBuildRequest,
    RoadmapItemResponse,
    RoadmapResponse,
)
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.jobs.service import enqueue_job

router = APIRouter(prefix="/api/v1", tags=["decisions"])


@router.get("/decisions/candidates", response_model=list[ActionCandidateResponse])
async def list_candidates(
    site_id: UUID,
    status: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_action_candidates(
        db, workspace_id, site_id, status=status
    )


@router.post("/decisions/candidates/generate")
async def generate_candidates(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.generate_action_candidates(db, workspace_id, site_id)
    await db.commit()
    return {"candidates_created": count}


@router.post(
    "/decisions/candidates/{candidate_id}/approve",
    response_model=ActionDecisionResponse,
)
async def approve_candidate(
    candidate_id: UUID,
    body: DecisionRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> ActionDecisionResponse:
    user, _membership, workspace_id = ctx
    candidate = await service.get_candidate_in_workspace(db, workspace_id, candidate_id)
    await get_site_in_workspace(db, workspace_id, candidate.site_id)
    decision = await service.record_decision(
        db,
        workspace_id=workspace_id,
        candidate_id=candidate_id,
        user_id=user.user_id,
        decision="approve",
        rationale=body.rationale,
        scheduled_for=body.scheduled_for,
        confidence=body.confidence,
    )
    await db.commit()
    await db.refresh(decision)
    return decision


@router.post(
    "/decisions/candidates/{candidate_id}/reject",
    response_model=ActionDecisionResponse,
)
async def reject_candidate(
    candidate_id: UUID,
    body: DecisionRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> ActionDecisionResponse:
    user, _membership, workspace_id = ctx
    candidate = await service.get_candidate_in_workspace(db, workspace_id, candidate_id)
    await get_site_in_workspace(db, workspace_id, candidate.site_id)
    decision = await service.record_decision(
        db,
        workspace_id=workspace_id,
        candidate_id=candidate_id,
        user_id=user.user_id,
        decision="reject",
        rationale=body.rationale,
        scheduled_for=body.scheduled_for,
        confidence=body.confidence,
    )
    await db.commit()
    await db.refresh(decision)
    return decision


@router.post(
    "/decisions/candidates/{candidate_id}/defer",
    response_model=ActionDecisionResponse,
)
async def defer_candidate(
    candidate_id: UUID,
    body: DecisionRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> ActionDecisionResponse:
    user, _membership, workspace_id = ctx
    candidate = await service.get_candidate_in_workspace(db, workspace_id, candidate_id)
    await get_site_in_workspace(db, workspace_id, candidate.site_id)
    decision = await service.record_decision(
        db,
        workspace_id=workspace_id,
        candidate_id=candidate_id,
        user_id=user.user_id,
        decision="defer",
        rationale=body.rationale,
        scheduled_for=body.scheduled_for,
        confidence=body.confidence,
    )
    await db.commit()
    await db.refresh(decision)
    return decision


@router.get("/outcomes")
async def list_action_outcomes(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    from exposureflow_api.decision.outcomes import list_action_outcomes as fetch_outcomes

    return await fetch_outcomes(db, workspace_id, site_id)


@router.get("/roadmaps", response_model=list[RoadmapResponse])
async def list_roadmaps(
    site_id: UUID,
    include_items: bool = Query(default=True),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[RoadmapResponse]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    roadmaps = await service.list_roadmaps(db, workspace_id, site_id)
    responses: list[RoadmapResponse] = []
    for roadmap in roadmaps:
        items: list[RoadmapItemResponse] = []
        if include_items:
            _rm, item_rows = await service.get_roadmap_with_items(db, workspace_id, roadmap.id)
            items = [RoadmapItemResponse.model_validate(i) for i in item_rows]
        responses.append(
            RoadmapResponse(
                id=roadmap.id,
                workspace_id=roadmap.workspace_id,
                site_id=roadmap.site_id,
                horizon_weeks=roadmap.horizon_weeks,
                title=roadmap.title,
                status=roadmap.status,
                created_at=roadmap.created_at,
                updated_at=roadmap.updated_at,
                items=items,
            )
        )
    return responses


@router.post("/roadmaps/build", response_model=RoadmapResponse)
async def build_roadmap(
    body: RoadmapBuildRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    if body.horizon_weeks not in {4, 8, 16}:
        raise APIError(
            code="INVALID_HORIZON",
            message="horizon_weeks must be 4, 8, or 16",
            status_code=400,
        )
    roadmap = await service.build_site_roadmap(
        db,
        workspace_id,
        body.site_id,
        horizon_weeks=body.horizon_weeks,
        title=body.title,
    )
    await db.commit()
    _rm, items = await service.get_roadmap_with_items(db, workspace_id, roadmap.id)
    return RoadmapResponse(
        id=roadmap.id,
        workspace_id=roadmap.workspace_id,
        site_id=roadmap.site_id,
        horizon_weeks=roadmap.horizon_weeks,
        title=roadmap.title,
        status=roadmap.status,
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
        items=[RoadmapItemResponse.model_validate(i) for i in items],
    )


@router.post("/roadmaps/build/async")
async def build_roadmap_async(
    body: RoadmapBuildRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="roadmap.build",
        site_id=body.site_id,
        input_json={
            "horizon_weeks": body.horizon_weeks,
            "title": body.title,
        },
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}
