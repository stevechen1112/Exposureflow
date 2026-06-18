"""GSC sitemap health audit — detect missing or unreachable submitted sitemaps."""

from __future__ import annotations

from dataclasses import dataclass, field

from connectors.google_search_console import GSCClient


@dataclass
class GscSitemapIssue:
    issue_type: str
    severity: str
    description: str
    recommended_action: str
    evidence: dict = field(default_factory=dict)


@dataclass
class GscSitemapHealthReport:
    site_url: str
    submitted_count: int = 0
    healthy: bool = True
    issues: list[GscSitemapIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "site_url": self.site_url,
            "submitted_count": self.submitted_count,
            "healthy": self.healthy,
            "issues": [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "description": i.description,
                    "recommended_action": i.recommended_action,
                    "evidence": i.evidence,
                }
                for i in self.issues
            ],
        }


def audit_gsc_sitemap_health(client: GSCClient) -> GscSitemapHealthReport:
    """Audit GSC-submitted sitemaps for fetch errors or missing submission."""
    report = GscSitemapHealthReport(site_url=client.site_url)

    try:
        sitemaps = client.list_sitemaps()
    except Exception as exc:  # noqa: BLE001
        report.healthy = False
        report.issues.append(
            GscSitemapIssue(
                issue_type="gsc_sitemap_api_error",
                severity="high",
                description=f"Unable to list GSC sitemaps: {exc}",
                recommended_action="Verify GSC credentials and site property access.",
                evidence={"error": str(exc)},
            )
        )
        return report

    report.submitted_count = len(sitemaps)
    if not sitemaps:
        report.healthy = False
        report.issues.append(
            GscSitemapIssue(
                issue_type="gsc_sitemap_missing",
                severity="high",
                description="No sitemap submitted in Google Search Console.",
                recommended_action="Submit /sitemap.xml once in GSC (onboarding checklist).",
                evidence={"site_url": client.site_url},
            )
        )
        return report

    broken: list[dict] = []
    for sm in sitemaps:
        sm_url = sm.get("path", "")
        try:
            errors = int(sm.get("errors", 0) or 0)
        except (TypeError, ValueError):
            errors = 0
        is_pending_raw = sm.get("isPending", False)
        if isinstance(is_pending_raw, str):
            is_pending = is_pending_raw.strip().lower() == "true"
        else:
            is_pending = bool(is_pending_raw)
        if errors > 0 or (not sm.get("lastDownloaded") and not is_pending):
            broken.append({"url": sm_url, "errors": errors, "warnings": sm.get("warnings", 0)})

    if broken:
        report.healthy = False
        report.issues.append(
            GscSitemapIssue(
                issue_type="gsc_sitemap_unreachable",
                severity="high",
                description=f"{len(broken)} submitted sitemap(s) could not be fetched by Google.",
                recommended_action="Fix sitemap URL accessibility and XML validity.",
                evidence={"broken_sitemaps": broken, "total_submitted": len(sitemaps)},
            )
        )

    return report
