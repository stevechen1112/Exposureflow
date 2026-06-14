# ExposureFlow Phase 執行紀錄

本文件記錄各 Phase 完成狀態，供跨 session 延續開發使用。  
執行準則見根目錄 **`AGENTS.md` 憲章四原則**。

**驗收規則：**

- 驗收單位 = **一個 Phase**
- **進入新 Phase 前**：重新閱讀 `docs/product/exposureflow-development-plan.md`（當前 Phase 第九章 + 第十六章補強），完成 Kickoff 後才寫碼（見 `AGENTS.md` §進入新 Phase 前）
- 每 Phase：**完整 Code Review**（含 Bugbot、必要測試、Security Review）→ 修復 → Commit → 標記 `completed` → **直接進下一 Phase**
- **不需**每 Phase 向使用者確認
- **唯一使用者回報**：Phase 0–14 全部完成後

## 狀態說明

- `pending`：尚未開始
- `in_progress`：進行中
- `review`：實作完成，review / 測試中
- `completed`：review 通過且已 commit
- `blocked`：阻塞，需記錄原因

## Phase 總表

| Phase | 名稱 | 狀態 | Commit | 完成日期 | 備註 |
|-------|------|------|--------|----------|------|
| 0 | 產品核心定義 | completed | 791ec51 | 2026-06-14 | EF-0001、EF-0002 |
| 1 | 多租戶基礎架構 | completed | 06d85f4 | 2026-06-14 | EF-0101–0104 |
| 2 | 資料接入層 | completed | 8c0b4c7 | 2026-06-14 | EF-0201–0205 完整 review |
| 3 | Exposure Core | completed | 40bd83a | 2026-06-14 | EF-0301–0303 + 補強 |
| 4 | Topic Graph | completed | 830d45d | 2026-06-14 | EF-0401–0403 + 補強 |
| 5 | SERP Matrix | completed | 5c87603 | 2026-06-14 | EF-0501–0503 + 補強 |
| 6 | AI Visibility | completed | 49942b4 | 2026-06-14 | EF-0601–0604 + 補強 |
| 7 | Decision Plane | completed | 1c12618 | 2026-06-14 | EF-0701–0703 |
| 8 | Execution Plane | completed | 0b589dc | 2026-06-14 | EF-0801–0814；review 見 `phase-8-review.md` |
| 9 | Dashboard / UX | completed | 0b589dc | 2026-06-14 | EF-0901–0910；review 見 `phase-9-review.md` |
| 10 | Reporting | completed | 0b589dc | 2026-06-14 | EF-1001–1002；review 見 `phase-10-review.md` |
| 11 | SaaS Commercial | in_progress | — | — | |
| 12 | Security / Reliability | pending | — | — | |
| 13 | Internal Admin / CS | pending | — | — | |
| 14 | Production Launch | pending | — | — | |

## Phase 詳細紀錄

---

### Phase 0 — 產品核心定義

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `docs/product/product-north-star-spec.md`（EF-0001）
- `docs/product/kpi-taxonomy.md`（EF-0001）
- `docs/product/contentflow-reuse-boundary.md`（EF-0002）
- `docs/product/contentflow-porting-map.md`（EF-0002）
- `docs/product/phase-0-review.md`

**驗收證據：**

- EF-0001 / EF-0002 檢查表全數 PASS（見 `phase-0-review.md`）
- KPI 映射矩陣覆蓋全部核心模組（`kpi-taxonomy.md` §9）
- ContentFlow 基準：`977734cc` @ `git@github.com:stevechen1112/ContentFlow.git`

**已知限制：**

- 無（Phase 0 為定義階段，無程式碼變更）

---

### Phase 1 — 多租戶基礎架構

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- 租戶模型與 Alembic migration（`apps/api/exposureflow_api/models/`、`alembic/versions/001_initial_tenant.py`）
- 租戶 API（workspaces、sites、members、invitations、integrations、api-keys、jobs）
- RBAC 權限矩陣（`auth/permissions.py`）
- Celery job 基礎（`jobs/`）
- Audit log helper（`common/audit.py`）
- 2FA / impersonation endpoints（`auth/router.py`）
- 整合測試（`tests/test_tenant_isolation.py`）
- `docs/product/phase-1-review.md`

