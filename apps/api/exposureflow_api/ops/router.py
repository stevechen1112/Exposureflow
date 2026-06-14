from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.database import get_db
from exposureflow_api.reliability.circuit_breaker import circuit_status
from exposureflow_api.reliability.slo import compute_slo_status, workspace_job_metrics

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


@router.get("/health")
async def ops_health(
    ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    slo = await compute_slo_status(db, workspace_id)
    return {
        "status": "ok",
        "workspace_id": str(workspace_id),
        "slo": slo["status"],
        "circuits": circuit_status(),
    }


@router.get("/metrics")
async def ops_metrics(
    ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    return await workspace_job_metrics(db, workspace_id)


@router.get("/slo")
async def ops_slo(
    ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    return await compute_slo_status(db, workspace_id)


@router.get("/circuits")
async def ops_circuits(
    _ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
) -> dict:
    return circuit_status()
