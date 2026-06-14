# ExposureFlow API

Base URL: `https://api.exposureflow.com`（production）或 `http://localhost:8000`（local）

## Authentication

```http
Authorization: Bearer <access_token>
X-Workspace-Id: <workspace_uuid>
```

### Dev Token（僅 non-production）

```http
POST /api/v1/auth/dev-token
Content-Type: application/json

{"email": "user@example.com", "name": "User"}
```

Production 使用 Clerk JWT。

## Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/workspaces` | List workspaces |
| GET | `/api/v1/sites` | List sites |
| GET | `/api/v1/exposure/sites/{site_id}/opportunities` | Opportunities |
| GET | `/api/v1/decisions/candidates` | Action candidates |
| POST | `/api/v1/decisions/candidates/{id}/approve` | Approve candidate |
| POST | `/api/v1/integrations/gsc/sync` | Trigger GSC sync |
| GET | `/api/v1/reports` | List reports |
| POST | `/api/v1/reports/generate` | Generate report |
| GET | `/api/v1/billing/plans` | List plans |
| POST | `/api/v1/billing/checkout` | Start Stripe checkout |

## OpenAPI

FastAPI 自動文件：`/docs`（建議 production 關閉或加 IP 限制）

## SDK

TypeScript SDK：`@exposureflow/sdk`

```typescript
import { createClient } from "@exposureflow/sdk";

const client = createClient({
  baseUrl: "http://localhost:8000",
  token: "...",
  workspaceId: "...",
});
```

## Rate Limits

- API：依 plan 配額與 reliability rate limiter
- 429 表示配額用盡或 backpressure

## Support

- Help Center: `/help`
- Status: `/status` 或 `GET /api/v1/status`
