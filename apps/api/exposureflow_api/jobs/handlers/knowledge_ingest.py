"""Ingest knowledge source metadata into facts — fetch page content and extract facts via OpenAI."""

from __future__ import annotations

import json
import re
from uuid import UUID

import httpx
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.config import settings
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.knowledge.service import get_source
from exposureflow_api.models import JobRun, KnowledgeFact

FACT_EXTRACTION_PROMPT = """Extract structured facts from the following web page content about a business/service.
Return a JSON array of fact objects. Each fact must have:
- fact_type: one of "product", "service", "pricing", "location", "contact", "faq", "about", "policy"
- subject: short label (e.g. "紗窗維修", "服務地區", "價格")
- fact_text: the actual factual statement (1-2 sentences, in Traditional Chinese if the source is Chinese)
- market: "tw" (Taiwan)
- language: "zh-TW"

Only extract facts that are explicitly stated in the content. Do not invent or infer.
Return ONLY the JSON array, no other text.

Content:
{content}"""


async def run_knowledge_source_ingest(db: AsyncSession, run: JobRun) -> None:
    source_id = (run.input_json or {}).get("knowledge_source_id")
    if not source_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SOURCE_ID",
            error_message="knowledge_source_id is required",
        )
        return

    try:
        source = await get_source(db, run.workspace_id, UUID(str(source_id)))
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="SOURCE_NOT_FOUND",
            error_message=str(exc),
        )
        return

    # Fetch page content
    content = ""
    if source.source_uri:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(source.source_uri, headers={
                    "User-Agent": "ExposureFlow/1.0 KnowledgeIngest",
                    "Accept": "text/html,application/xhtml+xml",
                })
                resp.raise_for_status()
                # Basic tag stripping
                text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                content = text[:8000]  # Limit to 8000 chars for API
        except Exception as fetch_err:
            await finalize_job_run(
                run,
                success=False,
                output={},
                error_code="FETCH_FAILED",
                error_message=f"Failed to fetch {source.source_uri}: {fetch_err}",
            )
            return

    if not content.strip():
        await finalize_job_run(
            run,
            success=True,
            output={"facts_created": 0, "reason": "no_content"},
        )
        return

    # Extract facts via OpenAI
    openai_api_key = settings.openai_api_key
    if not openai_api_key:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="NO_OPENAI_KEY",
            error_message="OPENAI_API_KEY not configured",
        )
        return

    try:
        client = AsyncOpenAI(api_key=openai_api_key)
        prompt = FACT_EXTRACTION_PROMPT.format(content=content)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or ""
        # Extract JSON array from response
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            facts = json.loads(json_match.group(0))
        else:
            facts = []
    except Exception as ai_err:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="AI_EXTRACTION_FAILED",
            error_message=str(ai_err),
        )
        return

    # Create fact records (auto-approved since extracted by AI from verified source)
    created = 0
    for item in facts:
        if not isinstance(item, dict):
            continue
        db.add(
            KnowledgeFact(
                workspace_id=run.workspace_id,
                site_id=source.site_id,
                knowledge_source_id=source.id,
                fact_type=str(item.get("fact_type", "product")),
                subject=str(item.get("subject", "")),
                fact_text=str(item.get("fact_text", "")),
                market=item.get("market"),
                language=item.get("language"),
                status="approved",
                metadata_json=item.get("metadata_json") or {},
            )
        )
        created += 1

    # Auto-approve the source so facts are immediately usable in Source Pack
    if source.status != "approved":
        source.status = "approved"
        db.add(source)

    await finalize_job_run(run, success=True, output={"facts_created": created})