**驗收證據：**

- EF-0101–0104 檢查表全數 PASS（見 `phase-1-review.md`）
- `ruff check exposureflow_api` 通過
- CI 含 Postgres service 執行 pytest

**已知限制：**

- 生產認證待 Phase 11 接入 Clerk
- Job handler 為佔位，實際 connector 邏輯於 Phase 2

**下一 Phase 前置：**

- 開始 Phase 2：GSC / GA4 / SERP / Tech SEO / Bing connectors

---

### Phase 2 — 資料接入層

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `packages/connectors/`（GSC、GA4、SERP、Tech SEO、Bing）
- `apps/api/exposureflow_api/models/ingestion.py`
- `apps/api/exposureflow_api/integrations/`（sync helpers、API routes）
- `apps/api/exposureflow_api/jobs/handlers/`（gsc、ga4、serp、tech_seo、bing）
- `alembic/versions/002_ingestion_layer.py`
- `docs/product/phase-2-review.md`

**驗收證據：**

- EF-0201–0205 檢查表全數 PASS（見 `phase-2-review.md`）
- `ruff check` 通過（connectors + api）
- connectors unit tests 3/3 PASS

**已知限制：**

- 外部 API 需有效憑證與環境變數
- EF-0206–0208 補強項待後續 Phase

**下一 Phase 前置：**

- 開始 Phase 3：ExposureAsset、ExposureOpportunity、Opportunity Scorer

---

### Phase 3 — Exposure Core

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `apps/api/exposureflow_api/models/exposure.py`
- `apps/api/exposureflow_api/exposure/`（scorer、service、router、owner_classification）
- `apps/api/exposureflow_api/competitors/router.py`
- `alembic/versions/004_exposure_core.py`
- `docs/product/phase-3-review.md`

**驗收證據：**

- EF-0301–0303 檢查表 PASS（見 `phase-3-review.md`）
- `ruff check` 通過；scorer / owner classification 單元測試 6 passed
- Bugbot + Security Review High 已修復

**已知限制：**

- OG-002+ 規則待 Phase 4–6 資料就緒後擴充
- 整合測試需 CI Postgres

**下一 Phase 前置：**

- 開始 Phase 4：Topic Graph、Cannibalization、Internal Link Opportunity

---

### Phase 4 — Topic Coverage Graph

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `models/topic.py`、`alembic/versions/005_topic_graph.py`
- `topics/`（graph_builder、cannibalization、internal_links、service、router）
- `jobs/handlers/topic_graph_rebuild.py`
- `docs/product/phase-4-review.md`

**驗收證據：**

- EF-0401–0403、EF-0404–0405 PASS（見 `phase-4-review.md`）
- 單元測試 10 passed；Bugbot / Security Review 完成

**已知限制：**

- embedding/Leiden 升級待後續 Phase
- 整合測試需 CI Postgres

**下一 Phase 前置：**

- 開始 Phase 5：SERP Slot Matrix、Featured Snippet / PAA Opportunity

---

### Phase 5 — SERP Slot Matrix

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `SerpSlotTarget` 模型與 migration `006_serp_matrix.py`
- `serp/`（matrix、opportunities、owner、service、router）
- SERP opportunity 規則 OG-002、OG-007、OG-008、OG-009
- `docs/product/phase-5-review.md`

**驗收證據：**

- EF-0501–0503、EF-0504–0505 PASS
- 單元測試 6 passed；Security Review PASS

**下一 Phase 前置：**

- 開始 Phase 6：AI Probe Framework、AI Visibility

---

### Phase 6 — AI Visibility Monitor

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `AIProbeSet`、`AIProbeRun`、`AICitation`、`BrandEntity`、`BrandMention`、`SerpoRecord`
- migration `007_ai_visibility.py`
- assisted manual / CSV·JSON import、visibility score、entity check、SERPO
- OG-010、OG-011 opportunity 規則
- `docs/product/phase-6-review.md`

