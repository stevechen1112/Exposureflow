"""Safe outbound HTTP URL validation (SSRF mitigation)."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from exposureflow_api.common.errors import APIError


def validate_safe_http_url(url: str) -> str:
    """Reject private/metadata URLs before server-side fetch."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("https", "http"):
        raise APIError(
            code="UNSAFE_URL",
            message="Only http/https URLs are allowed for ingestion.",
            status_code=400,
        )
    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        raise APIError(code="UNSAFE_URL", message="URL host is required.", status_code=400)
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise APIError(code="UNSAFE_URL", message="Local URLs are not allowed.", status_code=400)
    if host in {"metadata.google.internal", "metadata", "169.254.169.254"}:
        raise APIError(code="UNSAFE_URL", message="Metadata endpoints are not allowed.", status_code=400)

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise APIError(
            code="UNSAFE_URL",
            message="URL host could not be resolved.",
            status_code=400,
        ) from exc

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise APIError(
                code="UNSAFE_URL",
                message="Private or link-local URLs are not allowed.",
                status_code=400,
            )
    return url.strip()


def assert_url_host_allowed(url: str, allowed_site_url: str) -> str:
    """Ensure outbound fetch URL belongs to the configured managed site."""
    safe = validate_safe_http_url(url)
    target_host = (urlparse(safe).hostname or "").lower().strip(".")
    allowed_host = (urlparse(allowed_site_url.strip()).hostname or "").lower().strip(".")
    if not allowed_host:
        raise APIError(
            code="UNSAFE_URL",
            message="Managed site URL host is required.",
            status_code=400,
        )
    if target_host != allowed_host:
        raise APIError(
            code="UNSAFE_URL",
            message="Published URL host does not match managed site.",
            status_code=400,
        )
    return safe
