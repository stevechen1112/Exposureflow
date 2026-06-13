from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from exposureflow_api import __version__
from exposureflow_api.config import settings

app = FastAPI(
    title="ExposureFlow API",
    description="Natural exposure maximization platform",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/api/v1/me")
async def me() -> dict[str, str]:
    """Placeholder — auth module will replace this."""
    return {"message": "ExposureFlow API skeleton"}
