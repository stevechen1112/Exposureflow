"""Live sitemap root-cause diagnosis when GSC reports fetch errors."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx

from connectors.indexability.url_allowlist import UnsafeSitemapUrlError, assert_sitemap_url_allowed, normalize_site_domain

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
_LOCALHOST_RE = re.compile(r"localhost|127\.0\.0\.1", re.IGNORECASE)
_MAX_SAMPLE_LOCS = 50


@dataclass
class LiveSitemapDiagnosis:
    sitemap_url: str
    expected_domain: str
    fetch_ok: bool
    http_status: int | None
    root_cause: str | None
    sample_bad_urls: list[str] = field(default_factory=list)
    recommended_action: str = ""
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "sitemap_url": self.sitemap_url,
            "expected_domain": self.expected_domain,
            "fetch_ok": self.fetch_ok,
            "http_status": self.http_status,
            "root_cause": self.root_cause,
            "sample_bad_urls": self.sample_bad_urls,
            "recommended_action": self.recommended_action,
            "evidence": self.evidence,
        }


def _normalize_domain(domain: str) -> str:
    return normalize_site_domain(domain)


def _collect_locs(xml_text: str, expected_domain: str) -> list[str]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []

    tag = root.tag.rsplit("}", 1)[-1]
    if tag == "sitemapindex":
        child_urls = [
            loc.text.strip()
            for loc in root.findall("sm:sitemap/sm:loc", _SITEMAP_NS)
            if loc is not None and loc.text
        ]
        locs: list[str] = []
        for child_url in child_urls[:5]:
            locs.extend(_fetch_child_sitemap_locs(child_url, expected_domain))
        return locs[:_MAX_SAMPLE_LOCS]

    return [
        loc.text.strip()
        for loc in root.findall("sm:url/sm:loc", _SITEMAP_NS)
        if loc is not None and loc.text
    ][: _MAX_SAMPLE_LOCS]


def _fetch_child_sitemap_locs(url: str, expected_domain: str) -> list[str]:
    try:
        safe_url = assert_sitemap_url_allowed(url, expected_domain)
    except UnsafeSitemapUrlError:
        return []
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(safe_url)
        if resp.status_code >= 400:
            return []
        return [
            loc.text.strip()
            for loc in ElementTree.fromstring(resp.text).findall("sm:url/sm:loc", _SITEMAP_NS)
            if loc is not None and loc.text
        ][: _MAX_SAMPLE_LOCS]
    except Exception:  # noqa: BLE001
        return []


def _classify_loc(loc: str, expected_domain: str) -> str | None:
    parsed = urlparse(loc.strip())
    netloc = parsed.netloc.lower().removeprefix("www.")
    if not netloc:
        return "invalid_url"
    if _LOCALHOST_RE.search(netloc) or _LOCALHOST_RE.search(loc):
        return "localhost_urls"
    if netloc != expected_domain:
        return "wrong_domain"
    return None


def diagnose_live_sitemap(
    sitemap_url: str,
    expected_domain: str,
    *,
    http_client: httpx.Client | None = None,
) -> LiveSitemapDiagnosis:
    """Fetch live sitemap and infer why GSC may report errors."""
    domain = _normalize_domain(expected_domain)
    diagnosis = LiveSitemapDiagnosis(
        sitemap_url=sitemap_url,
        expected_domain=domain,
        fetch_ok=False,
        http_status=None,
        root_cause=None,
    )

    try:
        safe_url = assert_sitemap_url_allowed(sitemap_url, domain)
    except UnsafeSitemapUrlError as exc:
        diagnosis.root_cause = "unsafe_url"
        diagnosis.recommended_action = "Sitemap URL host does not match site domain."
        diagnosis.evidence = {"error": str(exc)}
        return diagnosis

    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=15.0, follow_redirects=True)
    try:
        resp = client.get(safe_url)
        diagnosis.http_status = resp.status_code
        if resp.status_code >= 400:
            diagnosis.root_cause = "fetch_failed"
            diagnosis.recommended_action = (
                f"Ensure {sitemap_url} returns HTTP 200 and is publicly reachable."
            )
            diagnosis.evidence = {"error": f"HTTP {resp.status_code}"}
            return diagnosis

        diagnosis.fetch_ok = True
        locs = _collect_locs(resp.text, domain)
        if not locs:
            diagnosis.root_cause = "xml_invalid_or_empty"
            diagnosis.recommended_action = (
                "Validate sitemap XML structure and ensure at least one <loc> entry."
            )
            diagnosis.evidence = {"loc_count": 0}
            return diagnosis

        bad_by_cause: dict[str, list[str]] = {}
        for loc in locs:
            cause = _classify_loc(loc, domain)
            if cause:
                bad_by_cause.setdefault(cause, []).append(loc)

        if bad_by_cause:
            root_cause = "localhost_urls" if "localhost_urls" in bad_by_cause else next(iter(bad_by_cause))
            diagnosis.root_cause = root_cause
            diagnosis.sample_bad_urls = bad_by_cause[root_cause][:5]
            if root_cause == "localhost_urls":
                diagnosis.recommended_action = (
                    "Fix site base URL env (e.g. NEXT_PUBLIC_SITE_URL) on the target site, "
                    "rebuild, then resubmit sitemap in GSC once."
                )
            elif root_cause == "wrong_domain":
                diagnosis.recommended_action = (
                    f"Ensure sitemap URLs use https://{domain}/ — check CMS or build-time site URL config."
                )
            else:
                diagnosis.recommended_action = "Fix invalid URLs in sitemap generation."
            diagnosis.evidence = {
                "loc_count": len(locs),
                "bad_counts": {k: len(v) for k, v in bad_by_cause.items()},
            }
            return diagnosis

        diagnosis.root_cause = "content_ok_gsc_stale"
        diagnosis.recommended_action = (
            "Live sitemap looks valid. Wait for Google to re-fetch, or resubmit sitemap once in GSC."
        )
        diagnosis.evidence = {"loc_count": len(locs), "sample_ok": locs[:3]}
        return diagnosis
    except Exception as exc:  # noqa: BLE001
        diagnosis.root_cause = "fetch_failed"
        diagnosis.recommended_action = f"Ensure {sitemap_url} is reachable from the public internet."
        diagnosis.evidence = {"error": str(exc)}
        return diagnosis
    finally:
        if owns_client:
            client.close()
