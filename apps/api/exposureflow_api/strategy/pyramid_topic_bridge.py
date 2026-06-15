"""Link approved Keyword Pyramid nodes to Topic Graph."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import ExposureTheme, TopicCluster, TopicNode
from exposureflow_api.models.strategy import KeywordPyramidNode
from exposureflow_api.strategy.keyword_research import infer_keyword_level


async def _get_or_create_default_theme(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> ExposureTheme:
    result = await db.execute(
        select(ExposureTheme).where(
            ExposureTheme.workspace_id == workspace_id,
            ExposureTheme.site_id == site_id,
        )
    )
    theme = result.scalar_one_or_none()
    if theme:
        return theme
    theme = ExposureTheme(
        workspace_id=workspace_id,
        site_id=site_id,
        name="Strategy pyramid themes",
        description="Linked from keyword pyramid",
    )
    db.add(theme)
    await db.flush()
    return theme


async def _resolve_cluster_for_node(
    db: AsyncSession,
    node: KeywordPyramidNode,
    theme: ExposureTheme,
) -> TopicCluster:
    if node.topic_cluster_id:
        cluster = await db.get(TopicCluster, node.topic_cluster_id)
        if cluster is not None:
            return cluster

    if node.parent_id:
        parent = await db.get(KeywordPyramidNode, node.parent_id)
        if parent and parent.topic_cluster_id:
            cluster = await db.get(TopicCluster, parent.topic_cluster_id)
            if cluster is not None:
                return cluster

    if node.node_type in ("pillar", "core"):
        cluster = TopicCluster(
            workspace_id=node.workspace_id,
            site_id=node.site_id,
            exposure_theme_id=theme.id,
            name=f"Pyramid: {node.keyword[:60]}",
            pillar_keyword=node.keyword,
            status="planned",
            metadata_json={"source": "keyword_pyramid", "pyramid_node_id": str(node.id)},
        )
        db.add(cluster)
        await db.flush()
        return cluster

    cluster = TopicCluster(
        workspace_id=node.workspace_id,
        site_id=node.site_id,
        exposure_theme_id=theme.id,
        name=f"Pyramid cluster: {node.keyword[:60]}",
        pillar_keyword=node.keyword,
        status="planned",
        metadata_json={"source": "keyword_pyramid", "pyramid_node_id": str(node.id)},
    )
    db.add(cluster)
    await db.flush()
    return cluster


async def link_pyramid_node_to_topic_graph(
    db: AsyncSession,
    node: KeywordPyramidNode,
) -> TopicNode | None:
    """Ensure topic node exists and FKs are set on pyramid node."""
    if node.business_fit_status not in ("in_scope", "needs_review"):
        return None
    if node.business_fit_status == "needs_review" and node.approved_at is None:
        return None

    theme = await _get_or_create_default_theme(db, node.workspace_id, node.site_id)
    cluster = await _resolve_cluster_for_node(db, node, theme)

    result = await db.execute(
        select(TopicNode).where(
            TopicNode.workspace_id == node.workspace_id,
            TopicNode.site_id == node.site_id,
            TopicNode.keyword == node.keyword,
        )
    )
    topic_node = result.scalar_one_or_none()
    if topic_node is None:
        topic_node = TopicNode(
            workspace_id=node.workspace_id,
            site_id=node.site_id,
            topic_cluster_id=cluster.id,
            keyword=node.keyword,
            intent=node.intent,
            keyword_level=node.keyword_level or infer_keyword_level(node.node_type),
            status="gap",
            cluster_assignment_locked=True,
            evidence_json={
                "source": "keyword_pyramid",
                "pyramid_node_id": str(node.id),
            },
        )
        db.add(topic_node)
        await db.flush()
    else:
        topic_node.cluster_assignment_locked = True
        if node.intent and not topic_node.intent:
            topic_node.intent = node.intent

    node.topic_node_id = topic_node.id
    node.topic_cluster_id = cluster.id
    if not node.keyword_level:
        node.keyword_level = infer_keyword_level(node.node_type)
    cluster.last_analyzed_at = datetime.now(UTC)
    await db.flush()
    return topic_node


async def sync_site_pyramid_links(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> dict[str, int]:
    result = await db.execute(
        select(KeywordPyramidNode).where(
            KeywordPyramidNode.workspace_id == workspace_id,
            KeywordPyramidNode.site_id == site_id,
            KeywordPyramidNode.business_fit_status == "in_scope",
        )
    )
    linked = 0
    skipped = 0
    for node in result.scalars().all():
        if node.approved_at is None:
            skipped += 1
            continue
        await link_pyramid_node_to_topic_graph(db, node)
        linked += 1
    return {"linked": linked, "skipped": skipped}
