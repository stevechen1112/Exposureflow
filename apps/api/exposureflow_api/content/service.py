"""Content execution API service."""

from __future__ import annotations

import asyncio
import hashlib
import json
from uuid import UUID

from connectors.indexability.verifier import verify_published_url

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.execution.capacity import check_capacity, record_usage_event
from exposureflow_api.execution.claim_verifier import run_claim_verification_gate
from exposureflow_api.execution.compiler import compile_grounded_draft
from exposureflow_api.execution.compiler.content_normalizer import (
    extract_excerpt,
    infer_category,
    normalize_article_markdown,
)
from exposureflow_api.execution.publish_gate import run_publish_gate
from exposureflow_api.content import repository as content_repo
from exposureflow_api.content.repository import pipeline_params_from_brief
from exposureflow_api.common.url_safety import assert_url_host_allowed, validate_safe_http_url
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
from execution_adapters.contentflow import (
    build_publish_payload as build_contentflow_payload,
    parse_contentflow_credentials,
    publish_draft as publish_contentflow_draft,
    resolve_blog_slug_from_brief,
    slugify_keyword,
    update_post as update_contentflow_post,
)
from execution_adapters.wordpress import (
    build_post_payload,
    parse_credentials,
    publish_draft,
)

PUBLISH_PROVIDERS = ("contentflow", "wordpress")


async def get_source_pack(
    db: AsyncSession, workspace_id: UUID, source_pack_id: UUID
) -> ContentSourcePack:
    return await content_repo.get_source_pack(db, workspace_id, source_pack_id)


async def get_brief(db: AsyncSession, workspace_id: UUID, brief_id: UUID) -> ContentBrief:
    return await content_repo.get_brief(db, workspace_id, brief_id)


async def get_generation_run(
    db: AsyncSession, workspace_id: UUID, run_id: UUID
) -> ContentGenerationRun:
    return await content_repo.get_generation_run(db, workspace_id, run_id)


async def _load_brief_and_pack(
    db: AsyncSession, workspace_id: UUID, brief: ContentBrief
) -> ContentSourcePack:
    return await content_repo.load_brief_source_pack(db, workspace_id, brief)


async def create_generation_run(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    site_id: UUID,
    execution_job_id: UUID,
    content_brief_id: UUID,
    generation_mode: str,
    review_level: str,
    auto_compile: bool = False,
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
    mode = generation_mode or brief.brief_json.get("generation_mode") or "grounded_llm"
    row = ContentGenerationRun(
        workspace_id=workspace_id,
        site_id=site_id,
        execution_job_id=execution_job_id,
        content_brief_id=content_brief_id,
        generation_mode=mode,
        review_level=review_level,
        input_hash=input_hash,
        status="queued",
        provider="llm" if mode == "grounded_llm" else "grounded_template",
    )
    db.add(row)
    await db.flush()

    await record_usage_event(
        db,
        workspace_id=workspace_id,
        site_id=site_id,
        metric="content_generation_runs",
        idempotency_key=f"content-gen:{row.id}",
        provider=row.provider or "llm",
    )

    if mode == "grounded_llm":
        from exposureflow_api.execution.agents.orchestrator import run_generation_pipeline

        params = pipeline_params_from_brief(brief)
        await run_generation_pipeline(
            db,
            workspace_id,
            row.id,
            keyword=params["keyword"] or "",
            node_type=params["node_type"] or "cluster",
            intent=params["intent"],
        )
    elif auto_compile:
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


async def _get_active_site_credential(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    provider: str,
) -> IntegrationCredential:
    cred_result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.workspace_id == workspace_id,
            IntegrationCredential.site_id == site_id,
            IntegrationCredential.provider == provider,
            IntegrationCredential.status == "active",
        )
    )
    credential = cred_result.scalar_one_or_none()
    if credential is None:
        raise not_found(f"{provider} integration credential")
    return credential


