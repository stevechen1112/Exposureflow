"""API rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from exposureflow_api.common.errors import APIError
from exposureflow_api.config import settings

_memory_buckets: dict[str, list[float]] = defaultdict(list)
_lock = Lock()
_redis_instance = None
_redis_init_failed = False


def _get_redis_client():
    global _redis_instance, _redis_init_failed
    if _redis_init_failed:
        return None
    if _redis_instance is not None:
        return _redis_instance
    try:
        import redis

        _redis_instance = redis.from_url(settings.redis_url, decode_responses=True)
        return _redis_instance
    except Exception:
        _redis_init_failed = True
        return None


def check_rate_limit(*, key: str, limit: int, window_seconds: int = 60) -> None:
    """Sliding window rate limit per key (IP or workspace)."""
    now = time.time()
    redis_client = _get_redis_client()
    if redis_client is not None:
        bucket_key = f"rl:{key}:{window_seconds}"
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(bucket_key, 0, now - window_seconds)
        pipe.zadd(bucket_key, {str(now): now})
        pipe.zcard(bucket_key)
        pipe.expire(bucket_key, window_seconds + 1)
        _, _, count, _ = pipe.execute()
        if int(count) > limit:
            raise APIError(
                code="RATE_LIMIT_EXCEEDED",
                message="Too many requests. Please retry later.",
                status_code=429,
            )
        return

    with _lock:
        timestamps = _memory_buckets[key]
        _memory_buckets[key] = [t for t in timestamps if t > now - window_seconds]
        if len(_memory_buckets[key]) >= limit:
            raise APIError(
                code="RATE_LIMIT_EXCEEDED",
                message="Too many requests. Please retry later.",
                status_code=429,
            )
        _memory_buckets[key].append(now)
