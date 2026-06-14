"""Technical SEO analyzer — robots, sitemap, page signals, AI crawler access."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import httpx

from connectors.tech_seo.url_policy import filter_seed_urls
from connectors.types import TechnicalIssueData

AI_CRAWLERS = [
    "Googlebot",
    "Bingbot",
    "OAI-SearchBot",
    "PerplexityBot",
    "GPTBot",
]

ISSUE_SEVERITY = {
    "robots_blocked": "critical",
    "noindex": "critical",
    "canonical_mismatch": "high",
    "redirect_chain": "medium",
    "not_found": "high",
    "server_error": "critical",
    "schema_error": "medium",
    "missing_sitemap": "medium",
    "sitemap_stale": "low",
    "ai_crawler_blocked": "high",
    "core_web_vitals_poor": "medium",
    "javascript_rendering_risk": "low",
}


class TechnicalSeoAnalyzer:
    def __init__(self, site_domain: str, http_client: httpx.Client | None = None) -> None:
        self.site_domain = site_domain.rstrip("/")
        if not self.site_domain.startswith("http"):
            self.site_domain = f"https://{self.site_domain}"
        self._http = http_client or httpx.Client(timeout=30.0, follow_redirects=True)

    def analyze(self, seed_urls: list[str] | None = None) -> list[TechnicalIssueData]:
        issues: list[TechnicalIssueData] = []
        issues.extend(self._check_robots_txt())
        issues.extend(self._check_sitemap())
        candidates = seed_urls or [self.site_domain]
        safe_urls = filter_seed_urls(candidates, self.site_domain) or [self.site_domain]
        for url in safe_urls:
            issues.extend(self._check_page(url))
        return issues

    def _check_robots_txt(self) -> list[TechnicalIssueData]:
        issues: list[TechnicalIssueData] = []
        robots_url = urljoin(self.site_domain, "/robots.txt")
        try:
            response = self._http.get(robots_url)
        except httpx.HTTPError as exc:
            return [
                TechnicalIssueData(
                    url=robots_url,
                    issue_type="robots_blocked",
                    severity="high",
                    description=f"Unable to fetch robots.txt: {exc}",
                    recommended_action="Ensure robots.txt is reachable.",
                    evidence={"error": str(exc)},
                )
            ]

        if response.status_code >= 400:
            issues.append(
                TechnicalIssueData(
                    url=robots_url,
                    issue_type="missing_sitemap",
                    severity="medium",
                    description=f"robots.txt returned HTTP {response.status_code}",
                    recommended_action="Publish a valid robots.txt.",
                    evidence={"status_code": response.status_code},
                )
            )
            return issues

        body = response.text
        if "Sitemap:" not in body:
            issues.append(
                TechnicalIssueData(
                    url=robots_url,
                    issue_type="missing_sitemap",
                    severity="medium",
                    description="robots.txt does not declare a sitemap.",
                    recommended_action="Add Sitemap directive to robots.txt.",
                )
            )

        for bot in AI_CRAWLERS:
            if self._is_bot_disallowed(body, bot):
                issues.append(
                    TechnicalIssueData(
                        url=robots_url,
                        issue_type="ai_crawler_blocked",
                        severity=ISSUE_SEVERITY["ai_crawler_blocked"],
                        description=f"{bot} is disallowed in robots.txt.",
                        recommended_action=f"Allow {bot} if AI visibility is a goal.",
                        evidence={"bot": bot},
                    )
                )
        return issues

    def _is_bot_disallowed(self, robots_body: str, bot: str) -> bool:
        current_agent = None
        for line in robots_body.splitlines():
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif line.lower().startswith("disallow:") and current_agent in (bot, "*"):
                path = line.split(":", 1)[1].strip()
                if path == "/":
                    return True
        return False

    def _check_sitemap(self) -> list[TechnicalIssueData]:
        issues: list[TechnicalIssueData] = []
        sitemap_url = urljoin(self.site_domain, "/sitemap.xml")
        try:
            response = self._http.get(sitemap_url)
        except httpx.HTTPError:
            return issues
        if response.status_code == 404:
            issues.append(
                TechnicalIssueData(
                    url=sitemap_url,
                    issue_type="missing_sitemap",
                    severity="medium",
                    description="sitemap.xml not found.",
                    recommended_action="Publish sitemap.xml.",
                )
            )
            return issues
        if response.status_code >= 400:
            return issues
        try:
            ElementTree.fromstring(response.text)
        except ElementTree.ParseError as exc:
            issues.append(
                TechnicalIssueData(
                    url=sitemap_url,
                    issue_type="schema_error",
                    severity="medium",
                    description="sitemap.xml is not valid XML.",
                    recommended_action="Fix sitemap XML structure.",
                    evidence={"error": str(exc)},
                )
            )
        return issues

    def _check_page(self, url: str) -> list[TechnicalIssueData]:
        issues: list[TechnicalIssueData] = []
        chain: list[str] = []
        try:
            response = self._http.get(url)
            chain.append(str(response.url))
        except httpx.HTTPError as exc:
            return [
                TechnicalIssueData(
                    url=url,
                    issue_type="server_error",
                    severity="critical",
                    description=f"Failed to fetch page: {exc}",
                    recommended_action="Fix server availability.",
                )
            ]

        if response.status_code == 404:
            issues.append(
                TechnicalIssueData(
                    url=url,
                    issue_type="not_found",
                    severity="high",
                    description="Page returns 404.",
                    recommended_action="Restore page or redirect.",
                )
            )
        if response.status_code >= 500:
            issues.append(
                TechnicalIssueData(
                    url=url,
                    issue_type="server_error",
                    severity="critical",
                    description=f"Page returns HTTP {response.status_code}.",
                    recommended_action="Fix server errors.",
                )
            )

        if len(chain) > 2 or str(response.url) != url:
            issues.append(
                TechnicalIssueData(
                    url=url,
                    issue_type="redirect_chain",
                    severity="medium",
                    description="Redirect chain detected.",
                    recommended_action="Reduce redirects to final URL.",
                    evidence={"chain": chain},
                )
            )

        html = response.text
        if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, re.I):
            issues.append(
                TechnicalIssueData(
                    url=url,
                    issue_type="noindex",
                    severity="critical",
                    description="Page has noindex meta tag.",
                    recommended_action="Remove noindex for indexable content.",
                )
            )

        canonical_match = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
            html,
            re.I,
        )
        if canonical_match:
            canonical = canonical_match.group(1)
            if urlparse(canonical).path != urlparse(str(response.url)).path:
                issues.append(
                    TechnicalIssueData(
                        url=url,
                        issue_type="canonical_mismatch",
                        severity="high",
                        description=f"Canonical points to {canonical}.",
                        recommended_action="Align canonical with preferred URL.",
                        evidence={"canonical": canonical},
                    )
                )

        if 'application/ld+json' not in html and "<html" in html.lower():
            issues.append(
                TechnicalIssueData(
                    url=url,
                    issue_type="schema_error",
                    severity="low",
                    description="No JSON-LD schema detected.",
                    recommended_action="Add structured data where appropriate.",
                )
            )

        return issues
