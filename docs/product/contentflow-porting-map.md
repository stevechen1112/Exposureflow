# ContentFlow → ExposureFlow 移植地圖

**文件編號**：EF-0002（附屬交付物）  
**狀態**：Phase 0 交付物  
**ContentFlow 基準**：`git@github.com:stevechen1112/ContentFlow.git` @ `977734cc372821f18ce8a086e2370a4439073398`

本文件為 RD 移植工單索引。每項移植完成後須更新「移植紀錄」區塊。

---

## 1. 移植優先序

```text
Phase 2: GSC → GA4 → SERP → Tech SEO → Brand Web Presence
Phase 8: Workspace Knowledge → Source Pack → Grounded Content Compiler → Claim Gate → Publish Gate → WordPress → ForgeBase
Phase 1: secret_crypto 模式、job registry 概念
Phase 4–7: site_intelligence、analytics、cluster、refresh、strategic_controls 邏輯翻譯
```

---

## 2. 工單對照（EF-CF）

| Ticket | 來源 | 目標 | Phase | 類型 | 狀態 |
|--------|------|------|-------|------|------|
| EF-CF-001 | `tools/gsc.py` | `packages/connectors/.../google_search_console.py` + `jobs/gsc_sync.py` | 2 | direct_port | pending |
| EF-CF-002 | `tools/serp.py` | `packages/connectors/.../serp/` + `serp/slot_extractor.py` | 2 | refactor | pending |
| EF-CF-003 | `publishers/wordpress.py` | `packages/execution-adapters/.../wordpress.py` | 8 | direct_port | pending |
| EF-CF-004 | `utils/publish_safety.py` | `apps/api/.../execution/safety/publish_gate.py` | 8 | refactor | pending |
| EF-CF-005 | `tools/ga4.py` | `packages/connectors/.../google_analytics.py` | 2 | direct_port | pending |
| EF-CF-006 | `tools/tech_seo.py` | `packages/connectors/.../tech_seo/` | 2 | refactor | pending |
| EF-CF-007 | `tools/brand_mentions.py` | `packages/connectors/.../brand_web_presence.py` | 2 | logic_translation | pending |
| EF-CF-008 | `publishers/forgebase.py` | `packages/execution-adapters/.../forgebase.py` | 8 | direct_port | pending |
| EF-CF-009 | `utils/article_schema.py` | `packages/shared/.../article_schema.py` | 8 | direct_port | pending |
| EF-CF-010 | `utils/slug_governance.py` | `packages/shared/.../slug_policy.py` | 8 | direct_port | pending |
| EF-CF-011 | `agents/content_compiler/*` | `apps/api/.../execution/content/grounded_compiler.py` + contracts | 8 | logic_translation | pending |
| EF-CF-012 | `agents/company_kb.py` | `apps/api/.../knowledge/` + PostgreSQL / pgvector | 8 | logic_translation | pending |
| EF-CF-013 | `agents/claim_verifier.py`, `agents/factcheck_agent.py` | `apps/api/.../execution/safety/claim_source_gate.py` | 8 | logic_translation | pending |
| EF-CF-014 | `agents/mode_router.py`, `policy_resolver.py`, `project_context.py` | `apps/api/.../execution/review_policy.py` | 8 | logic_translation | pending |

---

## 3. 邏輯翻譯工單（非 EF-CF，依 Phase 執行）

