"""GSC sync job handler tests with mocked connector."""

import json
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from connectors.types import GscPerformanceRow as ConnectorRow
from exposureflow_api.common.crypto import encrypt_secret
from exposureflow_api.jobs.handlers.gsc_sync import run_gsc_sync
from exposureflow_api.models import (
    Account,
    IntegrationCredential,
    JobRun,
    Organization,
    Site,
    User,
    Workspace,
    WorkspaceMembership,
)


@pytest.mark.asyncio
async def test_run_gsc_sync_upserts_rows(monkeypatch, engine) -> None:
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
        user = User(email="gsc-job@example.com", name="GSC")
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
            job_type="gsc.sync",
            status="queued",
            input_json={"site_url": "sc-domain:job.example.com"},
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        class FakeClient:
            def fetch_incremental(self, _last_date):  # noqa: ANN001
                return [
                    ConnectorRow(
                        date=date(2026, 6, 1),
                        query="job query",
                        page="https://job.example.com/p",
                        country="twn",
                        device="DESKTOP",
                        impressions=10,
                        clicks=1,
                        ctr=0.1,
                        position=4.0,
                    )
                ]

        monkeypatch.setattr(
            "exposureflow_api.jobs.handlers.gsc_sync.GSCClient",
            lambda **kwargs: FakeClient(),
        )
        monkeypatch.setattr(
            "exposureflow_api.jobs.handlers.gsc_sync.OAuthTokenProvider",
            lambda payload: object(),
        )

        await run_gsc_sync(db, run)
        await db.commit()
        await db.refresh(run)

        assert run.status == "succeeded"
        assert run.output_json.get("rows_upserted") == 1

        from sqlalchemy import select

        from exposureflow_api.models import GscPerformanceRow

        result = await db.execute(
            select(GscPerformanceRow).where(GscPerformanceRow.workspace_id == workspace.id)
        )
        rows = list(result.scalars().all())
        assert len(rows) == 1
        assert rows[0].query == "job query"


@pytest.mark.asyncio
async def test_run_gsc_sync_fails_without_credential(engine) -> None:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        workspace_id = uuid4()
        site_id = uuid4()
        run = JobRun(
            workspace_id=workspace_id,
            site_id=site_id,
            job_type="gsc.sync",
            status="queued",
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        await run_gsc_sync(db, run)
        assert run.status == "failed"
        assert run.error_code == "SITE_NOT_FOUND"
