"""Technical fix execution adapter."""

from __future__ import annotations

from exposureflow_api.execution.adapters.base import AdapterResult

FIX_PLAYBOOK: dict[str, dict] = {
    "noindex": {
        "summary": "Remove noindex directive from page",
        "steps": ["Remove noindex meta tag", "Verify robots.txt allows crawl", "Request re-index in GSC"],
    },
    "canonical_mismatch": {
        "summary": "Align canonical URL with preferred URL",
        "steps": ["Set canonical to target URL", "Remove conflicting alternate tags"],
    },
    "robots_blocked": {
        "summary": "Unblock URL in robots.txt",
        "steps": ["Update robots.txt disallow rules", "Validate with crawl test"],
    },
    "fix_indexability": {
        "summary": "Resolve indexability blockers",
        "steps": ["Audit HTTP status", "Fix redirect chains", "Remove noindex"],
    },
    "gsc_sitemap_unreachable": {
        "summary": "Fix GSC sitemap fetch errors",
        "steps": [
            "Fetch live /sitemap.xml and verify URLs use production domain",
            "Fix site base URL env (e.g. NEXT_PUBLIC_SITE_URL) if localhost appears",
            "Rebuild target site and verify sitemap in browser",
            "Resubmit sitemap once in GSC after fix",
        ],
    },
    "gsc_sitemap_missing": {
        "summary": "Submit sitemap to Google Search Console",
        "steps": [
            "Verify https://{domain}/sitemap.xml is reachable",
            "Submit sitemap once in GSC onboarding checklist",
        ],
    },
    "fix_ai_crawler_access": {
        "summary": "Allow approved AI crawlers per policy",
        "steps": ["Review robots.txt AI bot rules", "Apply client AI crawler policy"],
    },
}


def run_technical_fix_adapter(input_json: dict) -> AdapterResult:
    issue_type = input_json.get("issue_type") or input_json.get("opportunity_type") or "fix_indexability"
    evidence = input_json.get("evidence_json") or input_json.get("evidence") or {}
    if isinstance(evidence, dict):
        nested_issue = evidence.get("issue_type")
        if nested_issue in FIX_PLAYBOOK:
            issue_type = nested_issue
    url = input_json.get("current_url") or input_json.get("target_url")
    playbook = FIX_PLAYBOOK.get(issue_type, FIX_PLAYBOOK["fix_indexability"])
    if not url:
        return AdapterResult(success=False, output={}, error_message="URL is required")

    return AdapterResult(
        success=True,
        output={
            "adapter": "technical_fix",
            "issue_type": issue_type,
            "url": url,
            "playbook": playbook,
            "output_markdown": (
                f"# Technical fix: {issue_type}\n\n"
                f"**URL:** {url}\n\n"
                f"**Summary:** {playbook['summary']}\n\n"
                + "\n".join(f"1. {step}" for step in playbook["steps"])
                + "\n"
            ),
        },
    )
