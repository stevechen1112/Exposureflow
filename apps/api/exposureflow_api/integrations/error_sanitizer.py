"""Sanitize error messages before persisting to tenant-visible fields."""

from __future__ import annotations

import re


def sanitize_sync_error(exc: Exception | str) -> str:
    message = str(exc)
    message = re.sub(r"(apikey=)[^&\s\"']+", r"\1***", message, flags=re.IGNORECASE)
    message = re.sub(r"(api_key=)[^&\s\"']+", r"\1***", message, flags=re.IGNORECASE)
    message = re.sub(r"(access_token=)[^&\s\"']+", r"\1***", message, flags=re.IGNORECASE)
    message = re.sub(r"(Authorization:\s*Bearer\s+)\S+", r"\1***", message, flags=re.IGNORECASE)
    message = re.sub(r"(X-API-KEY:\s*)\S+", r"\1***", message, flags=re.IGNORECASE)
    if len(message) > 500:
        return message[:500] + "..."
    return message
