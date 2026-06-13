# ExposureFlow API

FastAPI 後端，模組對應開發計畫第十一節 RD 規格。

## 模組

| 目錄 | 職責 |
|------|------|
| `auth/` | 認證、JWT、workspace role claim |
| `tenants/` | Account、Workspace、Site、Membership |
| `billing/` | Stripe、訂閱、配額 |
| `integrations/` | GSC、GA4、WordPress、SERP providers |
| `exposure/` | ExposureAsset、ExposureOpportunity、Dashboard |
| `serp/` | SERP snapshot、slot matrix |
| `ai_visibility/` | AI probe、citation、brand mention |
| `decision/` | ActionCandidate、Decision、Roadmap |
| `execution/` | ExecutionJob、Publisher、Publish Gate |
| `reporting/` | 月報、匯出 |
| `admin/` | Internal admin、impersonation |
| `jobs/` | Celery tasks |
| `common/` | Middleware、errors、pagination |

## 本地啟動

```bash
pip install -e ".[dev]"
uvicorn exposureflow_api.main:app --reload
```
