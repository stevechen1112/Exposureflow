from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.platform import require_platform_admin
from exposureflow_api.common.audit import record_audit
from exposureflow_api.database import get_db
from exposureflow_api.ops_maintenance import service
from exposureflow_api.ops_maintenance.schemas import (
    OpsHealthRunOut,
    OpsMaintenanceLatestResponse,
    OpsMaintenanceRunRequest,
    OpsMaintenanceRunResponse,
)

router = APIRouter(prefix="/api/v1/internal/ops-maintenance", tags=["ops-maintenance"])


@router.get("/latest", response_model=OpsMaintenanceLatestResponse)
async def ops_maintenance_latest(
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> OpsMaintenanceLatestResponse:
    return await service.get_latest_ops_health(db)


@router.get("/runs", response_model=list[OpsHealthRunOut])
async def ops_maintenance_runs(
    limit: int = 30,
    _admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[OpsHealthRunOut]:
    return await service.list_ops_health_runs(db, limit=limit)


@router.post("/run", response_model=OpsMaintenanceRunResponse)
async def ops_maintenance_run(
    body: OpsMaintenanceRunRequest,
    admin: AuthContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> OpsMaintenanceRunResponse:
    result = await service.run_ops_health_manual(db, use_llm_summary=body.use_llm_summary)
    await record_audit(
        db,
        action="ops.maintenance.run",
        target_type="ops_health_run",
        target_id=str(result.run.id),
        actor_user_id=admin.user_id,
        metadata={"run_id": str(result.run.id), "status": result.run.status},
    )
    await db.commit()
    return result
