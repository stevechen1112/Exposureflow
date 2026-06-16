from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.exposure.schemas import CompetitorCreate, CompetitorResponse
from exposureflow_api.models import Competitor

router = APIRouter(prefix="/api/v1/competitors", tags=["competitors"])


@router.get("", response_model=list[CompetitorResponse])
async def list_competitors(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[Competitor]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(Competitor).where(
            Competitor.workspace_id == workspace_id,
            Competitor.site_id == site_id,
            Competitor.active.is_(True),
        )
    )
    return list(result.scalars().all())


@router.post("", response_model=CompetitorResponse)
async def create_competitor(
    body: CompetitorCreate,
    site_id: UUID = Query(...),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
) -> Competitor:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    # Normalize domain: strip protocol and trailing slash
    domain = body.domain.lower().strip()
    domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    # Check for duplicate
    existing = await db.execute(
        select(Competitor).where(
            Competitor.workspace_id == workspace_id,
            Competitor.site_id == site_id,
            Competitor.domain == domain,
            Competitor.active.is_(True),
        )
    )
    existing_row = existing.scalars().first()
    if existing_row:
        return existing_row
    competitor = Competitor(
        workspace_id=workspace_id,
        site_id=site_id,
        name=body.name,
        domain=domain,
        aliases_json=body.aliases,
        notes=body.notes,
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    _user, _membership, workspace_id = ctx
    competitor = await db.get(Competitor, competitor_id)
    if competitor is None or competitor.workspace_id != workspace_id:
        raise not_found("Competitor")
    competitor.active = False
    await db.commit()
    return {"status": "deleted"}
