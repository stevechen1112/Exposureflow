"""In-process metrics collector."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

_lock = Lock()
_counters: dict[str, int] = defaultdict(int)
_latency_sum_ms: dict[str, float] = defaultdict(float)
_latency_count: dict[str, int] = defaultdict(int)
_errors: int = 0
_requests: int = 0


def record_request(*, path: str, status_code: int, latency_ms: float) -> None:
    global _errors, _requests
    with _lock:
        _requests += 1
        _counters[f"http.{path}.{status_code}"] += 1
        _latency_sum_ms[path] += latency_ms
        _latency_count[path] += 1
        if status_code >= 500:
            _errors += 1


def metrics_snapshot() -> dict:
    with _lock:
        avg_latency = {}
        for path, total_ms in _latency_sum_ms.items():
            count = _latency_count[path]
            if count:
                avg_latency[path] = round(total_ms / count, 2)
        error_rate = 0.0 if _requests == 0 else round((_errors / _requests) * 100, 2)
        return {
            "http_requests_total": _requests,
            "http_error_rate_pct": error_rate,
            "http_status_counters": dict(_counters),
            "http_avg_latency_ms": avg_latency,
        }
