"""Audit recently published live URLs for noindex and robots.txt blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

_NOINDEX_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
    re.IGNORECASE,
)

_ROBOTS_BLOG_RE = re.compile(r"Disallow:\s*/blog", re.IGNORECASE)
_ROBOTS_ROOT_RE = re.compile(r"Disallow:\s*/\s*$", re.MULTILINE)


@dataclass
class PublishedArticleIssue:
    url: str
    issue_type: str
    severity: str
    description: str
    recommended_action: str


def audit_recent_published_urls(
    site_base_url: str,
    article_urls: list[str],
    *,
    http_client: httpx.Client | None = None,
    max_articles_to_check: int = 10,
) -> list[PublishedArticleIssue]:
    """Check robots.txt and sample published article HTML for indexability blockers."""
    if not article_urls:
        return []

    client = http_client or httpx.Client(timeout=15.0, follow_redirects=True)
    issues: list[PublishedArticleIssue] = []
    base = site_base_url.rstrip("/")

    try:
        robots_resp = client.get(f"{base}/robots.txt")
        robots_text = robots_resp.text if robots_resp.status_code == 200 else ""
        if _ROBOTS_BLOG_RE.search(robots_text):
            issues.append(
                PublishedArticleIssue(
                    url=f"{base}/robots.txt",
                    issue_type="robots_blocked",
                    severity="critical",
                    description="robots.txt disallows /blog — published articles may be blocked.",
                    recommended_action="Remove or narrow Disallow: /blog in robots.txt.",
                )
            )
        if _ROBOTS_ROOT_RE.search(robots_text):
            issues.append(
                PublishedArticleIssue(
                    url=f"{base}/robots.txt",
                    issue_type="robots_blocked",
                    severity="critical",
                    description="robots.txt disallows entire site.",
                    recommended_action="Allow crawling for public blog content.",
                )
            )
    except httpx.HTTPError:
        pass

    for article_url in article_urls[:max_articles_to_check]:
        try:
            response = client.get(article_url)
        except httpx.HTTPError as exc:
            issues.append(
                PublishedArticleIssue(
                    url=article_url,
                    issue_type="not_found",
                    severity="high",
                    description=f"Unable to fetch published URL: {exc}",
                    recommended_action="Verify publish pipeline and URL routing.",
                )
            )
            continue

        if response.status_code == 404:
            issues.append(
                PublishedArticleIssue(
                    url=article_url,
                    issue_type="not_found",
                    severity="high",
                    description="Published URL returned HTTP 404.",
                    recommended_action="Re-publish or fix slug routing on target site.",
                )
            )
            continue

        if response.status_code == 200 and _NOINDEX_RE.search(response.text):
            issues.append(
                PublishedArticleIssue(
                    url=article_url,
                    issue_type="noindex",
                    severity="critical",
                    description="Published article HTML contains noindex robots meta.",
                    recommended_action="Remove noindex from article template or meta tags.",
                )
            )

    return issues
