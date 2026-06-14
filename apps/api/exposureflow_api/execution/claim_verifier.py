"""Claim extraction and source verification gate."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.execution_content import (
    ContentClaim,
    ContentGateResult,
    ContentGenerationRun,
    ContentSourcePack,
)

CLAIM_TYPES = ("product", "data", "comparison", "case_study", "compliance")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ClaimFinding:
    claim_text: str
    claim_type: str
    verification_status: str
    severity: str
    source_refs_json: list
    finding_json: dict


def extract_claims(markdown: str) -> list[tuple[str, str]]:
    if not markdown:
        return []
    claims: list[tuple[str, str]] = []
    for sentence in SENTENCE_SPLIT.split(markdown.strip()):
        text = sentence.strip()
        if len(text) < 20:
            continue
        claim_type = "product"
        lower = text.lower()
        if any(w in lower for w in ("%", "percent", "倍", "提升", "降低")):
            claim_type = "data"
        elif any(w in lower for w in ("相比", "versus", "compared to", "better than")):
            claim_type = "comparison"
        elif any(w in lower for w in ("客戶", "案例", "customer", "case study")):
            claim_type = "case_study"
        claims.append((text, claim_type))
    return claims


def _match_sources(claim_text: str, source_refs: list[dict]) -> list[dict]:
    matched = []
    claim_lower = claim_text.lower()
    for ref in source_refs:
        fact_text = (ref.get("fact_text") or "").lower()
        subject = (ref.get("subject") or "").lower()
        if subject and subject in claim_lower:
            matched.append(ref)
        elif fact_text and any(token in fact_text for token in claim_lower.split()[:5] if len(token) > 4):
            matched.append(ref)
    return matched


def verify_claims_against_sources(
    markdown: str,
    source_refs: list[dict],
    *,
    forbidden_claims: list[str] | None = None,
) -> list[ClaimFinding]:
    findings: list[ClaimFinding] = []
    forbidden = [f.lower() for f in (forbidden_claims or [])]
    for claim_text, claim_type in extract_claims(markdown):
        if any(f in claim_text.lower() for f in forbidden):
            findings.append(
                ClaimFinding(
                    claim_text=claim_text,
                    claim_type="compliance",
                    verification_status="forbidden",
                    severity="high",
                    source_refs_json=[],
                    finding_json={"reason": "forbidden_claim_policy"},
                )
            )
            continue
        refs = _match_sources(claim_text, source_refs)
        if refs:
            findings.append(
                ClaimFinding(
                    claim_text=claim_text,
                    claim_type=claim_type,
                    verification_status="supported",
                    severity="low",
                    source_refs_json=refs,
                    finding_json={"matched_ref_count": len(refs)},
                )
            )
        else:
            findings.append(
                ClaimFinding(
                    claim_text=claim_text,
                    claim_type=claim_type,
                    verification_status="unsupported",
                    severity="high" if claim_type in ("data", "comparison", "compliance") else "medium",
                    source_refs_json=[],
                    finding_json={"reason": "no_matching_source"},
                )
            )
    return findings


async def run_claim_verification_gate(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    execution_job_id: UUID,
    generation_run: ContentGenerationRun,
    source_pack: ContentSourcePack,
    forbidden_claims: list[str] | None = None,
) -> ContentGateResult:
    markdown = generation_run.output_markdown or ""
    findings = verify_claims_against_sources(
        markdown,
        source_pack.source_refs_json or [],
        forbidden_claims=forbidden_claims,
    )
    blocked = [f for f in findings if f.verification_status in ("unsupported", "forbidden")]
    gate_status = "blocked" if blocked else "passed"

    for finding in findings:
        db.add(
            ContentClaim(
                workspace_id=workspace_id,
                site_id=site_id,
                content_generation_run_id=generation_run.id,
                claim_text=finding.claim_text,
                claim_type=finding.claim_type,
                source_refs_json=finding.source_refs_json,
                verification_status=finding.verification_status,
                severity=finding.severity,
                finding_json=finding.finding_json,
            )
        )

    gate = ContentGateResult(
        workspace_id=workspace_id,
        site_id=site_id,
        execution_job_id=execution_job_id,
        content_generation_run_id=generation_run.id,
        gate_type="claim_verification",
        status=gate_status,
        findings_json=[
            {
                "claim_text": f.claim_text,
                "claim_type": f.claim_type,
                "verification_status": f.verification_status,
                "severity": f.severity,
                "finding": f.finding_json,
            }
            for f in findings
        ],
    )
    db.add(gate)
    generation_run.unsupported_claims_json = [
        f.claim_text for f in findings if f.verification_status == "unsupported"
    ]
    await db.flush()
    return gate
