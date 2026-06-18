"""Indexability sitemap health job handler tests."""

import json
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from exposureflow_api.common.crypto import encrypt_secret
from exposureflow_api.jobs.handlers.indexability_sitemap_health import run_indexability_sitemap_health
from exposureflow_api.models import (
    Account,
    IntegrationCredential,
    JobRun,
    Organization,
    Site,
    TechnicalIssue,
    User,
    Workspace,
    WorkspaceMembership,
)


@pytest.mark.asyncio
async def test_run_indexability_sitemap_health_creates_issue(monkeypatch, engine) -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
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
        user = User(email="sitemap@example.com", name="Sitemap")
        db.add(user)
        await db.flush()
        db.add(WorkspaceMembership(workspace_id=workspace.id, user_id=user.id, role="owner"))
        site = Site(workspace_id=workspace.id, domain="job.example.com", site_name="Job Site")
        db.add(site)
        await db.flush()
        db.add(
            IntegrationCredential(
                workspace_id=workspace.id,
                site_id=site.id,
                provider="gsc",
                credential_type="oauth",
                encrypted_payload=encrypt_secret(json.dumps({"access_token": "tok"})),
            )
        )
        run = JobRun(
            workspace_id=workspace.id,
            site_id=site.id,
            job_type="indexability.sitemap_health",
            status="queued",
            input_json={"site_url": "sc-domain:job.example.com"},
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        class FakeClient:
            def list_sitemaps(self):
                return []

        monkeypatch.setattr(
            "exposureflow_api.jobs.handlers.indexability_sitemap_health.GSCClient",
            lambda **kwargs: FakeClient(),
        )
        monkeypatch.setattr(
            "exposureflow_api.jobs.handlers.indexability_sitemap_health.OAuthTokenProvider",
            lambda payload: object(),
        )

        await run_indexability_sitemap_health(db, run)
        await db.commit()
        await db.refresh(run)

        assert run.status == "succeeded"
        assert run.output_json.get("healthy") is False

        result = await db.execute(
            select(TechnicalIssue).where(
                TechnicalIssue.workspace_id == workspace.id,
                TechnicalIssue.issue_type == "gsc_sitemap_missing",
            )
        )
        issues = list(result.scalars().all())
        assert len(issues) == 1


@pytest.mark.asyncio
async def test_run_indexability_sitemap_health_fails_without_credential(engine) -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        workspace_id = uuid4()
        site_id = uuid4()
        run = JobRun(
            workspace_id=workspace_id,
            site_id=site_id,
            job_type="indexability.sitemap_health",
            status="queued",
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        await run_indexability_sitemap_health(db, run)
        assert run.status == "failed"
        assert run.error_code == "SITE_NOT_FOUND"
