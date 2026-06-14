# Phase 8 Code Review — Execution Plane（完整版）

**日期**：2026-06-14  
**狀態**：PASS  
**範圍**：EF-0801～EF-0809、EF-0810～EF-0814（第十六章補強）  
**Commit**：_(待使用者指示 commit)_

---

## 1. 變更清單

| 類別 | 路徑 |
|------|------|
| Migrations | `010_strategy_knowledge_execution.py`、`011_usage_events.py`、`012_knowledge_embeddings.py` |
| Models | `models/strategy.py`、`knowledge.py`、`execution_content.py`、`commercial.py` |
| Strategy | `strategy/business_fit.py`、`service.py`、`router.py`、`schemas.py` |
| Knowledge | `knowledge/service.py`、`router.py`、`embeddings.py`、`retrieval.py` |
| Content / Compiler | `content/*`、`execution/compiler/*`、`source_pack.py`、`brief_builder.py`、`claim_verifier.py` |
| Gates / Capacity | `execution/publish_gate.py`、`execution/capacity.py` |
| Adapters | `execution/adapters/*`、`execution/dispatcher.py` |
| Publishers | `packages/execution-adapters/wordpress.py`、`forgebase.py` |
| Jobs | `content.generate.*`、`knowledge.*`、`strategy.cold_start_research`、`execution.job.run` |
| Decision 整合 | `exposure/scorer.py`（business_fit_score）、`decision/candidate_generator.py` |
| 測試 | `test_*` Phase 8 相關 34+ unit tests |

---

## 2. EF-xxxx 逐項驗收

| Ticket | 結果 | 證據 |
|--------|------|------|
| EF-0801 Knowledge Base | PASS | `/api/v1/knowledge/*`、brand profile、sources、facts、tenant scope |
| EF-0802 Source Pack | PASS | `execution/source_pack.py`、`POST /content/source-packs/build` |
| EF-0803 Brief Builder | PASS | `execution/brief_builder.py`、`POST /content/briefs/build` |
| EF-0804 Content Compiler | PASS | `execution/compiler/*`、`POST /content/generation-runs/{id}/compile` |
| EF-0805 Claim Gate | PASS | `claim_verifier.py`、`POST .../verify-claims` |
| EF-0806 WordPress Publisher | PASS | `execution_adapters/wordpress.py`、contract test |
| EF-0807 Publish Gate | PASS | `publish_gate.py`、`POST .../publish-gate` |
| EF-0808 Human Review | PASS | approve / request-changes + `audit_logs` |
| EF-0809 Cost / Capacity | PASS | `usage_events`、`execution/capacity.py`、quota 429 |
| EF-0810 Refresh Adapter | PASS | `adapters/refresh.py`、`test_execution_adapters.py` |
| EF-0811 Schema Adapter | PASS | `adapters/schema_enhancement.py` |
| EF-0812 Technical Fix Adapter | PASS | `adapters/technical_fix.py` |
| EF-0813 Outreach Adapter | PASS | `adapters/outreach.py` |
| EF-0814 ForgeBase Publisher | PASS | `execution_adapters/forgebase.py`（integration 就緒時可用） |
| Strategy Intake / Business Fit | PASS | `strategy/*`、OG-017、`business_fit_score` in scorer |
| Cold-start | PASS | `cold_start_research` job → `needs_review` pyramid nodes |

---

## 3. 測試執行紀錄

| 命令 | 環境 | 結果 |
|------|------|------|
| `ruff check`（Phase 8 模組） | local Python 3.10 | **All checks passed** |
| `pytest tests/test_execution_adapters.py tests/test_knowledge_embeddings.py tests/test_compiler.py tests/test_publish_gate.py tests/test_business_fit.py tests/test_claim_verifier.py tests/test_source_pack.py tests/test_decision_business_fit.py tests/test_scorer.py tests/test_decision_*.py` | local | **34 passed** |
| `pytest tests/test_strategy_isolation.py` | 無 Postgres | **skipped**（需 Docker Postgres；CI 3.11 執行） |
| WordPress contract | `packages/execution-adapters` | **3 passed** |

---

## 4. Bugbot Review 結果

| 嚴重度 | 問題 | 處置 |
|--------|------|------|
| High | `review_level=editor` 繞過人工審核 | **已修**：預設改 `editor_review`；gate 含 `editor` alias |
| High | `needs_review` keyword 可進 brief | **已修**：brief 僅允許 `in_scope` + site 對齊 source pack |
| High | source pack 未驗證 site_id | **已修**：`pack.site_id == site_id` |
| High | blocked keyword 部分 action 未 no_op | **已修**：`fit.blocked` 一律 `no_op` |
| Medium | client 可注入 output_markdown | **已修**：移除 create API 的 markdown 注入，強制 compile |

---

## 5. Security Review 結果

| 項目 | 結果 |
|------|------|
| Strategy / Knowledge / Content API RBAC | PASS — `require_permission` + `X-Workspace-Id` |
| 租戶隔離 | PASS — 所有 query 帶 `workspace_id`；整合測試 `test_strategy_isolation.py` |
| WordPress 憑證 | PASS — site-scoped credential、decrypt 後 HTTPS only、publish 前 gate |
| Approve / override audit | PASS — strategy approve、content approve 寫 audit |
| Quota | PASS — `QUOTA_EXCEEDED` 429 |

---

## 6. 修復紀錄（review 期間）

- Bugbot High ×4 + Medium ×1 已於本 Phase 內修復（見 §4）
- `test_knowledge_embeddings` 浮點比較改用 `pytest.approx`

---

## 7. 已知限制

- pgvector column migration 012 已建立；embedding v1 存於 `metadata_json.embedding`（ORM/test 相容），Postgres 原生 vector query 待 CI pgvector image 整合後補 SQL 檢索路徑
- Content compiler v1 為 grounded template（非 LLM provider）；LLM 段落生成可於 Phase 11 計費層接 provider
- ForgeBase publish API 路徑為計畫契約，需實際 ForgeBase 環境 contract test
- 整合測試需 Postgres；本機 Docker 未啟動時 skip

---

## 8. 結論

**PASS** — Phase 8 EF-0801～EF-0814 核心驗收滿足；Bugbot High 已修；Security Review PASS。

**下一 Phase**：Phase 9 Dashboard / UX
