"""Content domain read helpers — shared by service and orchestrator (no circular imports)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.models.execution_content import (
    ContentBrief,
    ContentGenerationRun,
    ContentSourcePack,
)


async def get_source_pack(
    db: AsyncSession, workspace_id: UUID, source_pack_id: UUID
) -> ContentSourcePack:
    row = await db.get(ContentSourcePack, source_pack_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Content source pack")
    return row


async def get_brief(db: AsyncSession, workspace_id: UUID, brief_id: UUID) -> ContentBrief:
    row = await db.get(ContentBrief, brief_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Content brief")
    return row


async def get_generation_run(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ContentGenerationRun:
    row = await db.get(ContentGenerationRun, run_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Content generation run")
    return row


async def load_brief_source_pack(
    db: AsyncSession, workspace_id: UUID, brief: ContentBrief
) -> ContentSourcePack:
    if not brief.source_pack_id:
        raise not_found("Content source pack")
    pack = await get_source_pack(db, workspace_id, brief.source_pack_id)
    if pack.status == "needs_human_evidence":
        raise APIError(
            code="INSUFFICIENT_EVIDENCE",
            message="Source pack requires human evidence before content generation.",
            status_code=400,
        )
    return pack


def pipeline_params_from_brief(brief: ContentBrief) -> dict[str, str | None]:
    """Extract orchestrator keyword/node_type/intent from brief_json."""
    search_ctx = brief.brief_json.get("search_context") or {}
    return {
        "keyword": brief.brief_json.get("title_hint") or brief.brief_type,
        "node_type": (
            search_ctx.get("node_type")
            or brief.brief_json.get("node_type")
            or "cluster"
        ),
        "intent": search_ctx.get("intent") or brief.brief_json.get("intent"),
    }
