"""Guard external provider calls with circuit breaker."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from exposureflow_api.reliability.circuit_breaker import (
    assert_provider_available,
    record_provider_failure,
    record_provider_success,
)

T = TypeVar("T")


async def call_provider(provider: str, fn: Callable[[], Awaitable[T]]) -> T:
    assert_provider_available(provider)
    try:
        result = await fn()
        record_provider_success(provider)
        return result
    except Exception:
        record_provider_failure(provider)
        raise
