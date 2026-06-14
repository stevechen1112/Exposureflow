# Backup and Restore Runbook

## Scope

PostgreSQL 16 database for ExposureFlow (`exposureflow` database), including tenant data, integration credentials (encrypted), job history, and billing records.

## Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Full logical backup (`pg_dump`) | Daily 03:00 UTC | 30 days |
| WAL archiving (PITR) | Continuous | 7 days |

## Backup Procedure

```bash
pg_dump -Fc -h $PGHOST -U exposureflow exposureflow > backup_$(date +%Y%m%d).dump
```

Upload artifact to object storage with workspace-agnostic encryption (SSE-KMS).

## Restore Procedure

1. Stop API and Celery workers.
2. Create fresh database or drop/recreate schema in maintenance window.
3. Restore:

```bash
pg_restore -h $PGHOST -U exposureflow -d exposureflow --clean --if-exists backup_YYYYMMDD.dump
```

4. Run Alembic to head if needed: `alembic upgrade head`
5. Verify `/health` and spot-check tenant isolation test suite.
6. Resume workers.

## Workspace-Scoped Export

Users may request GDPR export via `POST /api/v1/security/data-export` (JSON bundle per workspace). This complements full DB backup for single-tenant recovery requests.

## Verification

- Monthly restore drill to staging
- Compare row counts for `workspaces`, `sites`, `subscriptions`
- Run `pytest tests/test_tenant_isolation.py` against restored staging
