# ExposureFlow SLO Definitions

| SLO | Target | Measurement |
|-----|--------|-------------|
| API availability | 99.5% monthly | 1 - (5xx / total requests) |
| Job completion | 95% success in 24h | `job_runs` status |
| Job latency P95 | < 300s | Worker metrics (Phase 12 in-process; Prometheus in production) |
| Sync freshness | GSC/GA4 < 26h stale | `integration_sync_states.last_success_at` |
| Quota enforcement | 100% blocked over-limit | Integration tests |

Status endpoint: `GET /api/v1/ops/slo` (authenticated workspace context).

Alerting thresholds (Phase 13 notifications):

- Sync failure > 3 consecutive for same site
- Billing webhook failures > 5/hour
- Job backlog > 100 queued per workspace
- Provider circuit open > 5 minutes
