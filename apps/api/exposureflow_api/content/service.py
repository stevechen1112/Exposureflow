"""Content execution API service."""

from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.execution.capacity import check_capacity, record_usage_event
from exposureflow_api.execution.claim_verifier import run_claim_verification_gate
from exposureflow_api.execution.compiler import compile_grounded_draft
from exposureflow_api.execution.publish_gate import run_publish_gate
from exposureflow_api.integrations.sync_helpers import decrypt_credential_payload
from exposureflow_api.knowledge.service import get_brand_profile
from exposureflow_api.models.execution_content import (
    ContentBrief,
    ContentClaim,
    ContentGateResult,
    ContentGenerationRun,
    ContentSourcePack,
    ExecutionJob,
)
from exposureflow_api.models.integrations import IntegrationCredential
from execution_adapters.wordpress import (
    build_post_payload,
    parse_credentials,
    publish_draft,
)


async def get_source_pack(
    db: AsyncSession, workspace_id: UUID, source_pack_id: UUID
) -> ContentSourcePack:
    row = await db.get(ContentSourcePack, source_pack_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Content source pack")
    return row


async def get_brief(db: AsyncSession, workspace_id: UUID, brief_id: UUID) -> ContentBrief:
    row = await db.get(ContentBrief, brief_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Content brief")
    return row


async def get_generation_run(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ContentGenerationRun:
    row = await db.get(ContentGenerationRun, run_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Content generation run")
    return row


async def _load_brief_and_pack(
    db: AsyncSession, workspace_id: UUID, brief: ContentBrief
) -> ContentSourcePack:
    if not brief.source_pack_id:
        raise not_found("Content source pack")
    pack = await get_source_pack(db, workspace_id, brief.source_pack_id)
    if pack.status == "needs_human_evidence":
        raise APIError(
            code="INSUFFICIENT_EVIDENCE",
            message="Source pack requires human evidence before content generation.",
            status_code=400,
        )
    return pack


async def create_generation_run(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    site_id: UUID,
    execution_job_id: UUID,
    content_brief_id: UUID,
    generation_mode: str,
    review_level: str,
    auto_compile: bool = True,
) -> ContentGenerationRun:
    await check_capacity(db, workspace_id, "content_generation_runs")
    brief = await get_brief(db, workspace_id, content_brief_id)
    if brief.site_id != site_id:
        raise not_found("Content brief")
    job = await db.get(ExecutionJob, execution_job_id)
    if job is None or job.workspace_id != workspace_id:
        raise not_found("Execution job")

    input_payload = {
        "brief_id": str(content_brief_id),
        "generation_mode": generation_mode,
        "brief_type": brief.brief_type,
    }
    input_hash = hashlib.sha256(repr(input_payload).encode()).hexdigest()
    row = ContentGenerationRun(
        workspace_id=workspace_id,
        site_id=site_id,
        execution_job_id=execution_job_id,
        content_brief_id=content_brief_id,
        generation_mode=generation_mode,
        review_level=review_level,
        input_hash=input_hash,
        status="queued",
        provider="grounded_template",
    )
    db.add(row)
    await db.flush()

    await record_usage_event(
        db,
        workspace_id=workspace_id,
        site_id=site_id,
        metric="content_generation_runs",
        idempotency_key=f"content-gen:{row.id}",
        provider="grounded_template",
    )

    if auto_compile:
        await compile_generation_run(db, workspace_id, row.id)

    return row


async def compile_generation_run(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ContentGenerationRun:
    run = await get_generation_run(db, workspace_id, run_id)
    brief = await get_brief(db, workspace_id, run.content_brief_id)
    pack = await _load_brief_and_pack(db, workspace_id, brief)

    result = compile_grounded_draft(
        brief,
        pack,
        generation_mode=run.generation_mode or "grounded_template",
        review_level=run.review_level,
    )
    run.output_markdown = result.markdown
    run.evidence_map_json = {
        "sections": result.evidence_map,
        "qa_report": result.qa_report,
    }
    run.provider = run.provider or "grounded_template"
    run.status = "draft"
    await db.execute(
        update(ContentGateResult)
        .where(
            ContentGateResult.workspace_id == workspace_id,
            ContentGateResult.content_generation_run_id == run.id,
            ContentGateResult.gate_type == "claim_verification",
            ContentGateResult.status == "passed",
        )
        .values(status="stale")
    )
    await db.flush()
    return run


async def verify_generation_run_claims(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ContentGateResult:
    await check_capacity(db, workspace_id, "claim_verification_runs")
    run = await get_generation_run(db, workspace_id, run_id)
    brief = await get_brief(db, workspace_id, run.content_brief_id)
    pack = await _load_brief_and_pack(db, workspace_id, brief)
    gate = await run_claim_verification_gate(
        db,
        workspace_id=workspace_id,
        site_id=run.site_id,
        execution_job_id=run.execution_job_id,
        generation_run=run,
        source_pack=pack,
        forbidden_claims=brief.forbidden_claims_json,
    )
    run.status = "claim_verified" if gate.status == "passed" else "claim_blocked"
    await record_usage_event(
        db,
        workspace_id=workspace_id,
        site_id=run.site_id,
        metric="claim_verification_runs",
        idempotency_key=f"claim-verify:{run.id}:{gate.id}",
    )
    return gate


async def check_publish_gate(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ContentGateResult:
    run = await get_generation_run(db, workspace_id, run_id)
    brief = await get_brief(db, workspace_id, run.content_brief_id)
    pack = await _load_brief_and_pack(db, workspace_id, brief)
    brand = await get_brand_profile(db, workspace_id, run.site_id)
    forbidden = list(brief.forbidden_claims_json or [])
    if brand:
        forbidden.extend(brand.compliance_policy_json.get("forbidden_claims", []))
    return await run_publish_gate(
        db,
        workspace_id=workspace_id,
        site_id=run.site_id,
        execution_job_id=run.execution_job_id,
        run=run,
        brief=brief,
        source_pack=pack,
        brand_forbidden_claims=forbidden,
    )


async def approve_generation_run(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    actor_user_id: UUID,
    rationale: str | None = None,
    override: bool = False,
) -> ContentGenerationRun:
    run = await get_generation_run(db, workspace_id, run_id)
    if run.status == "claim_blocked" and not override:
        raise APIError(
            code="CLAIM_BLOCKED",
            message="Claim verification blocked; set override=true with rationale to approve",
            status_code=400,
        )
    if run.status not in ("needs_review", "draft", "claim_verified", "claim_blocked"):
        raise APIError(
            code="INVALID_STATUS",
            message=f"Cannot approve run in status {run.status}",
            status_code=400,
        )
    run.status = "approved"
    await record_audit(
        db,
        action="content.generation_run.approve",
        target_type="content_generation_run",
        target_id=str(run_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"rationale": rationale, "override": override},
    )
    await db.flush()
    return run


async def request_changes(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    actor_user_id: UUID,
    notes: str,
) -> ContentGenerationRun:
    run = await get_generation_run(db, workspace_id, run_id)
    run.status = "needs_changes"
    qa = run.evidence_map_json.get("qa_report", {}) if run.evidence_map_json else {}
    notes_list = list(qa.get("human_review_notes", []))
    notes_list.append(notes)
    qa["human_review_notes"] = notes_list
    run.evidence_map_json = {**(run.evidence_map_json or {}), "qa_report": qa}
    await record_audit(
        db,
        action="content.generation_run.request_changes",
        target_type="content_generation_run",
        target_id=str(run_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"notes": notes},
    )
    await db.flush()
    return run


async def publish_to_wordpress(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    actor_user_id: UUID,
) -> dict:
    run = await get_generation_run(db, workspace_id, run_id)
    if run.status not in ("approved", "publish_ready"):
        raise APIError(
            code="PUBLISH_NOT_ALLOWED",
            message="Generation run must be approved or publish_ready before publishing.",
            status_code=400,
        )

    publish_gate = await db.execute(
        select(ContentGateResult)
        .where(
            ContentGateResult.workspace_id == workspace_id,
            ContentGateResult.content_generation_run_id == run.id,
            ContentGateResult.gate_type == "publish",
            ContentGateResult.status == "passed",
        )
        .limit(1)
    )
    if publish_gate.scalar_one_or_none() is None:
        raise APIError(
            code="PUBLISH_GATE_REQUIRED",
            message="Publish gate must pass before WordPress publish.",
            status_code=400,
        )

    cred_result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.workspace_id == workspace_id,
            IntegrationCredential.site_id == run.site_id,
            IntegrationCredential.provider == "wordpress",
            IntegrationCredential.status == "active",
        )
    )
    credential = cred_result.scalar_one_or_none()
    if credential is None:
        raise not_found("WordPress integration credential")

    brief = await get_brief(db, workspace_id, run.content_brief_id)
    title = brief.brief_json.get("title_hint") or "ExposureFlow Draft"
    wp_creds = parse_credentials(decrypt_credential_payload(credential))
    payload = build_post_payload(
        title=title,
        content_markdown=run.output_markdown or "",
        status="draft",
        meta_description=brief.brief_json.get("meta_description"),
        canonical_url=brief.brief_json.get("target_url"),
    )
    result = await publish_draft(wp_creds, payload)
    if not result.success:
        raise APIError(
            code="WORDPRESS_PUBLISH_FAILED",
            message="WordPress publish failed.",
            status_code=502,
            details=result.raw_response,
        )

    run.status = "published"
    job = await db.get(ExecutionJob, run.execution_job_id)
    if job:
        job.status = "completed"
        job.output_json = {
            **(job.output_json or {}),
            "wordpress_post_id": result.post_id,
            "wordpress_post_url": result.post_url,
        }

    await record_audit(
        db,
        action="content.generation_run.publish_wordpress",
        target_type="content_generation_run",
        target_id=str(run_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"post_id": result.post_id, "post_url": result.post_url},
    )
    await record_usage_event(
        db,
        workspace_id=workspace_id,
        site_id=run.site_id,
        metric="wordpress_publish",
        idempotency_key=f"wp-publish:{run.id}",
        provider="wordpress",
    )
    await db.flush()
    return {
        "post_id": result.post_id,
        "post_url": result.post_url,
        "status": result.status,
    }


async def list_gate_results(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    execution_job_id: UUID,
) -> list[ContentGateResult]:
    result = await db.execute(
        select(ContentGateResult).where(
            ContentGateResult.workspace_id == workspace_id,
            ContentGateResult.execution_job_id == execution_job_id,
        )
    )
    return list(result.scalars().all())


async def list_run_claims(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> list[ContentClaim]:
    result = await db.execute(
        select(ContentClaim).where(
            ContentClaim.workspace_id == workspace_id,
            ContentClaim.content_generation_run_id == run_id,
        )
    )
    return list(result.scalars().all())
