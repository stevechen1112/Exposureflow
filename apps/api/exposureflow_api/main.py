from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from exposureflow_api import __version__
from exposureflow_api.config import settings
from exposureflow_api.database import async_session_factory
from exposureflow_api.tenants import service as tenant_service
from exposureflow_api.auth.router import router as auth_router
from exposureflow_api.competitors.router import router as competitors_router
from exposureflow_api.exposure.router import router as exposure_router
from exposureflow_api.integrations.router import router as integrations_router
from exposureflow_api.serp.router import router as serp_router
from exposureflow_api.ai_visibility.router import router as ai_visibility_router
from exposureflow_api.decision.router import router as decision_router
from exposureflow_api.strategy.router import router as strategy_router
from exposureflow_api.knowledge.router import router as knowledge_router
from exposureflow_api.execution.router import router as execution_router
from exposureflow_api.content.router import router as content_router
from exposureflow_api.content.schedule_router import router as content_schedule_router
from exposureflow_api.topics.router import router as topics_router
from exposureflow_api.tenants.router import router as tenants_router
from exposureflow_api.reporting.router import router as reporting_router
from exposureflow_api.reporting.client_router import router as client_portal_router
from exposureflow_api.billing.router import router as billing_router, webhook_router as stripe_webhook_router
from exposureflow_api.billing.service import seed_plans
from exposureflow_api.agency.router import router as agency_router
from exposureflow_api.consultant.router import router as consultant_router
from exposureflow_api.security.router import router as security_router
from exposureflow_api.internal_admin.router import router as internal_admin_router
from exposureflow_api.launch.router import internal_router as launch_internal_router
from exposureflow_api.launch.router import router as launch_router
from exposureflow_api.notifications.router import router as notifications_router
from exposureflow_api.ops_maintenance.router import router as ops_maintenance_router
from exposureflow_api.observability.logging import configure_logging
from exposureflow_api.observability.middleware import ObservabilityMiddleware
from exposureflow_api.ops.router import router as ops_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    async with async_session_factory() as session:
        await tenant_service.seed_job_definitions(session)
        await seed_plans(session)
        await tenant_service.bootstrap_platform_support(session)
        await session.commit()
    yield


app = FastAPI(
    title="ExposureFlow API",
    description="Natural exposure maximization platform",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)

app.include_router(tenants_router)
app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(exposure_router)
app.include_router(competitors_router)
app.include_router(topics_router)
app.include_router(serp_router)
app.include_router(ai_visibility_router)
app.include_router(decision_router)
app.include_router(strategy_router)
app.include_router(knowledge_router)
app.include_router(execution_router)
app.include_router(content_router)
app.include_router(content_schedule_router)
app.include_router(reporting_router)
app.include_router(client_portal_router)
app.include_router(billing_router)
app.include_router(stripe_webhook_router)
app.include_router(agency_router)
app.include_router(consultant_router)
app.include_router(security_router)
app.include_router(ops_router)
app.include_router(internal_admin_router)
app.include_router(ops_maintenance_router)
app.include_router(launch_internal_router)
app.include_router(notifications_router)
app.include_router(launch_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
