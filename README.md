# ExposureFlow

以自然曝光最大化為核心的多租戶 SaaS 作業系統。

## 產品定位

ExposureFlow 協助企業與行銷顧問管理自然曝光資產：搜尋情境覆蓋、SERP 版位、AI 搜尋引用、主題集群與執行決策，而非以文章產量為中心。

## Monorepo 結構

```text
ExposureFlow/
├── apps/
│   ├── api/          # FastAPI 後端
│   └── web/          # Next.js 前端
├── packages/
│   ├── connectors/           # 外部資料接入（GSC、SERP 等）
│   ├── exposure-core/        # 曝光核心邏輯（機會評分、主題圖）
│   ├── execution-adapters/   # 執行適配器（WordPress、ForgeBase 等）
│   ├── shared/               # Python 共用工具
│   ├── shared-types/         # TypeScript 共用型別
│   ├── ui/                   # React UI 元件
│   └── sdk/                  # API Client SDK
├── docs/             # 文件（含 product/ 策略與開發計畫）
├── infra/            # Docker、K8s、Terraform
├── scripts/          # 開發與部署腳本
└── tests/            # 跨套件整合測試
```

## 技術棧

| 層級 | 技術 |
|------|------|
| Frontend | Next.js 15、React、TypeScript、Tailwind CSS、shadcn/ui |
| Backend | Python FastAPI、SQLAlchemy 2.x、Alembic |
| Database | PostgreSQL 16、pgvector |
| Queue | Redis、Celery |
| Billing | Stripe |

## 正式環境（Linode）

子網域：`app.kakusinn.com`（HTTPS）

| 項目 | 網址 |
|------|------|
| 首頁 | https://app.kakusinn.com |
| 顧問登入 | https://app.kakusinn.com/app-entry |
| 站點管理 | https://app.kakusinn.com/app/{workspaceId}/settings/sites |
| API Health | https://app.kakusinn.com/health ✅ |
| 開發切角色 | https://app.kakusinn.com/dev/login |

部署與重啟指令見 [Linode 部署 Runbook](docs/product/linode-deploy-runbook.md)；上線 scope 見 [GTM 部署決策](docs/product/gtm-deployment-scope.md)。

**新案接入（任何目標網站）**：見 [顧問 Site Onboarding Playbook](docs/product/consultant-site-onboarding-playbook.md)。

## 快速開始

```bash
# 安裝 Node 依賴
pnpm install

# 複製環境變數
cp .env.example .env

# 啟動 API（開發中）
cd apps/api && pip install -e ".[dev]" && uvicorn exposureflow_api.main:app --reload

# 啟動 Web（開發中）
pnpm --filter @exposureflow/web dev
```

## 文件

- **[開發憲章 / Agent 最高原則](AGENTS.md)** — Phase 順序、Review+Commit 關卡、完整實作要求
- [Phase 執行紀錄](docs/product/phase-log.md)
- [Product North Star Spec](docs/product/product-north-star-spec.md)
- [KPI Taxonomy](docs/product/kpi-taxonomy.md)
- [ContentFlow 復用邊界](docs/product/contentflow-reuse-boundary.md)
- [ContentFlow 移植地圖](docs/product/contentflow-porting-map.md)
- [自然曝光 SEO 策略](docs/product/organic-impressions-seo-plan.md)
- [ExposureFlow 開發計畫](docs/product/exposureflow-development-plan.md)
- **[目標網站串接 Playbook](docs/product/consultant-site-onboarding-playbook.md)** — 每一案 client site 標準 SOP（顧問操作 + 客戶資料 + GSC）

## 授權

Proprietary — All rights reserved.
