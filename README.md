# ExposureFlow

ExposureFlow 是以「自然曝光最大化」為核心的多租戶顧問作業系統。它不是單純的文章生產工具，而是把 **GSC / SERP / AI 搜尋引用 / Topic Graph / 關鍵字金字塔 / 內容 pipeline / 顧問待辦** 串成一條顧問可交付、可追蹤、可部署的營運流程。

目前產品採 **Consultant-Led GTM**：SEO 顧問或代理商使用後台代客戶操作；終端客戶現階段不自助註冊、不自行連 GSC、不走 Stripe 自助結帳。正式 scope 以 [`docs/product/gtm-deployment-scope.md`](docs/product/gtm-deployment-scope.md) 為準。

## 現況總覽

| 項目 | 狀態 |
|------|------|
| Production | `https://app.kakusinn.com` on Linode |
| 主要使用者 | SEO 顧問 / 代理商團隊 |
| 主要租戶模型 | Account → Workspace（client）→ Site |
| 資料來源 | Google Search Console、SERP、站內 sitemap / published URL audit |
| AI / Agent | 內容 pipeline、知識抽取、SEO QA、後續維護工程師規格 |
| 人工關卡 | 決策核准、內容核准、發布、關鍵字核准、客戶站修復 |
| 部署型態 | Docker Compose：API、Web、Worker、Beat、Postgres(pgvector)、Redis、Caddy |

## 核心能力

### 1. 顧問多租戶工作台

- Workspace Switcher：在不同 client workspace 間切換。
- Site Switcher：在同一客戶的多個 site 間切換。
- Consultant Inbox：跨站點 / 跨客戶彙總待辦。
- Agency Dashboard：跨客戶 KPI、待辦數、主站點、快速進入工作台。
- 待辦分桶：
  - **待處理**：高優先且阻擋曝光、發布、同步或決策的項目。
  - **進行中**：已立案或已啟動的路線圖項目。
  - **策略待辦**：覆蓋缺口、關鍵字核准、開放機會等長期規劃。
- 每個 inbox item 會附上「顧問怎麼做」的白話行動指引。

### 2. Indexability 閉環

- GSC sitemap health job 自動檢查 sitemap 提交 / 抓取狀態。
- Live sitemap diagnosis 可辨識 localhost URL、錯誤網域、XML 無效、抓取失敗等 root cause。
- TechnicalIssue + ExposureOpportunity + ActionCandidate 自動生成。
- 健康恢復時自動 resolve sitemap technical issues / opportunities。
- Published URL audit 檢查 404、noindex、robots / sitemap discovery 風險。
- URL safety / allowlist 保護，避免 SSRF 與跨網域抓取。

### 3. 內容與 AI Pipeline

- Content Brief → Source Pack → 7-agent pipeline：
  - research
  - strategy
  - writing
  - SEO check
  - SEO QA fixes
  - claim gate
  - normalized article output
- `gpt-4o-mini` 為主要 LLM；Gemini 可作備援設計。
- Review policy 預設要求 human approval。
- ContentFlow / WordPress publish adapter。
- ContentFlow live publish 成功且 indexability verify 通過後，會 enqueue topic graph rebuild，讓已覆蓋的 topic gap 後續可自動移出策略待辦。

### 4. 關鍵字、Topic 與自然曝光

- 關鍵字金字塔支援 business scope、fit status、核准流程。
- Topic Graph 從 GSC query / page 聚合建立 clusters 與 nodes。
- Topic gap 代表「有搜尋需求但站內尚未覆蓋」。
- Exposure Opportunity 將 GSC、SERP、indexability、AI visibility signal 轉成可決策的機會。
- Decision Plane 讓顧問核准 / 拒絕 ActionCandidate，再進入 roadmap 或內容排程。

### 5. Production 運維與維護工程師規格

- 目前已有 `/health`、launch readiness、internal admin、integration health、Celery beat / worker。
- 已新增完整規格文件：[`docs/product/ops-maintenance-agent-implementation-plan.md`](docs/product/ops-maintenance-agent-implementation-plan.md)。
- 規格方向：規則巡檢負責客觀偵測，AI Maintenance Agent 負責白話摘要與處理順序，不直接改 secrets、不直接核准或發布。

## Monorepo 結構

```text
ExposureFlow/
├── apps/
│   ├── api/                 # FastAPI、SQLAlchemy、Celery、Alembic
│   └── web/                 # Next.js 15 顧問後台
├── packages/
│   ├── connectors/          # GSC、SERP、indexability connectors
│   ├── execution-adapters/  # ContentFlow / WordPress 等執行適配器
│   ├── exposure-core/       # 曝光核心邏輯
│   ├── shared/              # Python 共用工具
│   ├── shared-types/        # TypeScript 共用型別
│   ├── ui/                  # React UI 元件
│   └── sdk/                 # TypeScript API SDK
├── docs/
│   ├── product/             # 產品規格、GTM、Phase、運維計畫
│   └── handoff/             # 客戶交付 handoff 文件
├── infra/
│   └── docker/              # Production Docker Compose、Caddy、維運腳本
└── tests/                   # 跨套件整合測試
```

