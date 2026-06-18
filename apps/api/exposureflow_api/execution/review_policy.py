"""Review policy resolution per site / industry (ContentFlow policy_resolver concept)."""

from __future__ import annotations

from dataclasses import dataclass

HIGH_COMPLIANCE_INDUSTRIES = frozenset({
    "healthcare",
    "medical",
    "pharma",
    "finance",
    "legal",
    "insurance",
})


@dataclass(frozen=True)
class ResolvedReviewPolicy:
    review_level: str
    generation_mode: str
    require_claim_gate: bool
    require_human_approval: bool
    writing_temperature: float


def resolve_review_policy(
    *,
    industry: str | None = None,
    brand_review_policy: str | None = None,
    brief_type: str = "article",
) -> ResolvedReviewPolicy:
    """Tenant/site-parameterized policy — same code path, different strictness."""
    industry_key = (industry or "").lower().strip()
    high_compliance = industry_key in HIGH_COMPLIANCE_INDUSTRIES

    review_level = brand_review_policy or "editor_review"
    if high_compliance:
        review_level = "manager_review"

    return ResolvedReviewPolicy(
        review_level=review_level,
        generation_mode="grounded_llm",
        require_claim_gate=True,
        require_human_approval=True,
        writing_temperature=0.45 if brief_type in ("comparison", "case_study") else 0.55,
    )
