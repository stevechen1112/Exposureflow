# ExposureFlow 開發憲章

本文件是 AI Agent 執行 ExposureFlow 全產品開發的**最高指導原則**。  
凡與本憲章衝突的建議、捷徑或縮減範圍做法，**一律以本憲章為準**。

**權威規格（技術細節）：**

- `docs/product/exposureflow-development-plan.md`（含第十六章補強規格）
- `docs/product/organic-impressions-seo-plan.md`（策略方法論）

**執行紀錄：**

- `docs/product/phase-log.md`

Cursor 自動規則：`.cursor/rules/exposureflow-constitution.mdc`

---

## 憲章四原則（唯一執行準則）

以下四點為使用者明確訂立的最高原則，Agent 必須逐字遵循。

### 原則 1：詳實按照計畫、Phase 順序開發

- 必須依照 `exposureflow-development-plan.md` 的 **Phase 0 → Phase 14**、各 Phase 的 **EF-xxxx 任務**與**驗收標準**逐步實作。
- **預設規則**：當前 Phase 完整完成並通過驗收（見原則 2）後，才可進入下一 Phase。
- **這是原則，不是死板**：僅在**必要**時允許調整順序或補做前置項，例如：
  - 當前 Phase 被明確的技術阻塞（migration、tenant middleware 未就緒）且無法在本 Phase 內解決；
  - 計畫文件本身有缺口，需先補文件再實作。
- 調整時必須在 `docs/product/phase-log.md` 記錄原因，**不得**以此為由跳過驗收或縮減範圍。
- **禁止**：
  - 跳過 Phase 或合併多個 Phase 以求快；
  - 用「先做簡化版」「先做 MVP」代替計畫中的完整 Phase 內容；
  - 未讀計畫對應章節就動手寫碼。

### 原則 2：每 Phase 結束 → 完整 Code Review → 修復補正 → Commit

**驗收單位 = 一個 Phase**（不是子里程碑、不是單一 ticket、不是中途向你請示）。

每個 Phase 結束時，**必須**依序完成：

1. **完整 Code Review**：對照該 Phase 所有 EF-xxxx 任務與驗收標準，逐項檢查，不得遺漏。
2. **修復補正**：Review 發現的問題必須在**本 Phase 內**全部修完，不得推到下一 Phase。
3. **品質驗證**：執行該 Phase 相關的 lint、測試、必要時整合測試；全部通過。
4. **Commit**：本 Phase 驗收通過後提交 git（可含多個邏輯 commit，但 Phase 在 `phase-log.md` 須一次標記為 `completed`）。
5. **紀錄**：更新 `docs/product/phase-log.md`（完成項、驗收證據、已知限制）。

**通過上述關卡後，Agent 直接進入下一 Phase。**

- **不需要**每個 Phase 結束時向使用者確認或等待批准。
- **不需要**使用者參與 Phase 間的 code review；Review 由 Agent 完整執行並留下可驗證證據（測試、檢查表、phase-log）。

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
- **唯一正式回報時機**：Phase 0–14 **全部**完成、最終驗收通過後，向使用者提交**一次**完整實作報告。

---

## 不存在的交付模式（明確禁止）

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

## 每 Phase Code Review 檢查表

- [ ] 該 Phase 所有 EF-xxxx 任務已完成
- [ ] 對照計畫驗收標準，逐項有證據（測試、API、UI、migration）
- [ ] `workspace_id` 租戶隔離（若適用）
- [ ] RBAC 與權限矩陣（若適用）
- [ ] audit log、usage event、憑證加密（若適用）
- [ ] 無 stub / 無未修復的 TODO 冒充完成
- [ ] lint / 測試通過
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
