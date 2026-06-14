from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.database import get_db
from exposureflow_api.observability.metrics import metrics_snapshot
from exposureflow_api.reliability.circuit_breaker import circuit_status
from exposureflow_api.reliability.slo import compute_slo_status

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


@router.get("/health")
async def ops_health(
    _ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    slo = await compute_slo_status(db)
    return {
        "status": "ok",
        "slo": slo["status"],
        "circuits": circuit_status(),
    }


@router.get("/metrics")
async def ops_metrics(
    _ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
) -> dict:
    return metrics_snapshot()


@router.get("/slo")
async def ops_slo(
    _ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await compute_slo_status(db)


@router.get("/circuits")
async def ops_circuits(
    _ctx: tuple[object, object, UUID] = Depends(require_permission("ops:read")),
) -> dict:
    return circuit_status()
