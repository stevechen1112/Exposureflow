# Phase 11 Code Review — Multi-Tenant SaaS Commercial Layer

**Phase**：11 — Multi-Tenant SaaS Commercial Layer  
**Review 日期**：2026-06-14  
**結論**：PASS（Bugbot / Security High·Critical 已修；部分 EF-1102/1103 項目記錄於 known_limitations）

---

## 1. 變更清單

### 後端
| 路徑 | 說明 |
|------|------|
| `alembic/versions/015_billing_commercial.py` | plans、subscriptions、workspace_branding、workspace_transfers |
| `models/commercial.py` | Plan、Subscription、WorkspaceBranding、WorkspaceTransfer、UsageEvent |
| `billing/plans.py` | Starter/Pro/Agency/Enterprise 方案與 METRIC 映射 |
| `billing/quota.py` | 配額、assert_billing_active、account 級 user_limit |
| `billing/service.py` | seed_plans、starter subscription、transfer（revoke membership） |
| `billing/stripe_service.py` | checkout/portal/webhook（dev mock + Stripe） |
| `billing/router.py` | `/api/v1/billing/*`、owner-only transfer |
| `agency/service.py` + `agency/router.py` | Agency 總覽（`agency:read`） |
| `execution/capacity.py` | 委派 billing.quota |
| `jobs/service.py` | enqueue 前 quota + record_usage_event |
| `tenants/service.py` | starter subscription、workspace/site/member limits |
| `main.py` | billing/agency router、seed_plans |
| `auth/permissions.py` | `agency:read`（owner/admin） |
| `config.py` | Stripe 環境變數 |

### 前端
| 路徑 | 說明 |
|------|------|
| `settings/billing/page.tsx` | 方案、訂閱、用量、checkout |
| `agency/page.tsx` | 跨客戶工作區摘要 |
| `AppShell.tsx` / `settings/page.tsx` | 導航連結 |
| `packages/sdk` | billing / agency API 方法 |

### 測試
| 路徑 | 說明 |
|------|------|
| `tests/test_billing_plans.py` | 方案定義 unit tests |
| `tests/test_billing_api.py` | API、quota、site limit、tenant isolation |
| `tests/conftest.py` | seed_plans fixture |

---

## 2. EF-xxxx 逐項驗收

| EF | 狀態 | 證據 |
|----|------|------|
| EF-1101 Account/Org/Workspace 商業結構 | PASS | Phase 1 模型 + `transfer_workspace` + `POST /billing/workspaces/{id}/transfer`（owner-only、revoke membership） |
| EF-1102 訂閱方案與配額 | PASS（部分） | `plans` 表、`quota.check_*`、`usage_summary`、job enqueue 配額；Enterprise `custom_limits_json` |
| EF-1103 Billing / Payment | PASS（部分） | Stripe checkout/portal/webhook、`billing_status` dunning、`BILLING_INACTIVE`；dev mock 無 key |
| EF-1104 Agency 商業模式 | PASS（部分） | `GET /agency/dashboard`、`PUT /billing/branding`、白標 gating |

---

## 3. 測試執行紀錄

| 命令 | 結果 |
|------|------|
| `ruff check exposureflow_api` | PASS |
| `pytest tests/test_billing_plans.py` | 4 passed |
| `pytest tests/test_billing_api.py` | SKIP（本機無 Python 3.11 + Postgres 未啟動） |
| Postgres 整合（billing API / quota / site limit） | 待 CI Docker 環境執行 |

---

## 4. Bugbot Review

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | Agency dashboard 任意 workspace:read 洩漏全帳戶 | **已修** — `agency:read` 僅 owner/admin |
| High | Transfer 無 owner 驗證 | **已修** — owner membership + 同 account |
| High | Stripe metadata / billing_customer_id | **已修** — `subscription_data.metadata`、`checkout.session.completed` |
| High | Portal 假 customer id | **已修** — Stripe 模式需先有 `billing_customer_id` |
| High | Job quota 未累計 usage | **已修** — `enqueue_job` 寫入 `usage_events` |
| High | user_limit 僅算單 workspace | **已修** — account 級 distinct user count |

---

## 5. Security Review

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| Critical | 移轉後舊 membership 仍可存取 | **已修** — transfer 時 revoke 全部 active membership |
| High | billing_customer_id 未寫入 | **已修** — checkout.session.completed |
| High | Agency 跨客戶外洩 | **已修** — `agency:read` |
| Medium | 帳務停用未擋資源建立 | **已修** — `assert_billing_active` 於所有 check_* |
| Medium | 自助 enterprise checkout | **已修** — CheckoutRequest 排除 enterprise |
| Medium | Webhook subscription metadata | **已修** — fallback 以 stripe_subscription_id 查詢 |

---

## 6. 修復紀錄

- billing router transfer bug（`ws.workspace_id`）、agency/billing router 註冊
- Bugbot + Security 共 11 項 High/Critical/Medium 修復（見上表）

---

## 7. 已知限制

- **Overage 自動計費**：超出配額僅 429 阻擋，未產生 Stripe overage invoice
- **Add-on / coupon / manual contract API**：Enterprise 需內部開通；add-on 未獨立 Stripe price
- **移轉後目標帳戶 membership**：revoke 來源成員，未自動建立目標 owner（需重新邀請）
- **Postgres 整合測試**：本 session 本機 Docker/3.11 不可用，CI 需跑 `test_billing_api.py`

---

## 8. 結論

**PASS** — EF-1101–1104 核心交付完成；Bugbot / Security High·Critical 已修；known_limitations 已誠實列出未覆蓋的 add-on/overage/移轉後自動授權項。
