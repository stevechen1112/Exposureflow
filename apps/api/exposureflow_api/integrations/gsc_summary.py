"""GSC ingested data summary for integrations UI."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import GscPerformanceRow


async def get_gsc_data_summary(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    top_queries_limit: int = 5,
) -> dict:
    base = (
        GscPerformanceRow.workspace_id == workspace_id,
        GscPerformanceRow.site_id == site_id,
    )

    total_rows = int(
        (
            await db.execute(
                select(func.count()).select_from(GscPerformanceRow).where(*base)
            )
        ).scalar_one()
    )

    distinct_queries = int(
        (
            await db.execute(
                select(func.count(func.distinct(GscPerformanceRow.query))).where(*base)
            )
        ).scalar_one()
    )

    distinct_pages = int(
        (
            await db.execute(
                select(func.count(func.distinct(GscPerformanceRow.page))).where(*base)
            )
        ).scalar_one()
    )

    date_bounds = (
        await db.execute(
            select(
                func.min(GscPerformanceRow.date),
                func.max(GscPerformanceRow.date),
            ).where(*base)
        )
    ).one()

    top_stmt = (
        select(
            GscPerformanceRow.query,
            func.sum(GscPerformanceRow.impressions).label("impressions"),
            func.sum(GscPerformanceRow.clicks).label("clicks"),
            func.avg(GscPerformanceRow.position).label("position"),
        )
        .where(*base)
        .group_by(GscPerformanceRow.query)
        .order_by(func.sum(GscPerformanceRow.impressions).desc())
        .limit(top_queries_limit)
    )
    top_rows = (await db.execute(top_stmt)).all()

    return {
        "total_rows": total_rows,
        "distinct_queries": distinct_queries,
        "distinct_pages": distinct_pages,
        "earliest_date": date_bounds[0],
        "latest_date": date_bounds[1],
        "top_queries": [
            {
                "query": row.query,
                "impressions": int(row.impressions or 0),
                "clicks": int(row.clicks or 0),
                "position": float(row.position or 0),
            }
            for row in top_rows
        ],
    }
