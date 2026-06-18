"""Post-publish indexability checks — HTTP, sitemap presence, noindex."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

import httpx
from xml.etree import ElementTree

_NOINDEX_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
    re.IGNORECASE,
)
_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class PostPublishIndexabilityResult:
    url: str
    checked_at: str
    http_status: int | None
    url_reachable: bool
    in_sitemap: bool | None
    has_noindex: bool
    sitemap_checked: bool
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Immediate publish gate: reachable and not noindex (sitemap checked separately)."""
        return self.url_reachable and not self.has_noindex

    def to_dict(self) -> dict:
        index_status = "indexability_warning"
        if self.ok:
            if self.sitemap_checked and self.in_sitemap is False:
                index_status = "indexability_warning"
            else:
                index_status = "pending_discovery"
        return {
            "url": self.url,
            "checked_at": self.checked_at,
            "http_status": self.http_status,
            "url_reachable": self.url_reachable,
            "in_sitemap": self.in_sitemap,
            "has_noindex": self.has_noindex,
            "sitemap_checked": self.sitemap_checked,
            "warnings": self.warnings,
            "ok": self.ok,
            "index_status": index_status,
        }


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def _collect_sitemap_locs(xml_text: str) -> tuple[list[str], list[str]]:
    """Return (page_locs, child_sitemap_locs)."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return [], []

    tag = root.tag.rsplit("}", 1)[-1]
    if tag == "sitemapindex":
        children = [
            loc.text.strip()
            for loc in root.findall("sm:sitemap/sm:loc", _SITEMAP_NS)
            if loc is not None and loc.text
        ]
        return [], children

    pages = [
        loc.text.strip()
        for loc in root.findall("sm:url/sm:loc", _SITEMAP_NS)
        if loc is not None and loc.text
    ]
    if not pages:
        pages = [
            loc.text.strip()
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if loc is not None and loc.text
        ]
    return pages, []


def _url_in_sitemap_entries(target: str, locs: list[str]) -> bool:
    normalized_target = _normalize_url(target)
    for loc in locs:
        if _normalize_url(loc) == normalized_target:
            return True
    return False


def _fetch_sitemap_locs(
    client: httpx.Client,
    sitemap_url: str,
    *,
    depth: int = 0,
    max_depth: int = 1,
) -> list[str]:
    try:
        response = client.get(sitemap_url)
    except httpx.HTTPError:
        return []
    if response.status_code >= 400:
        return []

    pages, children = _collect_sitemap_locs(response.text)
    if pages:
        return pages
    if children and depth < max_depth:
        merged: list[str] = []
        for child in children[:10]:
            merged.extend(_fetch_sitemap_locs(client, child, depth=depth + 1, max_depth=max_depth))
        return merged
    return []


def url_present_in_sitemap(
    article_url: str,
    *,
    site_base_url: str,
    http_client: httpx.Client | None = None,
) -> bool:
    client = http_client or httpx.Client(timeout=20.0, follow_redirects=True)
    sitemap_url = urljoin(site_base_url.rstrip("/") + "/", "sitemap.xml")
    locs = _fetch_sitemap_locs(client, sitemap_url)
    return _url_in_sitemap_entries(article_url, locs) if locs else False


def verify_published_url(
    article_url: str,
    *,
    site_base_url: str | None = None,
    http_client: httpx.Client | None = None,
    check_sitemap: bool = False,
) -> PostPublishIndexabilityResult:
    """Verify a newly published URL. Default: HTTP + noindex only (no sitemap race)."""
    warnings: list[str] = []
    checked_at = datetime.now(UTC).isoformat()
    client = http_client or httpx.Client(timeout=20.0, follow_redirects=True)

    http_status: int | None = None
    url_reachable = False
    has_noindex = False

    try:
        response = client.get(article_url)
        http_status = response.status_code
        url_reachable = response.status_code == 200
        if response.status_code == 200:
            has_noindex = bool(_NOINDEX_RE.search(response.text))
            if has_noindex:
                warnings.append("Page HTML contains noindex robots meta")
        elif response.status_code == 404:
            warnings.append("Published URL returned 404")
        else:
            warnings.append(f"Published URL returned HTTP {response.status_code}")
    except httpx.HTTPError as exc:
        warnings.append(f"Unable to fetch published URL: {exc}")

    in_sitemap: bool | None = None
    sitemap_checked = False
    if check_sitemap:
        sitemap_checked = True
        base = site_base_url or f"{urlparse(article_url).scheme}://{urlparse(article_url).netloc}"
        sitemap_url = urljoin(base.rstrip("/") + "/", "sitemap.xml")
        locs = _fetch_sitemap_locs(client, sitemap_url)
        in_sitemap = _url_in_sitemap_entries(article_url, locs) if locs else False
        if not locs:
            warnings.append("sitemap.xml missing, unreachable, or empty")
        elif not in_sitemap:
            warnings.append("Published URL not found in sitemap.xml")

    return PostPublishIndexabilityResult(
        url=article_url,
        checked_at=checked_at,
        http_status=http_status,
        url_reachable=url_reachable,
        in_sitemap=in_sitemap,
        has_noindex=has_noindex,
        sitemap_checked=sitemap_checked,
        warnings=warnings,
    )
