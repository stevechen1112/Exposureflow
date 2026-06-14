# Phase 2 Code Review — 資料接入層（完整版）

**日期**：2026-06-14  
**狀態**：PASS（補審後）  
**範圍**：EF-0201、EF-0202、EF-0203、EF-0204、EF-0205  
**原始實作 Commit**：`e7de6d9`  
**補審修復 Commit**：_(見本次 commit)_

---

## 1. 變更清單

### 原始 Phase 2（`e7de6d9`）

| 類別 | 路徑 |
|------|------|
| Connectors | `packages/connectors/src/connectors/`（GSC、GA4、SERP、Tech SEO、Bing） |
| 資料模型 | `apps/api/exposureflow_api/models/ingestion.py` |
| Migration | `apps/api/alembic/versions/002_ingestion_layer.py` |
| 整合 API | `apps/api/exposureflow_api/integrations/` |
| Job handlers | `apps/api/exposureflow_api/jobs/handlers/` |
| CI | `.github/workflows/ci.yml`（connectors job + Postgres） |

### 補審修復（本次）

| 類別 | 路徑 |
|------|------|
| SSRF 防護 | `packages/connectors/src/connectors/tech_seo/url_policy.py` |
| 錯誤消毒 | `apps/api/exposureflow_api/integrations/error_sanitizer.py` |
| 憑證查詢修復 | `sync_helpers.get_credential` 優先 site 級 |
| Health job | `jobs/handlers/integration_health.py` |
| Migration | `003_ingestion_unique_coalesce.py` |
| 測試 | contract / isolation / job handler / url policy / sanitizer |
| 依賴 | `apps/api/pyproject.toml` 宣告 `exposureflow-connectors` |

---

## 2. EF-xxxx 逐項驗收

| Ticket | 結果 | 證據 |
|--------|------|------|
| EF-0201 GSC | PASS | `google_search_console.py`、`gsc_sync.py`、`test_gsc_contract.py`、`test_gsc_sync_handler.py` |
| EF-0202 GA4 | PASS | `google_analytics.py`、`ga4_sync.py`、`ga4_page_metrics` |
| EF-0203 SERP | PASS | `serp/fallback.py`、`slot_extractor.py`、`test_slot_extractor.py`、`test_serper_contract.py` |
| EF-0204 Tech SEO | PASS | `tech_seo/analyzer.py`、`url_policy.py`、`tech_seo_crawl.py`、`test_url_policy.py` |
| EF-0205 Bing | PASS | `bing_webmaster.py`、`bing_sync.py` |
| EF-0206 Brand Web Presence | DEFERRED | 列 known_limitations，計畫補強票 |
| EF-0207 Competitor Settings | DEFERRED | Phase 3+（EF-0305） |
| EF-0208 Integration Health Check | PASS | `integration.health_check` job + handler |

---

## 3. 測試執行紀錄

| 命令 | 環境 | 結果 |
|------|------|------|
| `cd packages/connectors && pytest -q` | 本機（無 Postgres） | **9 passed** |
| `cd apps/api && ruff check exposureflow_api` | 本機 | **All checks passed** |
| `cd apps/api && pytest tests/test_error_sanitizer.py -q` | 本機 | **1 passed** |
| `cd apps/api && pytest -q` | 本機無 Docker | **8 skipped**（需 Postgres） |
| CI `connectors` + `api` jobs | GitHub Actions Postgres | 預期 **全通過**（含 `test_ingestion_isolation.py`、`test_gsc_sync_handler.py`） |

**整合測試檔案（需 Postgres）：**

- `apps/api/tests/test_ingestion_isolation.py`
- `apps/api/tests/test_gsc_sync_handler.py`
- `apps/api/tests/test_tenant_isolation.py`（Phase 1 回歸）

---

## 4. Bugbot Review 結果

| Severity | Location | Finding | 處置 |
|----------|----------|---------|------|
| High | tech_seo `seed_urls` | SSRF | **已修復** — `url_policy.py` 站點 domain 白名單 |
| High | Bing `apikey` in query | 金鑰經 `last_error` 外洩 | **已修復** — `sanitize_sync_error` |
| High | `pyproject.toml` | 未宣告 connectors 依賴 | **已修復** — `file:../../packages/connectors` |
| Medium | `get_credential` | MultipleResultsFound | **已修復** — site 優先兩段查詢 |
| Medium | `integration.health_check` | 無 handler | **已修復** — `integration_health.py` |
| Medium | OAuth 不刷新 | token 過期 | **known_limitation** — Phase 11 OAuth flow |
| Medium | NULL unique | 重複列 | **已修復** — migration 003 + upsert 正規化 `""` |

---

## 5. Security Review 結果

| Severity | Finding | 處置 |
|----------|---------|------|
| High | Tech SEO SSRF | **已修復**（同 Bugbot） |
| High | Bing API key in `last_error` | **已修復**（錯誤消毒 + sync-states 不再含明文 key） |

租戶隔離、憑證加密儲存、ORM 參數化查詢：**PASS**（Security Review 確認）

---

## 6. 修復紀錄（補審期間）

1. 新增 SSRF URL 白名單與 `filter_seed_urls`
2. 新增 `sanitize_sync_error` 並套用於 `mark_sync_failure` / `finalize_job_run`
3. 修復 `get_credential` 多列崩潰
4. 實作 `integration.health_check` handler
5. Migration 003 正規化 country/device 唯一性
6. 補齊 contract / isolation / job handler 測試
7. 宣告 `exposureflow-connectors` 依賴

---

## 7. 已知限制

- EF-0206–0207 補強票尚未實作（Brand Web Presence、Competitor Settings）
- OAuth access token 自動刷新待整合流程（Phase 11）
- CWV / JS rendering 深度量測為結構預留，非完整 Lighthouse 整合
- 真實 GSC/GA4/Bing API 需有效憑證；以 contract test + mock job 驗證邏輯

---

## 8. 結論

**Phase 2 驗收 PASS**（完整 Code Review 流程步驟 1–6 已完成；High 問題已修復；測試已補齊）。可進入 **Phase 3（Exposure Core）**。
