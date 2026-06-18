"""Consultant inbox service tests."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from exposureflow_api.consultant.service import build_consultant_inbox
from exposureflow_api.models import Account, Organization, Site, TechnicalIssue, Workspace
from exposureflow_api.models.exposure import ExposureOpportunity


@pytest.mark.asyncio
async def test_consultant_inbox_lists_gsc_sitemap_issue_without_duplicate_opp(engine) -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        account = Account(name="Agency", account_type="direct")
        db.add(account)
        await db.flush()
        org = Organization(account_id=account.id, name="Org")
        db.add(org)
        await db.flush()
        workspace = Workspace(
            account_id=account.id,
            organization_id=org.id,
            name="Client WS",
            workspace_type="client",
        )
        db.add(workspace)
        await db.flush()
        site = Site(workspace_id=workspace.id, domain="client.example.com", site_name="Client")
        db.add(site)
        await db.flush()
        now = datetime.now(UTC)
        db.add(
            TechnicalIssue(
                workspace_id=workspace.id,
                site_id=site.id,
                issue_type="gsc_sitemap_unreachable",
                severity="high",
                status="open",
                source="gsc_sitemap_health",
                description="1 submitted sitemap(s) could not be fetched by Google.",
                recommended_action="Fix NEXT_PUBLIC_SITE_URL",
                evidence_json={
                    "live_diagnosis": {"root_cause": "localhost_urls"},
                    "broken_sitemaps": [{"url": "https://client.example.com/sitemap.xml", "errors": 6}],
                },
                first_seen_at=now,
                last_seen_at=now,
            )
        )
        db.add(
            ExposureOpportunity(
                workspace_id=workspace.id,
                site_id=site.id,
                opportunity_type="fix_indexability",
                priority="critical",
                status="open",
                reason="Sitemap contains localhost URLs",
                evidence_json={"rule_id": "OG-SITEMAP-002", "root_cause": "localhost_urls"},
                total_opportunity_score=50,
                ranking_feasibility_score=10,
                serp_slot_score=10,
                ai_citation_score=10,
                topic_contribution_score=10,
                zero_click_value_score=10,
            )
        )
        await db.commit()

        inbox = await build_consultant_inbox(db, workspace.id)
        titles = [i.title for i in inbox.urgent]
        assert any("GSC Sitemap" in t for t in titles)
        assert not any(i.id.startswith("opp-") for i in inbox.urgent)
        assert inbox.summary.urgent >= 1
