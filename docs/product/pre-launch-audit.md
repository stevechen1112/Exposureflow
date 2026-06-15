# ExposureFlow 上線前 Audit（Pre-Launch）

> **GTM Scope 覆蓋**：Product 已確認 **顧問優先、無自助註冊／計費、現階段 Consultant-Only**。  
> 部署與上線 **必做／不做** 清單以 **`gtm-deployment-scope.md`** 為準；本 audit 為通用全自助 SaaS 參考，勿默認全部 BLOCKER 皆為現階段必做。

**Audit 日期**：2026-06-14  
**範圍**：Phase 0–14 工程交付 vs 正式對外 SaaS 上線就緒  
**結論**：**Phase 工程結案 ≠ Production GA Ready**。模組齊全度約 **85%**；上線前必須處理 **3 項 BLOCKER** 與若干 HIGH。

---

## 1. 執行摘要

| 維度 | 狀態 | 說明 |
|------|------|------|
| Phase 0–14 工程 | ✅ 已標 completed | `phase-log.md`、15 份 phase review |
| 計畫 EF 主線（EF-0001–EF-1403） | ✅ 大多 PASS | 各 phase review 逐項表 |
| 第十六章補強票 | ⚠️ 1 項 DEFERRED | **EF-0206** Brand Web Presence |
| 本機全量 pytest | ⚠️ 未驗 | Docker 未啟動；Py3.10 有 collection error |
| CI（GitHub Actions） | ⚠️ 部分 | API + Postgres 有；Web 無 `build` |
| Production 部署 | ❌ 缺失 | 無 Dockerfile / K8s / CD |
| Production 登入 | ❌ 缺失 | Clerk 未接入 |
| 自助 GSC 連線 | ❌ 缺失 | OAuth UI/API 未實作 |
| E2E 旅程 | ❌ 未驗 | 無 Playwright；關鍵路徑無整合測試 |

**上線判定：NO-GO**（待 BLOCKER 清單完成 + E2E 手動/自動驗收）

---

## 2. BLOCKER（不上線）

### B1. Clerk Production 認證未實作

| 項目 | 現況 |
|------|------|
| 計畫要求 | Production 使用 Clerk JWT；禁用 dev-token |
| 實際 | 僅 `POST /api/v1/auth/dev-token` + 自建 HS256 JWT |
| Web | `SessionBootstrap.tsx`、`app-entry/page.tsx` 在 non-dev 顯示「請使用 Clerk（尚未嵌入）」 |
| 缺口 | 無 `@clerk/nextjs`、無 Clerk webhook handler、`.env.example` 無 `CLERK_*` |

**修復方向**：Clerk Dashboard → Next.js middleware + API JWT 驗證（JWKS）→ webhook 同步 user。

---

### B2. 無 Production 部署管線

| 項目 | 現況 |
|------|------|
| 計畫要求 | Docker、API/Web/Worker、PostgreSQL、Redis、備份 job |
| 實際 | 僅 `infra/docker/docker-compose.yml`（local Postgres+Redis） |
| 缺口 | 無 Dockerfile、無 staging/prod manifest、CI 無 deploy job |

**修復方向**：API/Web/Celery 三服務 Dockerfile + staging 環境 + secrets（Stripe/Clerk/JWT/DB）。

---

### B3. 自助 GSC OAuth 連線未完成

| 項目 | 現況 |
|------|------|
| Launch checklist | 客戶自助連 GSC → sync → opportunity |
| 實際 | GSC sync **handler** 存在；憑證僅 `POST /integrations/credentials` API |
| UI | `settings/integrations/page.tsx` 顯示「設定連線（**待實作**）」 |
| 缺口 | 無 Google OAuth callback、token refresh 流程（phase-2 known_limitation） |

**修復方向**：OAuth 授權 URL + callback route + 憑證加密儲存 + Integrations UI 完成連線流程。

---

## 3. HIGH（上線前強烈建議完成）

