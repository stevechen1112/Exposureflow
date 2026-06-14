# Disaster Recovery Runbook

## Objectives

| Metric | Target |
|--------|--------|
| RPO | 1 hour (WAL PITR) |
| RTO | 4 hours (full region restore) |

## Failure Scenarios

### 1. PostgreSQL unavailable

- Fail over to read replica / restore from latest backup (see `backup-restore-runbook.md`)
- API returns 503 until DB healthy; queue jobs accumulate in Redis

### 2. Redis / Celery unavailable

- API remains read-only for cached paths; job enqueue returns `QUEUE_BACKPRESSURE` or 503
- Restart Redis cluster; drain dead letter queue after worker recovery

### 3. External provider outage (GSC, SERP, AI)

- Circuit breaker opens per provider (`GET /api/v1/ops/circuits`)
- Sync jobs fail gracefully; sanitized errors stored in `integration_sync_states`
- No cross-tenant impact; other workspaces continue

### 4. Stripe / billing webhook failure

- Billing status may lag; manual reconciliation via Stripe dashboard
- `account.billing_status` updated on webhook recovery

## Escalation

1. On-call checks `/api/v1/ops/health` and `/api/v1/ops/slo`
2. Page if job success rate < 95% for 30 minutes
3. Communicate via status page (Phase 13)

## Post-Incident

- Root cause in audit + security events
- Update runbook if gap found
- Re-run tenant isolation + billing integration tests
