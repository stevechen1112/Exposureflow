"""Host allowlist helpers for connector-side outbound fetches."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


class UnsafeSitemapUrlError(ValueError):
    """Raised when a sitemap URL is not safe to fetch server-side."""


def normalize_site_domain(domain: str) -> str:
    raw = domain.strip().lower()
    if raw.startswith("sc-domain:"):
        raw = raw.removeprefix("sc-domain:")
    if raw.startswith("http://") or raw.startswith("https://"):
        raw = urlparse(raw).netloc.lower()
    return raw.removeprefix("www.")


def assert_sitemap_url_allowed(sitemap_url: str, expected_domain: str) -> str:
    """Ensure sitemap fetch target belongs to the managed site (SSRF mitigation)."""
    parsed = urlparse((sitemap_url or "").strip())
    if parsed.scheme not in ("https", "http"):
        raise UnsafeSitemapUrlError("Only http/https sitemap URLs are allowed.")

    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        raise UnsafeSitemapUrlError("Sitemap URL host is required.")

    blocked_hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
        "metadata.google.internal",
        "metadata",
        "169.254.169.254",
    }
    if host in blocked_hosts or host.endswith(".local"):
        raise UnsafeSitemapUrlError(f"Blocked sitemap host: {host}")

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UnsafeSitemapUrlError("Private or link-local sitemap hosts are not allowed.")
    except ValueError:
        pass

    expected = normalize_site_domain(expected_domain)
    actual = host.removeprefix("www.")
    if actual != expected:
        raise UnsafeSitemapUrlError(
            f"Sitemap host {actual!r} does not match site domain {expected!r}."
        )
    return sitemap_url.strip()