### H1. 無端到端（E2E）驗證

`docs/product/launch-checklist.md` 自助旅程 7 步，**無** Playwright/Cypress 測試。

| 步驟 | 後端 | 前端 | 自動化測試 |
|------|------|------|------------|
| 登入 | dev-token only | dev only | ❌ |
| 建立 workspace/site | API ✅ | onboarding 部分 | 隔離測試 only |
| 連 GSC | handler ✅ | ❌ OAuth | mock handler test |
| 看 opportunity | API ✅ | UI ✅ | isolation ✅ |
| 核准 decision | API ✅ | UI ✅ | **無 approve 整合測** |
| 產生/匯出 report | API ✅ | client portal export | exporter 單元 only |
| Stripe 付款 | API ✅ | billing page | dev mock only |

**修復方向**：至少 1 條 Playwright happy path + 手動 UAT 簽核表。

---

### H2. Email 通知僅 log channel

- `notification_email_enabled=false`；啟用後仍 `email_channel: "log"`
- sync 失敗、配額警示、report ready **無法真正寄信**

**修復方向**：SendGrid/SES/SMTP adapter + production env。

---

### H3. Stripe Webhook 無整合測試

- Checkout/portal/webhook handler 存在（Phase 11）
- **無** `test_stripe_webhook`；無 key 時 dev mock
- Overage 計費列 known_limitation

**修復方向**：Stripe CLI webhook contract test + staging 真實 checkout 演練。

---

### H4. EF-0206 Brand Web Presence — DEFERRED

- 計畫第十六章補強票；`phase-2-review.md` 明確 DEFERRED
- 無 `brand_web_presence` connector

**判定**：非 launch hard blocker（若產品接受），但計畫完整性缺 1 票 → 需產品決策：補做或正式 waive。

---

### H5. 顧問端 Report UI 不完整

- 後端 `POST /api/v1/reports/generate` + export 完整
- Dashboard **無** dedicated reports 頁（client portal 可 export）
- Launch checklist 要求顧問/客戶皆可產生報表

**修復方向**：Dashboard 加 reports 頁或確認 client portal 為唯一入口並更新 checklist。

---

### H6. Security Review Checklist 未簽核

- `docs/product/security-review-checklist.md` 全部 `[ ]` 未勾
- 含：production 禁用 dev-token、JWT secret、backup drill、impersonation 等

**修復方向**：逐項勾選 + 記錄 reviewer/日期。

---

## 4. MEDIUM（可 v1 接受但須文件化）

| # | 項目 | 說明 |
|---|------|------|
| M1 | SAML 完整 SP | Phase 12：設定儲存 only，無 assertion 驗簽 |
| M2 | KMS | Fernet 本地加密；AWS KMS SDK 待 deploy |
| M3 | GDPR 級聯刪除 | export 有；全表 purge job 不完整 |
| M4 | pgvector 原生查詢 | embedding 在 JSONB；非 SQL vector search |
| M5 | PDF 中文字型 | latin-1 降級 |
| M6 | CI Web | 只 lint，無 `next build` |
| M7 | Opportunity 規則 | OG-002+ 部分依 Phase 4–6 擴充（phase-3 review） |
| M8 | ContentFlow 移植 | EF-CF-001–004 獨立 epic，非 Phase 15 |
| M9 | phase-log hash | Phase 14 commit 欄位與實際 HEAD 可能不一致 |

---

## 5. EF 追溯摘要（Phase 0–14 主線）

