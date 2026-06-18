"""Validate integration credential payloads before storage or outbound use."""

from __future__ import annotations

import json

from exposureflow_api.common.errors import APIError
from exposureflow_api.common.url_safety import validate_safe_http_url


def validate_contentflow_site_url(site_url: str) -> str:
    normalized = str(site_url or "").strip().rstrip("/")
    if not normalized:
        raise APIError(
            code="INVALID_CREDENTIAL",
            message="ContentFlow credential requires site_url.",
            status_code=400,
        )
    return validate_safe_http_url(normalized)


def validate_integration_payload(provider: str, payload: str) -> None:
    normalized_provider = (provider or "").strip().lower()
    if normalized_provider != "contentflow":
        return

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise APIError(
            code="INVALID_CREDENTIAL",
            message="ContentFlow credential payload must be valid JSON.",
            status_code=400,
        ) from exc

    if not isinstance(data, dict):
        raise APIError(
            code="INVALID_CREDENTIAL",
            message="ContentFlow credential payload must be a JSON object.",
            status_code=400,
        )

    validate_contentflow_site_url(str(data.get("site_url") or ""))
    secret = str(data.get("secret") or "").strip()
    if not secret:
        raise APIError(
            code="INVALID_CREDENTIAL",
            message="ContentFlow credential requires secret.",
            status_code=400,
        )
