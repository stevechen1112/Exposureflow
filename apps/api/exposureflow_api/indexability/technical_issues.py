"""Shared helpers for indexability job handlers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import TechnicalIssue


async def upsert_technical_issue(
    db: AsyncSession,
    *,
    workspace_id,
    site_id,
    issue_type: str,
    severity: str,
    description: str,
    recommended_action: str,
    evidence: dict,
    url: str | None = None,
    source: str = "indexability",
    match_url: bool = True,
) -> None:
    now = datetime.now(UTC)
    stmt = select(TechnicalIssue).where(
        TechnicalIssue.workspace_id == workspace_id,
        TechnicalIssue.site_id == site_id,
        TechnicalIssue.issue_type == issue_type,
        TechnicalIssue.status == "open",
    )
    if match_url and url:
        stmt = stmt.where(TechnicalIssue.url == url)
    existing = await db.execute(stmt)
    issue = existing.scalar_one_or_none()
    if issue is None:
        db.add(
            TechnicalIssue(
                workspace_id=workspace_id,
                site_id=site_id,
                url=url,
                issue_type=issue_type,
                severity=severity,
                status="open",
                source=source,
                description=description,
                recommended_action=recommended_action,
                evidence_json=evidence,
                first_seen_at=now,
                last_seen_at=now,
            )
        )
    else:
        issue.last_seen_at = now
        issue.description = description
        issue.evidence_json = evidence
        if url:
            issue.url = url


async def resolve_open_technical_issues(
    db: AsyncSession,
    *,
    workspace_id,
    site_id,
    issue_types: list[str],
) -> int:
    """Mark matching open issues as resolved (e.g. after sitemap health passes)."""
    if not issue_types:
        return 0
    now = datetime.now(UTC)
    stmt = select(TechnicalIssue).where(
        TechnicalIssue.workspace_id == workspace_id,
        TechnicalIssue.site_id == site_id,
        TechnicalIssue.issue_type.in_(issue_types),
        TechnicalIssue.status == "open",
    )
    result = await db.execute(stmt)
    resolved = 0
    for issue in result.scalars().all():
        issue.status = "resolved"
        issue.fixed_at = now
        issue.last_seen_at = now
        resolved += 1
    if resolved:
        await db.flush()
    return resolved