async def _assert_publish_allowed(
    db: AsyncSession,
    workspace_id: UUID,
    run: ContentGenerationRun,
) -> None:
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
            message="Publish gate must pass before site publish.",
            status_code=400,
        )


async def resolve_publish_provider(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> str:
    for provider in PUBLISH_PROVIDERS:
        cred_result = await db.execute(
            select(IntegrationCredential.id)
            .where(
                IntegrationCredential.workspace_id == workspace_id,
                IntegrationCredential.site_id == site_id,
                IntegrationCredential.provider == provider,
                IntegrationCredential.status == "active",
            )
            .limit(1)
        )
        if cred_result.scalar_one_or_none() is not None:
            return provider
    raise not_found("publish integration credential")


async def publish_generation_run(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    actor_user_id: UUID,
    provider: str | None = None,
    site_status: str = "draft",
) -> dict:
    normalized_status = site_status if site_status in ("draft", "published") else "draft"
    resolved = provider or await resolve_publish_provider(
        db, workspace_id, (await get_generation_run(db, workspace_id, run_id)).site_id
    )
    if resolved == "contentflow":
        return await publish_to_contentflow(
            db,
            workspace_id,
            run_id,
            actor_user_id=actor_user_id,
            site_status=normalized_status,
        )
    if resolved == "wordpress":
        if normalized_status == "published":
            raise APIError(
                code="PUBLISH_STATUS_UNSUPPORTED",
                message="WordPress publish only supports draft push from this endpoint.",
                status_code=400,
            )
        return await publish_to_wordpress(
            db, workspace_id, run_id, actor_user_id=actor_user_id
        )
    raise APIError(
        code="PUBLISH_PROVIDER_UNSUPPORTED",
        message=f"Unsupported publish provider: {resolved}",
        status_code=400,
    )


async def publish_to_contentflow(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    actor_user_id: UUID,
    site_status: str = "draft",
) -> dict:
    run = await get_generation_run(db, workspace_id, run_id)
    is_live_update = site_status == "published" and run.status == "published"
    if not is_live_update:
        await _assert_publish_allowed(db, workspace_id, run)

    credential = await _get_active_site_credential(
        db, workspace_id, run.site_id, "contentflow"
    )
    brief = await get_brief(db, workspace_id, run.content_brief_id)
    title = brief.brief_json.get("title_hint") or "ExposureFlow Draft"
    cf_creds = parse_contentflow_credentials(decrypt_credential_payload(credential))
    validate_safe_http_url(cf_creds.site_url)

    job = await db.get(ExecutionJob, run.execution_job_id)
    prior_slug = (job.output_json or {}).get("contentflow_slug") if job else None
    existing_slug = prior_slug or resolve_blog_slug_from_brief(
        brief.brief_json,
        blog_path=cf_creds.blog_path,
    )
    slug = existing_slug or slugify_keyword(title)

    qa = run.evidence_map_json.get("qa_report", {}) if run.evidence_map_json else {}
    meta = (run.evidence_map_json or {}).get("meta", {})
    json_ld = qa.get("faq_schema_json")
    if isinstance(json_ld, dict):
        json_ld = json.dumps(json_ld, ensure_ascii=False)

    keyword = brief.brief_json.get("keyword") or brief.brief_json.get("target_keyword") or ""
    normalized_md = normalize_article_markdown(
        run.output_markdown or "",
        keyword=keyword,
        title=title,
    )
    excerpt = (
        brief.brief_json.get("description")
        or meta.get("description")
        or extract_excerpt(normalized_md, keyword=keyword)
    )
    category = brief.brief_json.get("category") or infer_category(keyword, brief.brief_type)

    payload = build_contentflow_payload(
        title=title,
        slug=slug,
        content_markdown=normalized_md,
        status=site_status,
        excerpt=excerpt,
        meta_title=meta.get("title") or brief.brief_json.get("meta_title") or title,
        meta_description=meta.get("description") or brief.brief_json.get("meta_description"),
        json_ld=json_ld if isinstance(json_ld, str) else None,
        category=category,
        content_format="markdown",
    )

    if existing_slug or is_live_update:
        update_slug = existing_slug or slug
        update_payload = {k: v for k, v in payload.items() if k != "slug"}
        result = await update_contentflow_post(cf_creds, update_slug, update_payload)
        if not existing_slug:
            existing_slug = update_slug
    else:
        result = await publish_contentflow_draft(cf_creds, payload)
        if (
            not result.success
            and result.raw_response.get("status_code") == 409
            and payload.get("slug")
        ):
            update_payload = {k: v for k, v in payload.items() if k != "slug"}
            result = await update_contentflow_post(
                cf_creds, str(payload["slug"]), update_payload
            )
            existing_slug = str(payload["slug"])

    if not result.success:
        raise APIError(
            code="CONTENTFLOW_PUBLISH_FAILED",
            message="ContentFlow publish failed.",
            status_code=502,
            details=result.raw_response,
        )

    resolved_slug = existing_slug or slug
    indexability_verify: dict | None = None
    live_published_at: str | None = None
    if site_status == "published" and result.post_url:
        from datetime import UTC, datetime

        safe_post_url = assert_url_host_allowed(result.post_url, cf_creds.site_url)
        verify_result = await asyncio.to_thread(
            verify_published_url,
            safe_post_url,
            site_base_url=cf_creds.site_url,
            check_sitemap=False,
        )
        indexability_verify = verify_result.to_dict()
        live_published_at = datetime.now(UTC).isoformat()

    if run.status != "published":
        run.status = "published"
    if job:
        job.status = "completed"
        job.output_json = {
            **(job.output_json or {}),
            "contentflow_post_id": result.post_id,
            "contentflow_post_url": result.post_url,
            "contentflow_action": result.action,
            "contentflow_slug": resolved_slug,
            "contentflow_site_status": site_status,
            **({"contentflow_live_published_at": live_published_at} if live_published_at else {}),
            **({"indexability_verify": indexability_verify} if indexability_verify else {}),
        }

    audit_action = (
        "content.generation_run.publish_contentflow_live"
        if is_live_update
        else "content.generation_run.publish_contentflow"
    )
    await record_audit(
        db,
        action=audit_action,
        target_type="content_generation_run",
        target_id=str(run_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={
            "post_id": result.post_id,
            "post_url": result.post_url,
            "action": result.action,
            "slug": resolved_slug,
        },
    )
    await record_usage_event(
        db,
        workspace_id=workspace_id,
        site_id=run.site_id,
        metric="contentflow_publish",
        idempotency_key=f"cf-publish-{'live' if is_live_update else 'draft'}:{run.id}:{site_status}",
        provider="contentflow",
    )
    await db.flush()
    response = {
        "provider": "contentflow",
        "post_id": result.post_id,
        "post_url": result.post_url,
        "status": result.status,
        "action": result.action,
        "slug": resolved_slug,
        "site_status": site_status,
    }
    if indexability_verify:
        response["indexability_verify"] = indexability_verify
        if (
            indexability_verify.get("url_reachable")
            and not indexability_verify.get("has_noindex")
        ):
            from exposureflow_api.jobs.service import enqueue_job

            await enqueue_job(
                db,
                workspace_id=workspace_id,
                job_type="topic_graph.rebuild",
                site_id=run.site_id,
                idempotency_key=f"topic-graph-post-publish:{run.id}",
            )
    return response


async def publish_to_wordpress(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    actor_user_id: UUID,
) -> dict:
    run = await get_generation_run(db, workspace_id, run_id)
    await _assert_publish_allowed(db, workspace_id, run)

    credential = await _get_active_site_credential(
        db, workspace_id, run.site_id, "wordpress"
    )

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
        "provider": "wordpress",
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
