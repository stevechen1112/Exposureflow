from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.models import Site


async def get_site_in_workspace(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> Site:
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.workspace_id == workspace_id)
    )
    site = result.scalar_one_or_none()
    if site is None:
        raise not_found("Site")
    return site