## 技術棧

| 層級 | 技術 |
|------|------|
| Frontend | Next.js 15、React、TypeScript |
| Backend | FastAPI、SQLAlchemy 2.x、Alembic、Pydantic |
| Database | PostgreSQL 16、pgvector |
| Queue | Redis、Celery worker、Celery beat |
| AI | OpenAI SDK、grounded content pipeline、SEO QA / writing agents |
| Integrations | Google Search Console、ContentFlow、WordPress |
| Deployment | Docker Compose、Caddy、Linode |

## Production

| 項目 | URL / 說明 |
|------|------------|
| App | `https://app.kakusinn.com` |
| 顧問登入 | `https://app.kakusinn.com/app-entry` |
| API Health | `https://app.kakusinn.com/health` |
| 站點管理 | `/app/{workspaceId}/settings/sites` |
| 顧問工作台 | `/app/{workspaceId}/consultant-inbox` |
| 多站總覽 | `/app/{workspaceId}/agency` |
| Internal Admin | `/internal-admin` |

Production 服務組成：

```text
Caddy
  ├── Web (Next.js)
  └── API (FastAPI)
        ├── Postgres + pgvector
        ├── Redis
        ├── Celery worker
        └── Celery beat
```

部署與重啟依 [`docs/product/linode-deploy-runbook.md`](docs/product/linode-deploy-runbook.md)。

## 顧問作業流程

標準新案流程見 [`docs/product/consultant-site-onboarding-playbook.md`](docs/product/consultant-site-onboarding-playbook.md)。

```text
線下簽約 / 收款
  → 開通顧問帳號
  → 建立 client workspace
  → 建立 Site
  → 完成 Strategy / Business Scope
  → 連 GSC
  → 首次 sync
  → Opportunity / Decision
  → 內容產生 / 審核 / 發布
  → 報表或 handoff
```

目前「顧問」是作業模式，不是單一程式角色。實際權限由 RBAC 決定：

- `owner` / `admin`：完整管理、整合、agency dashboard。
- `strategist`：策略、內容、決策與站點操作。
- `editor`：內容與部分站點操作。
- `analyst`：讀取與分析。
- `client_viewer`：第二階段 Client Portal 使用，現階段不上線。

## 本機開發

> 使用者偏好：避免不必要的 Python venv 操作。以下保留標準指令，實際環境可依本機 setup 調整。

```bash
# Node dependencies
pnpm install

# Environment
cp .env.example .env

# API
cd apps/api
pip install -e ".[dev]"
uvicorn exposureflow_api.main:app --reload

# Web
pnpm --filter @exposureflow/web dev
```

常用檢查：

```bash
# Backend lint
cd apps/api
python -m ruff check exposureflow_api tests

# Focused consultant tests
python -m pytest tests/test_consultant_buckets.py tests/test_consultant_inbox.py -q

# Web typecheck
cd apps/web
npx tsc --noEmit
```

## 重要文件

| 文件 | 用途 |
|------|------|
| [`docs/product/gtm-deployment-scope.md`](docs/product/gtm-deployment-scope.md) | 現階段 GTM / 部署 scope，顧問優先 |
| [`docs/product/consultant-site-onboarding-playbook.md`](docs/product/consultant-site-onboarding-playbook.md) | 每一案 client site 標準 SOP |
| [`docs/product/exposureflow-development-plan.md`](docs/product/exposureflow-development-plan.md) | Phase 0–14 工程開發計畫 |
| [`docs/product/phase-log.md`](docs/product/phase-log.md) | Phase 完成紀錄 |
| [`docs/product/linode-deploy-runbook.md`](docs/product/linode-deploy-runbook.md) | Linode production 部署 runbook |
| [`docs/product/ops-maintenance-agent-implementation-plan.md`](docs/product/ops-maintenance-agent-implementation-plan.md) | AI 維護工程師施工規格 |
| [`docs/product/ui-ux-audit-and-restructure-plan.md`](docs/product/ui-ux-audit-and-restructure-plan.md) | UI/UX 重整紀錄與方向 |
| [`docs/product/contentflow-reuse-boundary.md`](docs/product/contentflow-reuse-boundary.md) | ContentFlow 復用邊界 |
| [`docs/product/contentflow-porting-map.md`](docs/product/contentflow-porting-map.md) | ContentFlow 移植地圖 |

## 開發與交付原則

- 以完整產品為目標，不做 MVP 捷徑。
- 任何 Phase 或大型功能需 code review、測試、必要時 Bugbot / Security Review。
- Secret、credential、`.env` 不得 commit。
- Production 以顧問代操為主；自助註冊、Stripe 自助計費、Client Portal 屬第二階段。
- AI / Agent 可偵測、產文、驗證、摘要，但不自動核准內容、決策、關鍵字，也不自動修改客戶網站。

## 授權

Proprietary — All rights reserved.
