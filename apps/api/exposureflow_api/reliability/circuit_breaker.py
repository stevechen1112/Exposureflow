"""Per-provider circuit breaker."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

from exposureflow_api.common.errors import APIError

FAILURE_THRESHOLD = 5
OPEN_SECONDS = 60


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


_states: dict[str, CircuitState] = defaultdict(CircuitState)
_lock = Lock()


def record_provider_success(provider: str) -> None:
    with _lock:
        _states[provider] = CircuitState()


def record_provider_failure(provider: str) -> None:
    with _lock:
        state = _states[provider]
        state.failures += 1
        if state.failures >= FAILURE_THRESHOLD:
            state.opened_at = time.time()


def assert_provider_available(provider: str) -> None:
    with _lock:
        state = _states.get(provider)
        if state is None or state.opened_at is None:
            return
        if time.time() - state.opened_at >= OPEN_SECONDS:
            _states[provider] = CircuitState()
            return
        raise APIError(
            code="PROVIDER_CIRCUIT_OPEN",
            message=f"Provider {provider} is temporarily unavailable.",
            status_code=503,
            details={"provider": provider, "retry_after_seconds": OPEN_SECONDS},
        )


def circuit_status() -> dict[str, dict]:
    with _lock:
        now = time.time()
        return {
            provider: {
                "failures": s.failures,
                "open": s.opened_at is not None and now - s.opened_at < OPEN_SECONDS,
            }
            for provider, s in _states.items()
        }
