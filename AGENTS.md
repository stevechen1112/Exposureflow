# ExposureFlow 開發憲章

本文件是 AI Agent 執行 ExposureFlow 全產品開發的**最高指導原則**。  
凡與本憲章衝突的建議、捷徑或縮減範圍做法，**一律以本憲章為準**。

**權威規格（技術細節）：**

- `docs/product/exposureflow-development-plan.md`（含第十六章補強規格）
- `docs/product/organic-impressions-seo-plan.md`（策略方法論）

**執行紀錄：**

- `docs/product/phase-log.md`

**上線／部署 Scope（GTM 決策 — 部署與整合優先序以此為準）：**

- `docs/product/gtm-deployment-scope.md` — 顧問優先、無自助註冊／計費、現階段 Consultant-Only；與 `pre-launch-audit.md` / `launch-checklist.md` 的「全自助 SaaS」假設衝突時 **以 GTM 文件為準**
- `docs/product/consultant-site-onboarding-playbook.md` — **每一案目標網站** 串接 SOP（顧問操作、客戶資料、GSC、驗收）

Cursor 自動規則：`.cursor/rules/exposureflow-constitution.mdc`

---

## 憲章四原則（唯一執行準則）

以下四點為使用者明確訂立的最高原則，Agent 必須逐字遵循。

### 原則 1：詳實按照計畫、Phase 順序開發

- 必須依照 `exposureflow-development-plan.md` 的 **Phase 0 → Phase 14**、各 Phase 的 **EF-xxxx 任務**與**驗收標準**逐步實作。
- **預設規則**：當前 Phase 完整完成並通過驗收（見原則 2）後，才可進入下一 Phase。
- **每次進入新 Phase 開發前**（含新 session 接續下一 Phase、或上一 Phase commit 後立即開工），**必須重新閱讀**開發計畫全文脈絡中的當前 Phase 章節，見 §進入新 Phase 前（Phase Kickoff）；**禁止**憑記憶或舊對話摘要直接寫碼，避免偏離計畫。
- **這是原則，不是死板**：僅在**必要**時允許調整順序或補做前置項，例如：
  - 當前 Phase 被明確的技術阻塞（migration、tenant middleware 未就緒）且無法在本 Phase 內解決；
  - 計畫文件本身有缺口，需先補文件再實作。
- 調整時必須在 `docs/product/phase-log.md` 記錄原因，**不得**以此為由跳過驗收或縮減範圍。
- **禁止**：
  - 跳過 Phase 或合併多個 Phase 以求快；
  - 用「先做簡化版」「先做 MVP」代替計畫中的完整 Phase 內容；
  - 未讀計畫對應章節就動手寫碼；
  - 實作與計畫驗收標準不一致卻未在 `phase-log.md` 記錄偏差。

### 原則 2：每 Phase 結束 → **完整 Code Review** → 修復補正 → Commit

**驗收單位 = 一個 Phase**（不是子里程碑、不是單一 ticket、不是中途向你請示）。

「完整 Code Review」**不是**自行填寫 PASS 檢查表而已；必須依下方 **§完整 Code Review 流程** 執行，並在 `docs/product/phase-N-review.md` 留下**可驗證證據**。

每個 Phase 結束時，**必須**依序完成：

1. **完整 Code Review**（§完整 Code Review 流程 步驟 1–6 全部完成）
2. **修復補正**：Review 發現的問題（含 Bugbot / Security Review 列出的項目）必須在**本 Phase 內**全部修完，或記錄為有理由的 `known_limitations` 且**不得**標記該 EF 驗收項為 PASS
3. **品質驗證**：該 Phase 相關 lint、單元測試、整合測試、contract 測試（若適用）**實際執行且通過**；禁止以 skip 代替通過（見 §測試執行要求）
4. **Commit**：本 Phase 驗收通過後提交 git（可含多個邏輯 commit，但 Phase 在 `phase-log.md` 須一次標記為 `completed`）
5. **紀錄**：更新 `docs/product/phase-log.md`（完成項、驗收證據、已知限制、review commit hash）

**通過上述關卡後，Agent 直接進入下一 Phase。**

- **不需要**每個 Phase 結束時向使用者確認或等待批准。
- **不需要**使用者參與 Phase 間的 code review。
- Review 由 Agent **完整執行**（含 Bugbot 子代理），並留下可驗證證據。

