"""Merge pages execution adapter — cannibalization consolidation plan."""

from __future__ import annotations

from exposureflow_api.execution.adapters.base import AdapterResult


def run_merge_pages_adapter(input_json: dict) -> AdapterResult:
    canonical_url = (
        input_json.get("canonical_url")
        or input_json.get("target_url")
        or input_json.get("current_url")
    )
    keyword = input_json.get("keyword") or input_json.get("target_keyword")
    competing_urls = input_json.get("urls") or input_json.get("merge_urls") or []

    if not canonical_url:
        return AdapterResult(success=False, output={}, error_message="canonical_url is required")
    if not competing_urls:
        current = input_json.get("current_url")
        if current and current != canonical_url:
            competing_urls = [current]
        else:
            return AdapterResult(success=False, output={}, error_message="urls to merge are required")

    unique_urls = []
    seen: set[str] = set()
    for url in competing_urls:
        if isinstance(url, str) and url and url not in seen:
            seen.add(url)
            unique_urls.append(url)

    steps = [
        {
            "step": "select_canonical",
            "url": canonical_url,
            "rationale": "Primary URL retained for consolidated ranking signals",
        },
        {
            "step": "301_redirect",
            "from_urls": [u for u in unique_urls if u != canonical_url],
            "to_url": canonical_url,
            "rationale": "Consolidate duplicate URLs competing for the same query",
        },
        {
            "step": "update_internal_links",
            "rationale": "Point inlinks to canonical URL after redirect deployment",
        },
    ]

    markdown_lines = [
        f"# Merge pages plan: {keyword or 'cannibalization fix'}",
        "",
        f"**Canonical URL:** {canonical_url}",
        "",
        "## Competing URLs",
    ]
    for url in unique_urls:
        markdown_lines.append(f"- {url}")
    markdown_lines.extend(["", "## Recommended steps"])
    for step in steps:
        markdown_lines.append(f"- {step['step']}: {step.get('rationale', '')}")

    return AdapterResult(
        success=True,
        output={
            "adapter": "merge_pages",
            "keyword": keyword,
            "canonical_url": canonical_url,
            "competing_urls": unique_urls,
            "steps": steps,
            "output_markdown": "\n".join(markdown_lines) + "\n",
        },
    )