| Phase | EF 範圍 | Audit 判定 | 主要缺口 |
|-------|---------|------------|----------|
| 0 | EF-0001–0002 | PASS | — |
| 1 | EF-0101–0104 | PASS | Clerk prod 替換 dev auth |
| 2 | EF-0201–0205 | PASS | **EF-0206 DEFERRED**；OAuth refresh |
| 3 | EF-0301–0307 | PASS | 部分 OG 規則待資料就緒 |
| 4 | EF-0401–0405 | PASS | embedding 代理算法 |
| 5 | EF-0501–0505 | PASS | — |
| 6 | EF-0601–0608 | PASS | — |
| 7 | EF-0701–0703 | PASS | LLM rationale v2 |
| 8 | EF-0801–0814 | PASS | pgvector 檢索路徑 |
| 9 | EF-0901–0910 | PASS | — |
| 10 | EF-1001–1002 | PASS | 中文 PDF；report E2E |
| 11 | EF-1101–1104 | PASS | overage；webhook 測試 |
| 12 | EF-1201–1204 | PASS | SAML/KMS/Prometheus |
| 13 | EF-1301–1306 | PASS | SMTP |
| 14 | EF-1401–1403 | PASS | 本 audit 為其延伸 |

**第十六章補強票**：除 EF-0206 外，其餘在對應 phase review 多標 PASS（需 CI Postgres 二次確認）。

---

## 6. 測試與自動化驗證

| 命令 | 本機（2026-06-14） | CI（`.github/workflows/ci.yml`） |
|------|-------------------|----------------------------------|
| `ruff check` | 預期 PASS | ✅ api job |
| `pytest`（全量） | Docker 未跑 → skip/error | ✅ api + Postgres 16 |
| `pytest tests/load/` | 需 Py3.11+ | 未獨立 job |
| `pnpm lint`（web） | — | ✅ |
| `next build` | — | ❌ 未跑 |
| Launch readiness API | 需 Postgres | 可手動 curl |

**建議上線前必跑**（staging）：

```bash
docker compose -f infra/docker/docker-compose.yml up -d
cd apps/api && alembic upgrade head && pytest tests/ -q
curl -s http://localhost:8000/api/v1/launch/readiness | jq .overall
```

---

## 7. 建議修復順序（4 週參考）

| 週 | 工作 | 解決 |
|----|------|------|
| W1 | Clerk 全棧 + 禁用 production dev-token | B1 |
| W1 | Dockerfile + staging deploy + secrets | B2 |
| W2 | GSC OAuth UI/API + token refresh | B3 |
| W2 | Stripe webhook 測試 + staging 付款演練 | H3 |
| W3 | Playwright E2E（登入→GSC→opp→approve→report） | H1 |
| W3 | SMTP 通知 | H2 |
| W4 | Security checklist 簽核 + backup restore drill | H6 |
| W4 | 手動 UAT + launch checklist 簽核 | GA |

---

## 8. Go / No-Go 檢查表

| # | 項目 | 狀態 |
|---|------|------|
| 1 | Clerk production 登入可用 | ❌ |
| 2 | Staging 部署可访问 | ❌ |
| 3 | 客戶可自助連 GSC 並 sync | ❌ |
| 4 | 付費 Stripe checkout 演練成功 | ⚠️ 未驗 |
| 5 | 全量 pytest 0 failed（CI） | ⚠️ 需確認 main CI |
| 6 | E2E 或 UAT 簽核 | ❌ |
| 7 | Security checklist 簽核 | ❌ |
| 8 | Backup restore drill | ⚠️ script 有，未演練 |
| 9 | EF-0206 決策（做或 waive） | ❌ 未決 |

**Go 條件**：上表 1–7 至少 1–6 全 ✅；8–9 有書面紀錄。

---

## 9. 與 Phase 14 自動檢查的關係

`GET /api/v1/launch/readiness` 檢查**模組/文件/DB 信號**，**不能**替代本 audit 的 BLOCKER 項（Clerk、deploy、OAuth）。

建議：本文件為 **GA 權威 gate**；launch readiness API 為 **工程健康儀表板**。

---

## 10. 簽核

| 角色 | 姓名 | 日期 | Go/No-Go |
|------|------|------|----------|
| Engineering | | | No-Go |
| Product | | | |
| Security | | | |
| Operations | | | |