#### 完整 Code Review 流程（強制，每 Phase 必做）

| 步驟 | 內容 | 產出 / 證據 |
|------|------|-------------|
| **1. 規格對照** | 讀開發計畫該 Phase **全部** EF-xxxx 任務與驗收標準（含第十六章補強票） | `phase-N-review.md` §EF 逐項表，每項附檔案路徑或測試名稱 |
| **2. 變更範圍盤點** | 列出本 Phase 新增/修改的程式、migration、API、job、UI、測試 | review 文件 §變更清單 |
| **3. 自動化關卡** | 執行並通過：`ruff check`、該 Phase 相關 `pytest`、CI 等價命令 | review 文件 §測試執行紀錄（命令 + 結果摘要） |
| **4. 必要測試補齊** | 依 §Phase 測試最低要求 補齊並執行缺失測試 | 測試檔路徑 + 通過數量 |
| **5. Bugbot Review** | 啟動 **Bugbot** 子代理（`readonly: true`），Diff = 本 Phase 變更（`branch changes` 或 Phase commit 範圍） | review 文件 §Bugbot 發現表；**所有 High/Critical 必須修復** |
| **6. Security Review** | 若本 Phase 涉及 auth、RBAC、憑證、多租戶、計費、對外 API、PII，啟動 **Security Review** 子代理 | review 文件 §Security 發現表；**所有 High/Critical 必須修復** |

**禁止視為「完整 Code Review」的做法：**

- 僅根據檔案存在就標 PASS，未執行測試
- 測試因無 Postgres / 無 API key 而 skip，卻仍標記該驗收項 PASS
- 未跑 Bugbot 就寫「Code Review PASS」
- 將計畫補強票（如 EF-0206）自行略過卻不寫入 `known_limitations`
- 用 stub / TODO 通過驗收

#### 測試執行要求

- **預設**：本 Phase 新增或修改的測試必須 **0 failed**；允許 skip 僅當該測試明確標記 `@pytest.mark.requires_secrets` 且 review 中說明替代驗證（如 contract test + mock）。
- **有程式碼變更的 Phase**：至少執行一次含 **PostgreSQL** 的整合測試（本機 Docker 或 CI 等價環境）；不可僅跑無 DB 的 unit test 就結案。
- **新增資料表或 API**：必須有 **tenant isolation** 整合測試（跨 workspace 存取須 403）。
- **新增 connector / 外部整合**：必須有 **contract test**（mock HTTP），驗證請求格式與回寫邏輯，不可只測純函式。

#### Phase 測試最低要求（依 Phase 類型）

| Phase 類型 | 額外必備測試 |
|------------|----------------|
| 0（文件） | 文件交叉引用檢查、與憲章 / 北極星一致性 |
| 1（多租戶） | tenant isolation、RBAC 拒絕案例 |
| 2（接入層） | connector contract tests、ingestion tenant isolation、job handler 測試（mock） |
| 3–8（核心邏輯） | 領域規則單元測試 + API 整合測試 |
| 9（UI） | lint + 關鍵頁面 smoke / component test |
| 11–12（商業 / 安全） | Security Review **必做** |
| 14（上線） | 全量回歸 + 部署檢查清單 |

#### `phase-N-review.md` 必備章節

```text
1. 變更清單
2. EF-xxxx 逐項驗收（PASS/FAIL + 證據）
3. 測試執行紀錄（命令、環境、passed/failed/skipped）
4. Bugbot Review 結果
5. Security Review 結果（若適用；不適用須註明原因）
6. 修復紀錄（review 期間修復的項目）
7. 已知限制（誠實列出未覆蓋範圍）
8. 結論（僅當步驟 1–6 與測試關卡全部滿足才可寫 PASS）
```

### 原則 3：完整作法，禁止最小做法

- 開發目標是計畫中的**完整產品**（Phase 0–14 全部完成 = 可對外營運的多租戶 SaaS），**不是 MVP、不是精簡版、不是 stub 演示**。
- 每個 Phase 內，該 Phase 在計畫中要求的所有模組、schema、API、UI、job、測試，均須**完整實作**，不得以「之後再補」為由交付半成品。
- **禁止**：
  - 省略 migration、測試、tenant 隔離、RBAC、audit log、error handling；
  - 用 hardcode、mock、TODO 冒充已完成功能；
  - 只做 happy path；
  - 以「最小可行」為理由縮減計畫已列出的範圍。
