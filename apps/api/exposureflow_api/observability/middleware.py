"""HTTP middleware for request tracing and metrics."""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from exposureflow_api.config import settings
from exposureflow_api.observability.metrics import record_request
from exposureflow_api.reliability.rate_limit import check_rate_limit

logger = logging.getLogger("exposureflow.api")

_UUID_SEGMENT = re.compile(
    r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def _client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _route_template(path: str) -> str:
    return _UUID_SEGMENT.sub("/{id}", path)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id

        client_ip = _client_ip(request)
        route = _route_template(request.url.path)

        if not request.url.path.startswith("/health"):
            check_rate_limit(key=f"ip:{client_ip}", limit=300, window_seconds=60)

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000

        record_request(
            path=route,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )
        response.headers["X-Request-Id"] = request_id

        log_record = logging.LogRecord(
            name="exposureflow.api",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"{request.method} {route} {response.status_code}",
            args=(),
            exc_info=None,
        )
        log_record.request_id = request_id
        logger.handle(log_record)
        return response
