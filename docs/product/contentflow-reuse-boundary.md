# ContentFlow 復用邊界文件

**文件編號**：EF-0002  
**狀態**：Phase 0 交付物  
**ContentFlow 來源**：`git@github.com:stevechen1112/ContentFlow.git` @ `977734cc372821f18ce8a086e2370a4439073398`  
**ExposureFlow 路徑**：`/Users/yuchuchen/Desktop/Exposureflow`

---

## 1. 邊界結論

ExposureFlow **復用** ContentFlow 的成熟 **connector、publisher、safety、utility** 能力，  
**不复用** 以 `Article` / `ContentCalendar` / `PipelineRun` 為中心的產品核心架構。

```text
ExposureFlow = 新產品核心 + 新資料模型 + 新決策/量測平面
             + 選擇性移植 ContentFlow 底層 adapter
```

---

## 2. 分類定義

| 分類 | 含義 | ExposureFlow 處置 |
|------|------|-------------------|
| **connector** | 外部資料接入（GSC、SERP 等） | 移植至 `packages/connectors`，DI 重構 |
| **publisher** | 內容發布至 CMS | 移植至 `packages/execution-adapters` |
| **safety** | 發布前安全閘 | 移植至 `execution/safety/publish_gate.py` |
| **utility** | 無領域核心的工具函式 | 移植至 `packages/shared` 或對應 util |
| **logic_reference** | 商業邏輯可參考，須重寫為 exposure-centric | 翻譯邏輯，不搬檔案 |
| **reference_only** | 反面教材或歷史參考 | 不移植 |
| **forbidden** | 禁止作為 ExposureFlow 核心 | 不得進入核心 schema / 決策 / 主 UI |

---

## 3. 檔案級分類表

### 3.1 connector（移植）

| ContentFlow 路徑 | ExposureFlow 目標 | 優先級 | Phase |
|------------------|-------------------|--------|-------|
| `tools/gsc.py` | `packages/connectors/src/connectors/google_search_console.py` | P0 移植 | 2 |
| `tools/ga4.py` | `packages/connectors/src/connectors/google_analytics.py` | P1 | 2 |
| `tools/serp.py` | `packages/connectors/src/connectors/serp/` + slot extractor | P0 移植 | 2 |
| `tools/tech_seo.py` | `packages/connectors/src/connectors/tech_seo/` | P0 移植 | 2 |
| `tools/brand_mentions.py` | `packages/connectors/src/connectors/brand_web_presence.py` | P2 | 2 |

### 3.2 publisher（移植）

| ContentFlow 路徑 | ExposureFlow 目標 | Phase |
|------------------|-------------------|-------|
| `publishers/wordpress.py` | `packages/execution-adapters/.../wordpress.py` | 8 |
| `publishers/forgebase.py` | `packages/execution-adapters/.../forgebase.py` | 8 |
| `publishers/base.py` | 參考介面設計 | 8 |

### 3.3 safety / utility（移植）

| ContentFlow 路徑 | ExposureFlow 目標 | Phase |
|------------------|-------------------|-------|
| `utils/publish_safety.py` | `apps/api/.../execution/safety/publish_gate.py` | 8 |
| `utils/article_schema.py` | `packages/shared/.../article_schema.py` | 8 |
| `utils/slug_governance.py` | `packages/shared/.../slug_policy.py` | 8 |
| `utils/secret_crypto.py` | 參考加密模式 | 1 |

### 3.4 logic_reference（邏輯翻譯，不直接搬）

| ContentFlow 路徑 | 翻譯為 | Phase |
|------------------|--------|-------|
| `agents/site_intelligence.py` | `site_inventory.py`, `content_overlap.py` | 4 |
| `agents/analytics_agent.py` | exposure-first diagnostics, cannibalization | 3–4 |
| `agents/cluster_agent.py` | topic graph（embeddings + GSC，非 LLM 主分群） | 4 |
| `agents/refresh_agent.py` | snippet detector, section refresh | 5, 8 |
| `agents/content_compiler/` | Content Execution Adapter（非核心） | 8 |
| `scheduler_job_registry.py` | `job_definitions` 設計參考 | 1 |
| `agents/strategic_controls.py` | candidate/decision trace 參考 | 7 |

### 3.5 reference_only（不移植）

| ContentFlow 路徑 | 原因 |
|------------------|------|
| `agents/strategic_agent.py` | 高耦合、以 generate/refresh 文章為中心 |
| `agents/orchestrator.py` | 文章 pipeline 編排 |
| `scheduler.py` | 27 jobs 與文章 pipeline 耦合 |
| `admin/app.py` | UI 綁定文章管理 |
| `admin/templates/*` | 文章工廠後台 |
| `agents/writing_agent.py` 等產文 agents | 非 ExposureFlow 核心 |

### 3.6 forbidden（禁止作為 ExposureFlow 核心）

| 項目 | 禁止方式 |
|------|----------|
| `models/database.py` 整檔作為主 schema | 不得複製；ExposureFlow 使用第十一章 + 第十六章 schema |
| `Article` 作為第一級物件 | 僅能作為 `ExposureAsset.asset_type` 之一 |
| `ContentCalendar` 作為主工作流 | 改用 Opportunity Queue + Roadmap |
| `PipelineRun` 作為核心狀態機 | 改用 `ExecutionJob` + `job_runs` |
| `SEO Score` 作為主品質門檻 | 改用 ExposureOpportunityScore |
| `strategic_agent.py` 作為決策核心 | 改用 Decision Plane + evidence-backed candidates |
| 16 agents 作為產品對外語言 | 對外以 Exposure Plane 模組語言呈現 |

---

## 4. 依賴與設定邊界

移植時 **必須移除** 對下列 ContentFlow 專屬項的硬依賴：

- `contentflow.config` 全域 settings
- `contentflow.models.database` ORM 模型
- `contentflow.db` session 單例
- ContentFlow admin 路由與模板

改為：

- `exposureflow_api.config.Settings`（pydantic-settings）
- SQLAlchemy models 對齊 ExposureFlow schema
- Dependency injection（connector 接收 credentials + http client）
- 獨立 `job_runs` / Celery task 上下文帶 `workspace_id`

---

## 5. 測試邊界

每個移植 adapter 必須具備：

- 無 ContentFlow app context 的 unit test
- contract test（mock provider response）
- workspace isolation test（若寫入 DB）

不得僅在 ContentFlow 環境內驗證即視為移植完成。

---

## 6. 驗收對照（EF-0002）

| 驗收項 | 狀態 |
|--------|------|
| 可復用檔案已分類為 connector / publisher / safety / utility / reference | 本文件 §3 |
| 禁止 Article / ContentCalendar / PipelineRun 作為核心 schema | §3.6 |
| 不得直接複製 `models/database.py` | §3.6 |
| `strategic_agent.py` 不作為決策核心 | §3.5、§3.6 |
| 移植路徑與 Phase 對應 | 見 `contentflow-porting-map.md` |

---

## 7. 相關文件

- `contentflow-porting-map.md` — 逐檔移植工單
- `exposureflow-development-plan.md` 第四章、第十三章
- `product-north-star-spec.md` §7
