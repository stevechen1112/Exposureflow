from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.platform import require_platform_admin
from exposureflow_api.business_metrics.service import compute_business_metrics
from exposureflow_api.database import get_db
from exposureflow_api.launch.readiness import run_launch_checklist, summarize_checklist
from exposureflow_api.launch.schemas import LaunchCheckItem, LaunchChecklistResponse

router = APIRouter(prefix="/api/v1/launch", tags=["launch"])
internal_router = APIRouter(prefix="/api/v1/internal", tags=["launch"])


@router.get("/readiness", response_model=LaunchChecklistResponse)
async def public_launch_readiness(db: AsyncSession = Depends(get_db)) -> LaunchChecklistResponse:
    """Public readiness summary for status / monitoring (no secrets)."""
    results = await run_launch_checklist(db)
    summary = summarize_checklist(results)
    # Public endpoint omits file paths in evidence for failed checks
    checks = [
        LaunchCheckItem(
            id=r.id,
            name=r.name,
            category=r.category,
            status=r.status,
            message=r.message,
            evidence=None,
        )
        for r in results
    ]
    return LaunchChecklistResponse(checks=checks, **summary)


@internal_router.get("/launch/checklist", response_model=LaunchChecklistResponse)
async def internal_launch_checklist(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> LaunchChecklistResponse:
    results = await run_launch_checklist(db)
    summary = summarize_checklist(results)
    checks = [LaunchCheckItem(**r.__dict__) for r in results]
    return LaunchChecklistResponse(checks=checks, **summary)


@internal_router.get("/business-metrics")
async def internal_business_metrics(
    days: int = 30,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await compute_business_metrics(db, days=days)
