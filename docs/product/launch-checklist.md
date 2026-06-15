# ExposureFlow 正式上線檢查表（EF-1401 / EF-H010）

> **GTM Scope**：現階段僅 **顧問後台**（Consultant-Only），無自助註冊／Stripe／Client Portal。  
> 見 **`gtm-deployment-scope.md`**。「自助客戶旅程」現階段 **不適用**；「顧問客戶旅程」適用。

本檢查表用於 Phase 14 正式對外營運前驗收。自動化檢查可透過 `GET /api/v1/launch/readiness` 或 Internal Admin 取得。

## 產品核心

| # | 項目 | 驗收標準 | 自動檢查 ID |
|---|------|----------|-------------|
| 1 | 多租戶隔離 | 跨 workspace 讀寫 403；`test_tenant_isolation.py` 通過 | `tenant.isolation_tests` |
| 2 | Site onboarding | 可建立 site、完成 onboarding 步驟 | `product.onboarding` |
| 3 | GSC / 整合 | 可觸發 sync；sync state 可追蹤 | `product.gsc_sync` |
| 4 | Exposure Opportunity | 可列出、評分 opportunity | `product.opportunities` |
| 5 | Decision 核准 | approve / reject / defer 流程完整 | `product.decisions` |
| 6 | 報表 | 可產生並匯出 report | `product.reports` |

## 商業化

| # | 項目 | 驗收標準 | 自動檢查 ID |
|---|------|----------|-------------|
| 7 | 訂閱方案 | plans 已 seed | `billing.plans_seeded` |
| 8 | Stripe | checkout / portal / webhook 就緒 | `billing.subscriptions` |
| 9 | Usage metering | usage_events 記錄外部 API 成本 | `billing.usage_metering` |

## 營運與可靠性

| # | 項目 | 驗收標準 | 自動檢查 ID |
|---|------|----------|-------------|
| 10 | Internal Admin | support 可查 workspace / job / audit | `ops.internal_admin` |
| 11 | Backup / Restore | runbook + script 可執行 | `ops.backup_runbook`, `ops.backup_script` |
| 12 | Load test | dashboard / health 負載測試通過 | `ops.load_test` |
| 13 | Security review | 檢查表完成 | `security.review_checklist` |
| 14 | Job 佇列 | job definitions 註冊 | `ops.job_definitions` |

## 文件與對外材料（EF-1402）

| # | 項目 | 路徑 |
|---|------|------|
| 15 | Help center | `/help` |
| 16 | Onboarding guide | `/help/onboarding` |
| 17 | Integration setup | `/help/integrations` |
| 18 | API docs | `/help/api` |
| 19 | Security page | `/security` |
| 20 | Pricing | `/pricing` |
| 21 | Terms | `/terms` |
| 22 | Privacy | `/privacy` |
| 23 | DPA template | `/dpa` |
| 24 | Status page | `/status` |

## 自助客戶旅程（E2E）

1. 註冊 / 登入（Clerk production；dev 使用 dev-token）
2. 建立 workspace 與 site
3. 連接 GSC（Settings → Integrations）
4. 觸發 GSC sync → 等待 opportunity 出現
5. 核准 decision candidate → 查看 roadmap
6. 產生 monthly report → 匯出 PDF
7. 升級方案（Billing → Checkout）

## 顧問客戶旅程

1. Agency dashboard 建立 client workspace
2. 設定 white-label branding
3. 為 client 產生報表並匯出

## 內部團隊

1. Internal Admin：查 sync 失敗、配額、工單
2. Impersonation（audit 記錄）
3. Status incident 發布

## 簽核

| 角色 | 簽名 | 日期 |
|------|------|------|
| Engineering | | |
| Product | | |
| Security | | |
| Operations | | |
