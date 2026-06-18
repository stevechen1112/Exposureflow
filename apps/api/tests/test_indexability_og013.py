"""OG-013 opportunity generation tests."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from exposureflow_api.exposure.service import generate_opportunities_from_indexability
from exposureflow_api.models import ExposureOpportunity


@pytest.mark.asyncio
async def test_generate_opportunities_from_indexability_creates_og013(engine) -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        from exposureflow_api.models import Account, Organization, Site, Workspace

        account = Account(name="Test", account_type="direct")
        db.add(account)
        await db.flush()
        org = Organization(account_id=account.id, name="Org")
        db.add(org)
        await db.flush()
        workspace = Workspace(
            account_id=account.id,
            organization_id=org.id,
            name="WS",
            workspace_type="client",
        )
        db.add(workspace)
        await db.flush()
        site = Site(workspace_id=workspace.id, domain="example.com", site_name="Site")
        db.add(site)
        await db.commit()

        created = await generate_opportunities_from_indexability(
            db,
            workspace.id,
            site.id,
            ["https://example.com/blog/missing"],
        )
        await db.commit()
        assert created == 1

        from sqlalchemy import select

        result = await db.execute(
            select(ExposureOpportunity).where(
                ExposureOpportunity.workspace_id == workspace.id,
                ExposureOpportunity.opportunity_type == "fix_indexability",
            )
        )
        opp = result.scalar_one()
        assert opp.current_url == "https://example.com/blog/missing"
        assert opp.evidence_json.get("rule_id") == "OG-013"


@pytest.mark.asyncio
async def test_generate_opportunities_from_indexability_dedupes(engine) -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        from exposureflow_api.models import Account, ExposureOpportunity, Organization, Site, Workspace

        account = Account(name="Test2", account_type="direct")
        db.add(account)
        await db.flush()
        org = Organization(account_id=account.id, name="Org2")
        db.add(org)
        await db.flush()
        workspace = Workspace(
            account_id=account.id,
            organization_id=org.id,
            name="WS2",
            workspace_type="client",
        )
        db.add(workspace)
        await db.flush()
        site = Site(workspace_id=workspace.id, domain="example.org", site_name="Site2")
        db.add(site)
        await db.flush()
        db.add(
            ExposureOpportunity(
                workspace_id=workspace.id,
                site_id=site.id,
                opportunity_type="fix_indexability",
                current_url="https://example.org/blog/existing",
                reason="OG-013: existing",
                status="open",
                evidence_json={"rule_id": "OG-013"},
            )
        )
        await db.commit()

        created = await generate_opportunities_from_indexability(
            db,
            workspace.id,
            site.id,
            ["https://example.org/blog/existing"],
        )
        assert created == 0
