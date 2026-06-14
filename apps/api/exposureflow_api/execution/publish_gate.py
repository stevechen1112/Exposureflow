"""Exposure-specific publish safety gate."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.execution_content import (
    ContentBrief,
    ContentGateResult,
    ContentGenerationRun,
    ContentSourcePack,
)


@dataclass(frozen=True)
class PublishGateFinding:
    check: str
    status: str
    message: str
    severity: str


@dataclass(frozen=True)
class PublishGateResult:
    status: str
    findings: list[PublishGateFinding]


def evaluate_publish_readiness(
    *,
    run: ContentGenerationRun,
    brief: ContentBrief,
    source_pack: ContentSourcePack,
    claim_gate: ContentGateResult | None,
    brand_forbidden_claims: list[str] | None = None,
) -> PublishGateResult:
    findings: list[PublishGateFinding] = []

    if run.status not in ("draft", "claim_verified", "approved", "publish_ready"):
        findings.append(
            PublishGateFinding(
                check="run_status",
                status="failed",
                message=f"Generation run status must be draft-ready, got {run.status}",
                severity="high",
            )
        )

    if not run.output_markdown:
        findings.append(
            PublishGateFinding(
                check="draft_present",
                status="failed",
                message="No draft markdown on generation run",
                severity="high",
            )
        )

    coverage = float(source_pack.coverage_score or 0)
    if coverage < 0.5:
        findings.append(
            PublishGateFinding(
                check="source_coverage",
                status="failed",
                message=f"Source coverage {coverage} below minimum 0.5",
                severity="high",
            )
        )
    else:
        findings.append(
            PublishGateFinding(
                check="source_coverage",
                status="passed",
                message=f"Source coverage {coverage}",
                severity="low",
            )
        )

    if claim_gate is None:
        findings.append(
            PublishGateFinding(
                check="claim_verification",
                status="failed",
                message="Claim verification gate has not been run",
                severity="high",
            )
        )
    elif claim_gate.status in ("blocked", "stale"):
        findings.append(
            PublishGateFinding(
                check="claim_verification",
                status="failed",
                message="Claim verification gate blocked or stale after re-compile",
                severity="high",
            )
        )
    else:
        findings.append(
            PublishGateFinding(
                check="claim_verification",
                status="passed",
                message="Claim verification passed",
                severity="low",
            )
        )

    forbidden = brand_forbidden_claims or brief.forbidden_claims_json or []
    draft_lower = (run.output_markdown or "").lower()
    for phrase in forbidden:
        if phrase.lower() in draft_lower:
            findings.append(
                PublishGateFinding(
                    check="brand_policy",
                    status="failed",
                    message=f"Forbidden claim phrase present: {phrase}",
                    severity="high",
                )
            )

    if brief.brief_type == "faq" and "schema:faq" not in (run.output_markdown or ""):
        findings.append(
            PublishGateFinding(
                check="schema_block",
                status="failed",
                message="FAQ content missing schema block",
                severity="medium",
            )
        )

    export_markets = brief.brief_json.get("export_markets") or []
    if export_markets and not (brief.market or source_pack.market):
        findings.append(
            PublishGateFinding(
                check="market_readiness",
                status="failed",
                message="Export market page requires target market",
                severity="high",
            )
        )

    blocked = any(f.status == "failed" and f.severity == "high" for f in findings)
    status = "blocked" if blocked else "passed"
    if not blocked and run.review_level in ("legal_review_required", "editor_review", "editor"):
        if run.status != "approved":
            status = "needs_review"
            findings.append(
                PublishGateFinding(
                    check="human_review",
                    status="pending",
                    message=f"Human review required ({run.review_level})",
                    severity="medium",
                )
            )

    return PublishGateResult(status=status, findings=findings)


async def run_publish_gate(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    execution_job_id: UUID,
    run: ContentGenerationRun,
    brief: ContentBrief,
    source_pack: ContentSourcePack,
    brand_forbidden_claims: list[str] | None = None,
) -> ContentGateResult:
    claim_result = await db.execute(
        select(ContentGateResult)
        .where(
            ContentGateResult.workspace_id == workspace_id,
            ContentGateResult.content_generation_run_id == run.id,
            ContentGateResult.gate_type == "claim_verification",
        )
        .order_by(ContentGateResult.checked_at.desc())
        .limit(1)
    )
    claim_gate = claim_result.scalar_one_or_none()

    evaluation = evaluate_publish_readiness(
        run=run,
        brief=brief,
        source_pack=source_pack,
        claim_gate=claim_gate,
        brand_forbidden_claims=brand_forbidden_claims,
    )

    gate = ContentGateResult(
        workspace_id=workspace_id,
        site_id=site_id,
        execution_job_id=execution_job_id,
        content_generation_run_id=run.id,
        gate_type="publish",
        status=evaluation.status,
        findings_json=[
            {
                "check": f.check,
                "status": f.status,
                "message": f.message,
                "severity": f.severity,
            }
            for f in evaluation.findings
        ],
    )
    db.add(gate)
    if evaluation.status == "passed":
        run.status = "publish_ready"
    elif evaluation.status == "needs_review":
        run.status = "needs_review"
    await db.flush()
    return gate