| 來源 | 目標模組 | Phase | 狀態 |
|------|----------|-------|------|
| `agents/site_intelligence.py` | `services/site_inventory.py`, `content_overlap.py` | 4 | pending |
| `agents/analytics_agent.py` | opportunity generator rules, cannibalization | 3–4 | pending |
| `agents/cluster_agent.py` | `topic_graph/rebuild` job | 4 | pending |
| `agents/refresh_agent.py` | snippet/PAA detector, refresh adapter | 5, 8 | pending |
| `agents/content_compiler/*` | `execution/content_brief_builder`, grounded compiler, evidence map | 8 | pending |
| `agents/company_kb.py` | `knowledge/sources`, `knowledge/facts`, workspace-scoped retrieval | 8 | pending |
| `agents/claim_verifier.py`, `agents/factcheck_agent.py` | `execution/safety/claim_source_gate.py`, `content_claims`, `content_gate_results` | 8 | pending |
| `agents/mode_router.py`, `policy_resolver.py`, `project_context.py` | domain / compliance / review policy router | 8 | pending |
| `agents/strategic_controls.py` | `decision/candidate_generator` trace | 7 | pending |
| `scheduler_job_registry.py` | `job_definitions` seed data | 1 | pending |

---

## 4. 禁止移植清單

以下路徑 **不得** 出現在 ExposureFlow `apps/` 或 `packages/` 核心路徑中（可作 `docs/reference/` 只讀摘錄除外）：

```text
ContentFlow/src/contentflow/models/database.py
ContentFlow/src/contentflow/agents/strategic_agent.py
ContentFlow/src/contentflow/agents/orchestrator.py
ContentFlow/src/contentflow/scheduler.py
ContentFlow/src/contentflow/admin/
ContentFlow/src/contentflow/agents/company_kb.py as runtime dependency
ContentFlow/src/contentflow/agents/content_compiler/compiler.py as runtime dependency
```

---

## 5. 逐檔移植規格（EF-CF-001 範本）

### EF-CF-001：GSC Connector

```text
source_file: ContentFlow/src/contentflow/tools/gsc.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file:
  - packages/connectors/src/connectors/google_search_console.py
  - apps/api/exposureflow_api/integrations/gsc/client.py
  - apps/api/exposureflow_api/jobs/gsc_sync.py
porting_type: refactor
removed_dependencies:
  - contentflow.config settings singleton
  - contentflow.db session
new_interfaces:
  - GSCClient(credentials, site_url, http_client)
  - sync_gsc_site(workspace_id, site_id, date_range) -> job_runs
tests_added:
  - tests/connectors/test_gsc_client.py
  - tests/jobs/test_gsc_sync.py
  - tests/integration/test_gsc_tenant_isolation.py
known_limitations:
  - GSC API 資料延遲 2–3 天
acceptance:
  - 同步 query/page/country/device/date 至 gsc_performance_rows
  - incremental sync
  - 失敗不影響其他 workspace
```

### EF-CF-002：SERP Connector

```text
source_file: ContentFlow/src/contentflow/tools/serp.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file:
  - packages/connectors/src/connectors/serp/providers/serper.py
  - packages/connectors/src/connectors/serp/providers/serpapi.py
  - apps/api/exposureflow_api/serp/slot_extractor.py
porting_type: refactor
removed_dependencies:
  - ContentFlow SERP result 綁定 Article 的資料結構
new_interfaces:
  - SerpProvider.fetch(keyword, country, language, device) -> raw_json
  - SlotExtractor.extract(raw_json) -> list[SERPSlot]
tests_added:
  - tests/serp/test_slot_extractor.py
known_limitations:
  - AI Overview presence 依 provider 能力；不可用猜測標記 achieved
acceptance:
  - Serper / SerpAPI fallback
  - 寫入 serp_query_snapshots + serp_slots
```

### EF-CF-003：WordPress Publisher

```text
source_file: ContentFlow/src/contentflow/publishers/wordpress.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file: packages/execution-adapters/src/execution_adapters/wordpress.py
porting_type: direct_port
new_interfaces:
  - publish_draft(execution_job) / update_post(execution_job)
acceptance:
  - site-scoped credentials
  - 僅在 publish_gate 通過後執行
```

### EF-CF-004：Publish Gate

```text
source_file: ContentFlow/src/contentflow/utils/publish_safety.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file: apps/api/exposureflow_api/execution/safety/publish_gate.py
porting_type: refactor
new_interfaces:
  - PublishGate.check(execution_job) -> GateResult
  - 新增 exposure 專屬：schema, noindex, canonical, AI crawler policy
  - 必須讀取 claim_source_gate 與 content_gate_results，不可只看 SEO score
acceptance:
  - gate 未通過則 execution job 不可 publish
```

