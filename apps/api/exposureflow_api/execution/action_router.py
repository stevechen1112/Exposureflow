"""Action type routing for ExposureFlow execution plane.

Maps ActionCandidate / ExposureOpportunity types to the correct execution path.
Content generation is only allowed for content-producing action types.
"""

from __future__ import annotations

import re
from typing import Any

from exposureflow_api.common.errors import APIError

# Opportunity types that produce new/updated publishable content.
CONTENT_GENERATION_ACTION_TYPES = frozenset({
    "create_page",
    "solution_page",
    "enrich",
    "add_faq",
    "schema_enhancement",
    "comparison",
    "case_study",
})

# Technical / governance actions — not content writing workflows.
NON_CONTENT_ACTION_TYPES = frozenset({
    "merge_pages",
    "refresh_page",
    "redirect_page",
    "differentiate",
    "technical_fix",
    "fix_indexability",
    "outreach",
    "no_op",
})

_OG_DIAGNOSTIC = re.compile(r"OG-\d{3}", re.I)


def is_content_generation_action(action_type: str | None) -> bool:
    return (action_type or "") in CONTENT_GENERATION_ACTION_TYPES


def assert_content_generation_eligible(action_type: str | None) -> None:
    if not is_content_generation_action(action_type):
        raise APIError(
            code="ACTION_NOT_CONTENT_ELIGIBLE",
            message=(
                f"Action type '{action_type}' is not eligible for content generation. "
                f"Use technical/SEO execution adapters instead."
            ),
            status_code=400,
        )


def extract_keyword_from_payload(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    for key in ("keyword", "target_keyword"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def extract_target_url(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    for key in ("target_url", "current_url"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def format_candidate_label(
    *,
    action_type: str,
    action_payload_json: dict[str, Any] | None = None,
    evidence_json: dict[str, Any] | None = None,
    opportunity_id: str | None = None,
) -> str:
    """Human-readable label for UI dropdowns."""
    keyword = (
        extract_keyword_from_payload(action_payload_json)
        or extract_keyword_from_payload(evidence_json)
        or (evidence_json or {}).get("reason", "")[:40]
    )
    url = extract_target_url(action_payload_json) or extract_target_url(evidence_json)
    parts: list[str] = []
    if keyword:
        parts.append(str(keyword))
    parts.append(action_type)
    if url:
        short = url.replace("https://", "").replace("http://", "")
        if len(short) > 48:
            short = short[:45] + "…"
        parts.append(short)
    elif opportunity_id:
        parts.append(opportunity_id[:8] + "…")
    return " · ".join(parts)


def is_usable_source_fact(fact_text: str | None) -> bool:
    """Filter internal diagnostic strings from publishable content."""
    if not fact_text or not str(fact_text).strip():
        return False
    text = str(fact_text).strip()
    if _OG_DIAGNOSTIC.search(text):
        return False
    if text.startswith("OG-"):
        return False
    if "Multiple URLs competing" in text:
        return False
    return True


def sanitize_source_refs(refs: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for ref in refs:
        fact = ref.get("fact_text") or ""
        if not is_usable_source_fact(fact):
            continue
        cleaned.append(ref)
    return cleaned
