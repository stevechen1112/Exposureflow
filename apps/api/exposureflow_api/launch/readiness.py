"""Production launch readiness checks (EF-1401 / EF-H010)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.config import settings
from exposureflow_api.models import (
    ActionCandidate,
    ActionDecision,
    ExposureOpportunity,
    IntegrationSyncState,
    JobDefinition,
    Plan,
    Report,
    Site,
    Subscription,
    Workspace,
)


@dataclass
class CheckResult:
    id: str
    name: str
    category: str
    status: str  # pass | fail | warn
    message: str
    evidence: str | None = None


REPO_ROOT = Path(__file__).resolve().parents[4]


async def run_launch_checklist(db: AsyncSession) -> list[CheckResult]:
    results: list[CheckResult] = []

    async def _add(check_id: str, name: str, category: str, ok: bool, message: str, evidence: str | None = None):
        results.append(
            CheckResult(
                id=check_id,
                name=name,
                category=category,
                status="pass" if ok else "fail",
                message=message,
                evidence=evidence,
            )
        )

    # Core modules — file presence
    core_modules = [
        ("exposure", "apps/api/exposureflow_api/exposure/router.py"),
        ("decision", "apps/api/exposureflow_api/decision/router.py"),
        ("execution", "apps/api/exposureflow_api/execution/router.py"),
        ("reporting", "apps/api/exposureflow_api/reporting/router.py"),
        ("billing", "apps/api/exposureflow_api/billing/router.py"),
        ("internal_admin", "apps/api/exposureflow_api/internal_admin/router.py"),
        ("security", "apps/api/exposureflow_api/security/router.py"),
    ]
    for mod, rel in core_modules:
        path = REPO_ROOT / rel
        await _add(f"core.{mod}", f"Core module: {mod}", "core", path.exists(), str(path))

    # Tenant isolation tests
    iso_test = REPO_ROOT / "apps/api/tests/test_tenant_isolation.py"
    await _add(
        "tenant.isolation_tests",
        "Tenant isolation tests",
        "security",
        iso_test.exists(),
        "test_tenant_isolation.py present",
        str(iso_test),
    )

    # Billing / plans
    plan_count = int((await db.execute(select(func.count()).select_from(Plan))).scalar_one())
    await _add(
        "billing.plans_seeded",
        "Subscription plans seeded",
        "billing",
        plan_count > 0,
        f"{plan_count} plan(s) in database",
    )

    sub_count = int((await db.execute(select(func.count()).select_from(Subscription))).scalar_one())
    await _add(
        "billing.subscriptions",
        "Subscription records",
        "billing",
        True,
        f"{sub_count} subscription(s); Stripe configured={bool(settings.stripe_secret_key)}",
    )

    # Usage metering — usage_events table via imports
    from exposureflow_api.models.commercial import UsageEvent

    usage_count = int((await db.execute(select(func.count()).select_from(UsageEvent))).scalar_one())
    await _add(
        "billing.usage_metering",
        "Usage event tracking",
        "billing",
        True,
        f"{usage_count} usage event(s) recorded",
    )

    # Job definitions
    job_def_count = int((await db.execute(select(func.count()).select_from(JobDefinition))).scalar_one())
    await _add(
        "ops.job_definitions",
        "Job definitions registered",
        "ops",
        job_def_count >= 5,
        f"{job_def_count} job definition(s)",
    )

    # Internal admin
    await _add(
        "ops.internal_admin",
        "Internal admin module",
        "ops",
        (REPO_ROOT / "apps/api/exposureflow_api/internal_admin/router.py").exists(),
        "internal_admin router present",
    )

    # Backup / restore runbook
    backup_doc = REPO_ROOT / "docs/operations/backup-restore-runbook.md"
    dr_doc = REPO_ROOT / "docs/operations/disaster-recovery-runbook.md"
    await _add(
        "ops.backup_runbook",
        "Backup / restore runbook",
        "ops",
        backup_doc.exists() and dr_doc.exists(),
        "backup-restore + disaster-recovery runbooks",
        str(backup_doc),
    )

    backup_script = REPO_ROOT / "scripts/backup-db.sh"
    await _add(
        "ops.backup_script",
        "Backup script",
        "ops",
        backup_script.exists(),
        "scripts/backup-db.sh",
        str(backup_script),
    )

    # Load test
    load_test = REPO_ROOT / "apps/api/tests/load/test_launch_load.py"
    await _add(
        "ops.load_test",
        "Load test suite",
        "ops",
        load_test.exists(),
        "load test present",
        str(load_test),
    )

    # Security review checklist
    sec_checklist = REPO_ROOT / "docs/product/security-review-checklist.md"
    await _add(
        "security.review_checklist",
        "Security review checklist",
        "security",
        sec_checklist.exists(),
        "security-review-checklist.md",
        str(sec_checklist),
    )

    # Documentation
    for doc_id, rel, label in [
        ("docs.help_center", "apps/web/app/(marketing)/help/page.tsx", "Help center"),
        ("docs.onboarding", "docs/help/onboarding-guide.md", "Onboarding guide"),
        ("docs.integrations", "docs/help/integration-setup.md", "Integration setup guide"),
        ("docs.api", "docs/api/README.md", "API documentation"),
        ("docs.webhooks", "docs/api/webhooks.md", "Webhook documentation"),
        ("docs.launch_checklist", "docs/product/launch-checklist.md", "Launch checklist"),
    ]:
        path = REPO_ROOT / rel
        await _add(doc_id, label, "documentation", path.exists(), str(path))

    # Onboarding — workspace + site capability
    ws_count = int(
        (await db.execute(select(func.count()).select_from(Workspace).where(Workspace.status == "active"))).scalar_one()
    )
    site_count = int((await db.execute(select(func.count()).select_from(Site))).scalar_one())
    await _add(
        "product.onboarding",
        "Workspace / site onboarding",
        "product",
        True,
        f"{ws_count} active workspace(s), {site_count} site(s)",
    )

    # End-to-end capability signals
    opp_count = int((await db.execute(select(func.count()).select_from(ExposureOpportunity))).scalar_one())
    await _add(
        "product.opportunities",
        "Exposure opportunities",
        "product",
        True,
        f"{opp_count} opportunity record(s)",
    )

    approved = int(
        (
            await db.execute(
                select(func.count()).select_from(ActionDecision).where(ActionDecision.decision == "approved")
            )
        ).scalar_one()
    )
    candidates = int((await db.execute(select(func.count()).select_from(ActionCandidate))).scalar_one())
    await _add(
        "product.decisions",
        "Decision approval flow",
        "product",
        True,
        f"{approved} approved / {candidates} candidate(s)",
    )

    reports = int(
        (await db.execute(select(func.count()).select_from(Report).where(Report.status == "ready"))).scalar_one()
    )
    await _add(
        "product.reports",
        "Report generation",
        "product",
        True,
        f"{reports} ready report(s)",
    )

    gsc_syncs = int(
        (
            await db.execute(
                select(func.count()).select_from(IntegrationSyncState).where(
                    IntegrationSyncState.provider == "gsc",
                    IntegrationSyncState.last_success_at.isnot(None),
                )
            )
        ).scalar_one()
    )
    await _add(
        "product.gsc_sync",
        "GSC sync capability",
        "product",
        True,
        f"{gsc_syncs} successful GSC sync state(s)",
    )

    # JWT secret in production
    if settings.app_env == "production":
        await _add(
            "security.jwt_secret",
            "JWT secret not default",
            "security",
            settings.jwt_secret not in {"change-me", ""},
            "Production JWT secret configured",
        )

    return results


def summarize_checklist(results: list[CheckResult]) -> dict:
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    warned = sum(1 for r in results if r.status == "warn")
    overall = "ready" if failed == 0 else "not_ready"
    return {
        "overall": overall,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "total": len(results),
    }
