# Phase 2 Code Review — 資料接入層

**日期**：2026-06-14  
**狀態**：PASS  
**範圍**：EF-0201、EF-0202、EF-0203、EF-0204、EF-0205

## EF-0201 GSC Connector

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| OAuth / service account 支援 | PASS | `connectors/google_search_console.py` |
| query/page/date/country/device 匯入 | PASS | `GSCClient.fetch_search_analytics` |
| 寫入 `gsc_performance_rows` | PASS | `models/ingestion.py` + `upsert_gsc_rows` |
| incremental sync + 延遲處理 | PASS | `fetch_incremental`（3 天 lag）+ `integration_sync_states` |
| 查詢 API | PASS | `GET /api/v1/integrations/gsc/performance` |
| workspace 隔離 | PASS | 所有 row 含 `workspace_id` |

## EF-0202 GA4 Connector

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| page path / sessions / engagement / conversions | PASS | `connectors/google_analytics.py` |
| 寫入 `ga4_page_metrics` | PASS | `upsert_ga4_rows` |
| 標記為輔助資料 | PASS | API response `auxiliary: true` |
| 對應 ExposureAsset 前置 | PASS | `page_path` 欄位可供 Phase 3 映射 |

## EF-0203 SERP Connector

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| Serper / SerpAPI fallback | PASS | `connectors/serp/fallback.py` |
| snapshot persistence | PASS | `serp_query_snapshots` + `serp_slots` |
| slot extraction | PASS | `connectors/serp/slot_extractor.py` |
| organic / PAA / related / featured / image / video / product / forum / ai_overview | PASS | extractor + unit tests |
| country / language / device | PASS | job input + snapshot 欄位 |

## EF-0204 Technical SEO Connector

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| robots / sitemap / noindex / canonical / redirect / 404 / schema | PASS | `connectors/tech_seo/analyzer.py` |
| 寫入 `technical_issues` | PASS | `jobs/handlers/tech_seo_crawl.py` |
| AI crawler access 檢查 | PASS | Googlebot、Bingbot、OAI-SearchBot、PerplexityBot、GPTBot |

## EF-0205 Bing Webmaster Connector

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| Bing query stats 同步 | PASS | `connectors/bing_webmaster.py` |
| 寫入 `bing_performance_rows` | PASS | `upsert_bing_rows` |
| incremental sync | PASS | `integration_sync_states` + `bing.sync` job |

## 基礎設施

| 檢查項 | 結果 | 證據 |
|--------|------|------|
| Alembic migration 002 | PASS | `alembic/versions/002_ingestion_layer.py` |
| Job handlers 路由 | PASS | `jobs/handlers/__init__.py` |
| Integrations API | PASS | `integrations/router.py` |
| Connectors 套件 + CI | PASS | `packages/connectors/` + `.github/workflows/ci.yml` |
| Slot extractor 測試 | PASS | `packages/connectors/tests/test_slot_extractor.py` |

## 已知限制

- 實際 GSC / GA4 / Bing API 呼叫需有效 OAuth 或 service account 憑證（由 IntegrationCredential 管理）。
- SERP 需設定 `SERPER_API_KEY` 或 `SERPAPI_API_KEY` 環境變數。
- CWV 與 JavaScript rendering 風險在 Phase 2 以結構化 issue type 預留，深度量測待後續 Phase 擴充。
- EF-0206–0208（Brand Web Presence、Competitor Settings、Integration Health Check）列於計畫補強，將於 Phase 3 前後銜接。

## 結論

Phase 2 驗收 **PASS**，可進入 Phase 3（Exposure Core）。
