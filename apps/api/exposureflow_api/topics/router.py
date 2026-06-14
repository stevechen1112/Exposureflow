from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.jobs.service import enqueue_job
from exposureflow_api.models import CannibalizationCase, InternalLinkSuggestion, TopicCluster, TopicNode
from exposureflow_api.topics import service
from exposureflow_api.topics.schemas import (
    CannibalizationResponse,
    InternalLinkApprovalRequest,
    InternalLinkResponse,
    RebuildRequest,
    TopicClusterResponse,
    TopicNodeAssignRequest,
    TopicNodeResponse,
)

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


@router.get("/clusters", response_model=list[TopicClusterResponse])
async def list_clusters(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[TopicCluster]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(TopicCluster)
        .where(
            TopicCluster.workspace_id == workspace_id,
            TopicCluster.site_id == site_id,
        )
        .order_by(TopicCluster.total_impressions.desc())
    )
    return list(result.scalars().all())


@router.get("/clusters/{cluster_id}", response_model=TopicClusterResponse)
async def get_cluster(
    cluster_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> TopicCluster:
    _user, _membership, workspace_id = ctx
    cluster = await db.get(TopicCluster, cluster_id)
    if cluster is None or cluster.workspace_id != workspace_id:
        raise not_found("Topic cluster")
    await get_site_in_workspace(db, workspace_id, cluster.site_id)
    return cluster


@router.post("/clusters/rebuild")
async def rebuild_clusters(
    body: RebuildRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="topic_graph.rebuild",
        site_id=body.site_id,
        input_json={},
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.post("/clusters/rebuild-sync")
async def rebuild_clusters_sync(
    body: RebuildRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    graph = await service.rebuild_topic_graph(db, workspace_id, body.site_id)
    cannibal = await service.run_cannibalization_detection(db, workspace_id, body.site_id)
    links = await service.generate_internal_links_for_site(db, workspace_id, body.site_id)
    await db.commit()
    return {**graph, "cannibalization_cases": cannibal, "internal_link_suggestions": links}


@router.get("/nodes", response_model=list[TopicNodeResponse])
async def list_nodes(
    site_id: UUID,
    cluster_id: UUID | None = None,
    status: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[TopicNode]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    stmt = select(TopicNode).where(
        TopicNode.workspace_id == workspace_id,
        TopicNode.site_id == site_id,
    )
    if cluster_id:
        stmt = stmt.where(TopicNode.topic_cluster_id == cluster_id)
    if status:
        stmt = stmt.where(TopicNode.status == status)
    result = await db.execute(stmt.order_by(TopicNode.impressions.desc()))
    return list(result.scalars().all())


@router.patch("/nodes/{node_id}", response_model=TopicNodeResponse)
async def assign_node_cluster(
    node_id: UUID,
    body: TopicNodeAssignRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> TopicNode:
    user, _membership, workspace_id = ctx
    node = await db.get(TopicNode, node_id)
    if node is None or node.workspace_id != workspace_id:
        raise not_found("Topic node")
    updated = await service.assign_node_cluster(
        db,
        workspace_id,
        node.site_id,
        node_id,
        body.topic_cluster_id,
        lock_assignment=body.lock_assignment,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(updated)
    return updated


@router.get("/cannibalization", response_model=list[CannibalizationResponse])
async def list_cannibalization(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[CannibalizationCase]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(CannibalizationCase).where(
            CannibalizationCase.workspace_id == workspace_id,
            CannibalizationCase.site_id == site_id,
            CannibalizationCase.status == "open",
        )
    )
    return list(result.scalars().all())


@router.post("/cannibalization/detect")
async def detect_cannibalization(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.run_cannibalization_detection(db, workspace_id, site_id)
    await db.commit()
    return {"cases_created": count}


@router.get("/internal-links", response_model=list[InternalLinkResponse])
async def list_internal_links(
    site_id: UUID,
    cluster_id: UUID | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[InternalLinkSuggestion]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    stmt = select(InternalLinkSuggestion).where(
        InternalLinkSuggestion.workspace_id == workspace_id,
        InternalLinkSuggestion.site_id == site_id,
    )
    if cluster_id:
        stmt = stmt.where(InternalLinkSuggestion.topic_cluster_id == cluster_id)
    result = await db.execute(stmt.order_by(InternalLinkSuggestion.anchor_relevance_score.desc()))
    return list(result.scalars().all())


@router.post("/internal-links/generate")
async def generate_internal_links(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.generate_internal_links_for_site(db, workspace_id, site_id)
    await db.commit()
    return {"suggestions_created": count}


@router.patch("/internal-links/{suggestion_id}", response_model=InternalLinkResponse)
async def approve_internal_link(
    suggestion_id: UUID,
    body: InternalLinkApprovalRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> InternalLinkSuggestion:
    user, _membership, workspace_id = ctx
    updated = await service.approve_internal_link(
        db,
        workspace_id,
        suggestion_id,
        approved=body.approved,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(updated)
    return updated