- **允許**：計畫文件已明確列為「未來升級選項」的技術（例如 Temporal 替換 Celery）在第一版不實作——但這是**計畫原文**的例外，不是 Agent 自行縮減。

### 原則 4：從 Phase 0 起自主推進，完整實作後才回報

- 自 Phase 0 啟動後，Agent **持續工作**，依本憲章與計畫文件推進 Phase 0 → 14。
- **過程中不向使用者回報進度、不請示、不等待批准**；可自決的技術與實作問題一律自行解決。
- **僅在以下情況暫停**（記錄於 `phase-log.md` 的 `blocked` 狀態）：
  - 必須由使用者提供的 secret 或帳號（Clerk、Stripe、GSC OAuth 生產憑證等），且 local/dev 替代方案無法讓當前 Phase 驗收繼續；
  - 破壞性操作需明確授權（force push、刪除 production 資料等）；
  - 計畫與憲章無法覆蓋且無法合理推斷的商業決策。
- **Session 中斷時**：完成當前 Phase 的 review + commit + `phase-log.md` 後停止；下一 session **自動**從下一 Phase 繼續，**無需**使用者確認。
- **新 session 或新 Phase 的第一個動作**：執行 §進入新 Phase 前（Phase Kickoff），**重新閱讀** `docs/product/exposureflow-development-plan.md` 後再寫任何程式碼。
- **唯一正式回報時機**：Phase 0–14 **全部**完成、最終驗收通過後，向使用者提交**一次**完整實作報告。

---

## 進入新 Phase 前（Phase Kickoff，強制）

**觸發時機**（每次皆須執行，不可省略）：

- 開始 Phase 0 或任意 **Phase N** 的實作工作
- 上一 Phase 標記 `completed` 後，**進入 Phase N+1 的第一個動作**
- Session 中斷後接續開發，且當前 `phase-log.md` 顯示某 Phase 為 `in_progress` 或即將開始新 Phase

**必讀文件（依序）：**

1. **`docs/product/exposureflow-development-plan.md`**（權威工程規格；工作區路徑：`/Users/yuchuchen/Desktop/Exposureflow/docs/product/exposureflow-development-plan.md`）
2. **`docs/product/phase-log.md`** — 確認上一 Phase 的 `known_limitations` 與前置條件
3. **`AGENTS.md`** — 確認憲章四原則與完整 Code Review 要求未變更

**在開發計畫中至少精讀：**

| 章節 | 內容 | 目的 |
|------|------|------|
| **第九章** | 當前 Phase 的 **全部 EF-xxxx** 任務與**驗收標準** | 本 Phase 交付範圍 |
| **第十六章** | 當前 Phase 的補強票（如 EF-0205、EF-0306 等） | 避免漏做補強項 |
| **第四章 / 第十一章**（若本章節有引用） | schema、API、技術棧細節 | 與資料模型一致 |
| **第十三章**（若涉及 ContentFlow 移植） | EF-CF 對照 | 移植邊界正確 |

**Kickoff 產出（動手寫碼前完成）：**

- 在 `phase-log.md` 將當前 Phase 標為 `in_progress`（若尚未標記）
- 列出本 Phase **EF 工單清單**（含第十六章補強票；明確排除項須寫入備註）
- 對照計畫確認：**不做**上一 Phase 的範圍、**不做**下一 Phase 的範圍（避免搶做或偏移）

**禁止：**

- 未重新閱讀開發計畫就開始新 Phase 實作
- 僅依賴對話摘要、舊 review 或記憶代替閱讀計畫原文
- 發現與計畫不一致時自行改範圍而不更新 `phase-log.md`


以下概念**不得**出現在本專案執行中，不得作為縮減範圍的依據：

- MVP、MVP-Dev、精簡版、演示版
- Commercial Beta / Commercial GA 分階段交付（相對於完整 Phase 計畫的替代路線）
- 「先上線核心功能再補」
- 「這個 Phase 先做一部分」

**唯一交付路徑：Phase 0 → Phase 14，每 Phase 完整實作並驗收。**

---

## 產品紅線（計畫要求，開發時不得偏離）

