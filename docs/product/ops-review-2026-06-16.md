# 營運變更 Code Review — 2026-06-16

## 1. 變更清單

| # | 檔案 | 變更類型 | 說明 |
|---|------|---------|------|
| 1 | `apps/api/exposureflow_api/jobs/handlers/knowledge_ingest.py` | **重寫** | 從 stub → 完整 httpx 爬取 + OpenAI gpt-4o-mini 抽取 |
| 2 | `packages/sdk/src/index.ts` | **新增 7 方法** | buildSourcePack, buildContentBrief, createExecutionJob, createGenerationRun, listGenerationRuns, approveGenerationRun, requestChangesGenerationRun |
| 3 | `apps/web/.../content-review/page.tsx` | **新增 UI** | 內容生成工作區 + 預覽/核准/退件面板 |
| 4 | `apps/api/pyproject.toml` | **新增依賴** | `openai>=1.0.0` |
| 5 | `infra/docker/docker-compose.prod.yml` | **修改** | worker 從 `build:` → `image: docker-api:latest` |

## 2. 逐項審查

### 2.1 knowledge_ingest.py

| # | 項目 | 嚴重度 | 說明 |
|---|------|--------|------|
| A1 | `import re` 在函式內部 (L73) | 🟡 Medium | `re` 在 L73 和 L118 兩處使用，應移至檔案頂部。目前可運作但違反 PEP 8 |
| A2 | `db.add(source)` 冗餘 (L155) | 🟢 Low | source 已由 `get_source()` 載入同一 session，設 `status="approved"` 即自動追蹤。`db.add()` 無害但多餘 |
| A3 | HTML 解析僅用 regex | 🟡 Medium | 對簡單商業網站足夠，複雜 SPA 頁面可能漏內容。已知限制 |
| A4 | 無 OpenAI 重試機制 | 🟡 Medium | API 失敗 → job 永久失敗。Celery 層有 retry 但 handler 內無。已知限制 |
| A5 | JSON 提取 regex greedy | 🟢 Low | `r'\[.*\]'` greedy 匹配，若 AI 回傳多個陣列可能錯取。Prompt 已限制「ONLY the JSON array」 |
| A6 | Facts 無驗證 | 🟢 Low | 信任 AI 抽取結果，無交叉比對。設計決策（AI from verified source） |
| A7 | `market`/`language` 可為 None | 🟢 Low | Prompt 寫死 `"tw"`/`"zh-TW"` 但 code 用 `.get()`，AI 若漏給則存 None |

**✅ 已驗證通過**：
- 錯誤處理完整（MISSING_SOURCE_ID, SOURCE_NOT_FOUND, FETCH_FAILED, NO_OPENAI_KEY, AI_EXTRACTION_FAILED）
- `finalize_job_run` 統一收尾（commit + 狀態更新）
- Facts `status="approved"` + source auto-approve（#1 修復）
- Content 截斷 8000 chars 合理（成本控制）
- `httpx.AsyncClient(timeout=30.0, follow_redirects=True)` 正確

### 2.2 SDK index.ts（新增 7 方法，L583-655）

| # | 項目 | 嚴重度 | 說明 |
|---|------|--------|------|
| B1 | 回傳型別 `Record<string, unknown>` | 🟢 Low | 與 SDK 其餘方法一致，非 regression |
| B2 | API 路徑正確 | ✅ | 全部對應 `content/router.py` 路由 |
| B3 | `buildSourcePack` body 參數完整 | ✅ | site_id, opportunity_id, execution_job_id, market, language, brief_type |
| B4 | `createGenerationRun` 含 `auto_compile` | ✅ | 前端傳 `auto_compile: true`，API 接受 |

**✅ 無問題**。

### 2.3 content-review/page.tsx（新增 UI）

| # | 項目 | 嚴重度 | 說明 |
|---|------|--------|------|
| C1 | `loadApprovedCandidates` silent catch | 🔴 **High** | `catch { /* silent */ }` — API 失敗時 dropdown 空白且無錯誤提示，使用者無法診斷 |
| C2 | `runWorkflow` 無 partial failure cleanup | 🟡 Medium | Step 2 失敗後 Step 1 的 Source Pack 成孤兒。已知限制 |
| C3 | `workflowStep` 無 timeout | 🟡 Medium | API 卡住時 UI 永久顯示「建立 Source Pack…」。應加 30s timeout |
| C4 | Markdown 以 `<pre>` 純文字呈現 | 🟢 Low | 無 markdown→HTML 渲染。設計決策（審核階段看原始 markdown） |
| C5 | 無分頁 | 🟢 Low | `listGenerationRuns` 全量載入。站點 runs 少時可接受 |

