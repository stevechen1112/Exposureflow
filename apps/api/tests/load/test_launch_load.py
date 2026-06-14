"""Load tests for launch readiness (EF-H007)."""

from __future__ import annotations

import asyncio
import time

import pytest
from httpx import ASGITransport, AsyncClient


async def _client() -> AsyncClient:
    from exposureflow_api.main import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint_load() -> None:
    async with await _client() as client:
        start = time.perf_counter()

        async def hit() -> int:
            r = await client.get("/health")
            return r.status_code

        results = await asyncio.gather(*[hit() for _ in range(50)])
        elapsed = time.perf_counter() - start
        assert all(code == 200 for code in results)
        assert elapsed < 5.0, f"50 health checks took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_launch_readiness_load(client) -> None:
    start = time.perf_counter()
    async with await _client() as ac:
        results = await asyncio.gather(*[ac.get("/api/v1/launch/readiness") for _ in range(20)])
    elapsed = time.perf_counter() - start
    assert all(r.status_code == 200 for r in results)
    assert elapsed < 15.0


@pytest.mark.asyncio
async def test_public_status_load(client) -> None:
    async with await _client() as ac:
        results = await asyncio.gather(*[ac.get("/api/v1/status") for _ in range(20)])
    assert all(r.status_code == 200 for r in results)