- 北極星：自然曝光最大化；核心 KPI 為曝光、版位、主題覆蓋、AI 可見性。
- 核心物件：`ExposureOpportunity`、`ExposureAsset`、`TopicCluster`、`SERPSlot`、`AICitation`。
- 禁止做成 ContentFlow 2.0（文章工廠、以發文量為中心、無審核全自動發布）。

---

## 技術棧（計畫第十一章 + 第十六章，固定）

| 項目 | 決策 |
|------|------|
| Backend | Python FastAPI |
| ORM / Migration | SQLAlchemy 2.x + Alembic |
| Database | PostgreSQL 16 + pgvector |
| Queue | Redis + Celery |
| Frontend | Next.js 15 + React + TypeScript |
| Monorepo | pnpm + turbo |
| Auth | Clerk（production）+ dev JWT（local/test） |
| Billing | Stripe |

---

## Phase 清單（0–14）

| Phase | 名稱 |
|-------|------|
| 0 | 產品核心定義 |
| 1 | 多租戶基礎架構 |
| 2 | 資料接入層 |
| 3 | Exposure Core |
| 4 | Topic Graph |
| 5 | SERP Matrix |
| 6 | AI Visibility |
| 7 | Decision Plane |
| 8 | Execution Plane |
| 9 | Dashboard / UX |
| 10 | Reporting |
| 11 | Multi-Tenant SaaS Commercial Layer |
| 12 | Security / Compliance / Reliability |
| 13 | Product Operations / Internal Admin |
| 14 | Production Launch / Commercial Readiness |

各 Phase 任務與驗收標準以開發計畫**第九章**為準。

---

## 每 Phase 啟動檢查表（Kickoff，寫碼前）

- [ ] 已重新閱讀 `docs/product/exposureflow-development-plan.md` 當前 Phase（第九章 + 第十六章補強）
- [ ] 已閱讀 `phase-log.md` 上一 Phase 限制與前置條件
- [ ] 已列出本 Phase 全部 EF-xxxx 工單
- [ ] `phase-log.md` 當前 Phase 已標為 `in_progress`
- [ ] 已確認本 Phase 邊界（不搶做他 Phase 範圍）

## 每 Phase Code Review 檢查表

**僅在 §完整 Code Review 流程 步驟 1–6 完成後勾選。**

- [ ] 該 Phase 所有 EF-xxxx 任務已完成（含計畫第十六章補強票，或已記錄於 known_limitations）
- [ ] 對照計畫驗收標準，逐項有**可執行證據**（測試名稱、API 路徑、migration 檔名）— 非僅檔案存在
- [ ] `workspace_id` 租戶隔離**整合測試**（若本 Phase 新增資料表或 API）
- [ ] RBAC 與權限矩陣拒絕案例測試（若適用）
- [ ] audit log、usage event、憑證加密（若適用）已驗證
- [ ] connector / 外部整合 **contract test**（mock HTTP，若適用）
- [ ] 無 stub / 無未修復的 TODO 冒充完成
- [ ] `ruff check` 通過
- [ ] `pytest` 執行完成：**0 failed**（skip 須符合 §測試執行要求）
- [ ] 含 PostgreSQL 的整合測試已執行（有程式碼變更的 Phase）
- [ ] **Bugbot Review** 已執行，High/Critical 已修復
- [ ] **Security Review** 已執行（若適用），High/Critical 已修復
- [ ] `docs/product/phase-N-review.md` 含必備八章節
- [ ] `phase-log.md` 已更新為 `completed`
- [ ] git commit 已完成

---

## Commit 規範

```text
phase(N): 簡述 Phase 完成內容

- 主要交付項
- 測試與 migration

Ref: EF-xxxx
```

- 不提交 `.env`、真實 API key。
- 僅在使用者**明確要求**時 `git push`。

---

## 文件衝突時的優先順序

1. **本憲章（AGENTS.md）** — 執行方式與四原則
2. **開發計畫第九章 Phase 任務與驗收** — 做什麼
3. **開發計畫第十一章 + 第十六章** — 技術與 schema 細節
4. SEO 策略計畫 — 方法論參考，非工程縮減依據

若開發計畫第十六章曾出現 MVP 分層描述，**以本憲章為準，該描述不適用於本專案執行**。

---

## 生效

自 Phase 0 啟動起生效。變更憲章須使用者明確指示。