**✅ 已驗證通過**：
- RBAC：`canReview = can("site:write")` 正確 gate
- 狀態機：idle → building_source_pack → building_brief → creating_job → creating_run → idle
- 成功後自動 reset 選項 + 刷新列表
- 預覽面板 toggle 正確（同 run 再點 = 收起）
- 退件面板含必填 textarea 驗證

### 2.4 pyproject.toml

| # | 項目 | 說明 |
|---|------|------|
| D1 | `openai>=1.0.0` | ✅ 正確加入 dependencies，與 `httpx>=0.28.0` 同區塊 |

### 2.5 docker-compose.prod.yml

| # | 項目 | 嚴重度 | 說明 |
|---|------|--------|------|
| E1 | 缺少 `pull_policy: never` | 🔴 **High** | `image: docker-api:latest` 無 pull_policy，Docker 可能嘗試從 registry pull（會失敗）。需加 `pull_policy: never` |
| E2 | Image 依賴隱式 | 🟡 Medium | Worker 依賴 `docker-api:latest` 先 build，但 compose 無 explicit 宣告。`depends_on: api` 只保證啟動順序 |

## 3. 測試執行紀錄

| 測試 | 方法 | 結果 |
|------|------|------|
| Ingest handler 端到端 | 觸發 job → 檢查 DB facts | ✅ 8 facts 成功抽取 |
| Source Pack coverage | 8 approved facts → build | ✅ coverage 1.00（從 0.20） |
| Content Brief 建立 | Source Pack ready → build | ✅ status=ready, brief_type=article |
| Generation Run | Brief + Job → create | ✅ status=draft, output_markdown 有內容 |
| 核准流程 | UI 點擊核准 | ✅ status=approved |
| Worker image 一致化 | `docker inspect` | ✅ 兩容器皆 `docker-api:latest` |
| Worker handler 同步 | grep `status.*approved` | ✅ 第 146 行 |
| Celery worker 運行 | `celery inspect ping` | ✅ 1 node online |

## 4. Bugbot Review

（本日變更為營運修復，非 Phase 開發。手動審查替代。）

| 嚴重度 | 數量 | 項目 |
|--------|------|------|
| 🔴 High | 2 | C1 (silent catch), E1 (missing pull_policy) |
| 🟡 Medium | 5 | A1, A3, A4, C2, C3, E2 |
| 🟢 Low | 5 | A2, A5, A6, A7, B1, C4, C5 |

## 5. Security Review

| 項目 | 評估 |
|------|------|
| OpenAI API key | 透過 `settings.openai_api_key` 從環境變數讀取，未 hardcode ✅ |
| 網頁爬取 | 僅爬取 `source.source_uri`（已入庫的 URL），無 SSRF 風險 ✅ |
| User-Agent | 自訂 `ExposureFlow/1.0 KnowledgeIngest`，非偽裝 ✅ |
| Content 截斷 | 8000 chars 上限，防止 token 濫用 ✅ |
| compose 檔 | 無暴露新 port，無 secret 洩漏 ✅ |

**無 High/Critical security 問題。**

## 6. 修復紀錄

| # | 項目 | 修復 | 狀態 |
|---|------|------|------|
| C1 | `loadApprovedCandidates` silent catch | 加 `candidatesError` state + UI 顯示 | ✅ 已部署 |
| E1 | 缺少 `pull_policy: never` | 加 `pull_policy: never` | ✅ 已部署 |
| A1 | `import re` 位置 | 移至檔案頂部 | ✅ 已部署 |

## 7. 已知限制

| # | 項目 | 說明 |
|---|------|------|
| L1 | HTML 解析僅 regex | 複雜 SPA 頁面可能漏內容，未來可換 BeautifulSoup/trafilatura |
| L2 | 無 OpenAI 重試 | Celery 層有 retry 但 handler 內無 exponential backoff |
| L3 | `runWorkflow` 無 partial failure cleanup | Step N 失敗後前面步驟的資源成孤兒 |
| L4 | `workflowStep` 無 timeout | API 卡住時 UI 永久顯示進度中 |
| L5 | Markdown 純文字預覽 | 無渲染，審核階段可接受 |
| L6 | Worker image 需手動 rebuild API 後才更新 | `docker compose up -d --no-deps worker` 可解決 |

## 8. 結論

**PASS** — 3 項修復完成後。

所有變更功能驗證通過（端到端測試：ingest → Source Pack → Brief → Generation Run → 核准）。High 項目 C1/E1 及 Medium A1 需修復，其餘 Medium 為已知限制。
