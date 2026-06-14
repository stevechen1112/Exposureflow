"""URL allowlist for technical SEO crawls (SSRF mitigation)."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def _normalize_host(domain: str) -> str:
    host = domain.lower().strip()
    if host.startswith("http://"):
        host = host[7:]
    elif host.startswith("https://"):
        host = host[8:]
    return host.split("/")[0].removeprefix("www.")


def is_crawl_url_allowed(url: str, site_domain: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except ValueError:
        pass

    site_host = _normalize_host(site_domain)
    host_norm = host.lower().removeprefix("www.")
    return host_norm == site_host or host_norm.endswith(f".{site_host}")


def filter_seed_urls(seed_urls: list[str], site_domain: str, *, max_urls: int = 20) -> list[str]:
    allowed: list[str] = []
    for url in seed_urls[:max_urls]:
        if is_crawl_url_allowed(url, site_domain):
            allowed.append(url)
    return allowed