**驗收證據：**

- EF-0601–0608 PASS
- 單元測試 10 passed；Bugbot / Security Review 修復後 PASS

**下一 Phase 前置：**

- 開始 Phase 7：Decision Plane（Candidate Generator、Action Selector）

---

### Phase 7 — Decision Plane

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `ActionCandidate`、`ActionDecision`、`Roadmap`、`RoadmapItem`
- migration `009_decision_plane.py`
- Candidate generator、selector、roadmap builder
- API：`/decisions/candidates`、`/roadmaps`
- Jobs：`decision.candidates.generate`、`roadmap.build`
- `docs/product/phase-7-review.md`

**驗收證據：**

- EF-0701–0703 PASS
- 單元測試 5 passed

**下一 Phase 前置：**

- 開始 Phase 8：Execution Plane

---

### 2026-06-14 規格修訂 — Phase 8 企業級內容執行補強

**原因：**

- 上市版 ExposureFlow 將服務上百上千多租戶 B2B 企業客戶。
- 除決策核准外，系統必須自行完成可系統化的執行與產出，包含文章、頁面更新、FAQ、schema、解決方案頁、比較頁與出口市場內容。
- 原 Phase 8 僅以 Content Brief / Content Execution Adapter / Publish Gate 描述內容能力，對企業自家資料、domain knowledge、claim verification、source coverage、多市場與容量控管不足。

**本次修訂文件：**

- `docs/product/exposureflow-development-plan.md`
- `docs/product/product-north-star-spec.md`
- `docs/product/contentflow-reuse-boundary.md`
- `docs/product/contentflow-porting-map.md`

**新增權威要求：**

- Phase 8 必須實作 Workspace Brand / Knowledge Base、Evidence Retrieval / Source Pack、Grounded Content Brief Builder、Grounded Content Compiler、Claim / Source Verification Gate、Content QA / Human Review、Content Cost / Capacity Controls。
- ContentFlow 只能作邏輯參考；不得直接依賴 ContentFlow runtime。
- 所有 knowledge retrieval 必須以 `workspace_id` 隔離，禁止跨租戶資料用於生成。
- 沒有足夠 evidence 的 claim 不可 publish-ready，必須進入 `needs_human_evidence`、`blocked` 或人工補資料流程。

---

### 2026-06-14 規格修訂 — 顧問策略面談 / 關鍵字金字塔 / 交付承諾

**原因：**

- SEO 顧問實務不是先由系統任意挑 keyword，而是先與客戶面談，理解公司、產品、服務、市場、競品、未來目標、主力產品與客戶族群。
- 新網站或新市場可能沒有 GSC 資料，不能把 GSC 當成唯一發動來源。
- 顧問需要能與客戶承諾每月 / 每季內容、refresh、FAQ / schema、技術修復與報表交付量；純 opportunity-driven 會讓掌握度不足。
- 自然曝光最大化必須受 business scope 約束，不能推薦客戶不賣、不服務或不想進入的市場 / 關鍵字。

**本次修訂文件：**

- `docs/product/exposureflow-development-plan.md`
- `docs/product/product-north-star-spec.md`

**新增權威要求：**

- 新增 Strategy Intake / Business Scope Layer：Business Intake、Product / Solution Scope、Target Market / Competitor Map、Keyword Pyramid、Business Fit Gate、Delivery Commitment。
- 新增 cold-start 流程：以顧問核准的 keyword pyramid、產品範圍、競品 / SERP research 啟動新站 / 新市場。
- Opportunity Generator 新增 OG-016 / OG-017，支援 cold-start candidate 與 out-of-scope keyword 阻擋。
- Opportunity Scorer 新增 `business_fit_score`，且 `business_fit_score = 0` 時不得進入內容生成或 publish-ready。
- Roadmap Builder 必須同時考慮 exposure priority 與 delivery commitment，顯示承諾量、已排程量、已完成量與缺口。

