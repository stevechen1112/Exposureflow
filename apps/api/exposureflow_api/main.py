from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from exposureflow_api import __version__
from exposureflow_api.config import settings
from exposureflow_api.database import async_session_factory
from exposureflow_api.tenants import service as tenant_service
from exposureflow_api.auth.router import router as auth_router
from exposureflow_api.tenants.router import router as tenants_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with async_session_factory() as session:
        await tenant_service.seed_job_definitions(session)
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

app.include_router(tenants_router)
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