### EF-CF-011：Grounded Content Compiler

```text
source_file:
  - ContentFlow/src/contentflow/agents/content_compiler/brief_builder.py
  - ContentFlow/src/contentflow/agents/content_compiler/outline_planner.py
  - ContentFlow/src/contentflow/agents/content_compiler/section_generator.py
  - ContentFlow/src/contentflow/agents/content_compiler/content_integrator.py
  - ContentFlow/src/contentflow/models/content_contracts.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file:
  - apps/api/exposureflow_api/execution/content/brief_builder.py
  - apps/api/exposureflow_api/execution/content/grounded_compiler.py
  - apps/api/exposureflow_api/execution/content/contracts.py
porting_type: logic_translation
removed_dependencies:
  - ContentFlow Article / PipelineRun / Orchestrator runtime
  - ContentFlow settings / db session
new_interfaces:
  - build_content_brief(workspace_id, opportunity_id, decision_id) -> ContentBrief
  - run_grounded_content_generation(execution_job_id) -> ContentGenerationRun
acceptance:
  - draft 附 evidence_map、claim list、unsupported claims
  - 不通過 source pack coverage 時不可產生 publish-ready draft
```

### EF-CF-012：Workspace Knowledge Base

```text
source_file:
  - ContentFlow/src/contentflow/agents/company_kb.py
  - ContentFlow/src/contentflow/project_context.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file:
  - apps/api/exposureflow_api/knowledge/models.py
  - apps/api/exposureflow_api/knowledge/retrieval.py
  - apps/api/exposureflow_api/knowledge/ingest.py
porting_type: logic_translation
removed_dependencies:
  - ChromaDB project collection as tenant boundary
new_interfaces:
  - ingest_knowledge_source(workspace_id, site_id, source)
  - retrieve_workspace_facts(workspace_id, site_id, query, filters)
acceptance:
  - pgvector retrieval 必須在 DB query 中帶 workspace_id filter
  - expired / unapproved facts 不可用於自動生成
```

### EF-CF-013：Claim / Source Gate

```text
source_file:
  - ContentFlow/src/contentflow/agents/claim_verifier.py
  - ContentFlow/src/contentflow/agents/factcheck_agent.py
source_commit: 977734cc372821f18ce8a086e2370a4439073398
target_file:
  - apps/api/exposureflow_api/execution/safety/claim_source_gate.py
  - apps/api/exposureflow_api/execution/content/claim_extractor.py
porting_type: logic_translation
removed_dependencies:
  - heuristic-only KB match as final authority
new_interfaces:
  - verify_content_claims(content_generation_run_id) -> list[ContentClaim]
  - block_publish_on_unsupported_claims(execution_job_id)
acceptance:
  - unsupported / contradicted / forbidden claims block publish
  - gate result 顯示可補 source 與 severity
```

---

## 6. 外部依賴對照

| ContentFlow 依賴 | ExposureFlow 替代 |
|------------------|-------------------|
| ContentFlow `.env` | 根目錄 `.env` + `Settings` |
| SQLite / ContentFlow DB | PostgreSQL + Alembic |
| ContentFlow scheduler | Celery + `job_runs` |
| Admin 手動觸發 | API + Internal Admin（Phase 13） |

---

## 7. 移植完成定義

單一 EF-CF ticket 完成當且僅當：

1. 目標檔案已實作並通過測試。
2. 無 ContentFlow import。
3. `usage_events` 已記錄外部 API 呼叫（若適用）。
4. 本文件對應列 `狀態` 更新為 `completed`。
5. 移植紀錄區塊已填寫。

---

## 8. 相關文件

- `contentflow-reuse-boundary.md`
- `exposureflow-development-plan.md` 第十三章、第十六章 §12
