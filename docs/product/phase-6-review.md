# Phase 6 Code Review — AI Visibility Monitor（完整版）

**日期**：2026-06-14  
**狀態**：PASS  
**範圍**：EF-0601–0604；第十六章 EF-0605–0608  
**Commit**：_(見本次 commit)_

---

## 1. 變更清單

| 類別 | 路徑 |
|------|------|
| 模型 | `models/ai_visibility.py` |
| Migration | `alembic/versions/007_ai_visibility.py` |
| Citation | `ai_visibility/citation_extractor.py` |
| Brand | `ai_visibility/brand_monitor.py` |
| Entity | `ai_visibility/entity_checker.py` |
| SERPO | `ai_visibility/serpo.py` |
| Import | `ai_visibility/import_probe.py` |
| Opportunities | `ai_visibility/opportunities.py`（OG-010、OG-011） |
| Service / API | `ai_visibility/service.py`、`router.py`、`schemas.py` |
| 測試 | `test_ai_*.py`、`test_ai_visibility_isolation.py` |

---

## 2. EF-xxxx 逐項驗收

| Ticket | 結果 | 證據 |
|--------|------|------|
| EF-0601 AI Probe Framework | PASS | `AIProbeSet`、prompt/surface list、assisted manual run |
| EF-0602 AI Citation Extractor | PASS | URL 抽取 + owner 分類 → `AICitation` |
| EF-0603 Brand Mention / Sentiment | PASS | `BrandMention`、visibility score API |
| EF-0604 Entity Consistency | PASS | `entity-check`、OG-011 |
| EF-0605 assisted manual flow | PASS | `POST /runs/assisted` |
| EF-0606 manual import | PASS | CSV/JSON `POST /runs/import` |
| EF-0607 AICitation table | PASS | 正規化 `ai_citations` |
| EF-0608 SERPO Monitor | PASS | `SerpoRecord` + capture API |

---

## 3. 測試執行紀錄

| 命令 | 結果 |
|------|------|
| `ruff check exposureflow_api` | **All checks passed** |
| `pytest tests/test_ai_*.py`（unit） | **10 passed** |
| `pytest tests/test_ai_visibility_isolation.py` | skip（需 Postgres，CI 執行） |

---

## 4. Bugbot Review 結果

| Severity | Finding | 處置 |
|----------|---------|------|
| High | import 未驗證 probe_set 租戶 | **已修復** — `validate_probe_set` |
| High | OG-010 誤用品牌提及 | **已修復** — `external_url_cited` |
| High | 多筆 BrandEntity 500 | **已修復** — 取最新一筆 |
| Medium | probe_set site 不一致 | **已修復** |
| Medium | topic_cluster 未驗證 | **已修復** |
| Medium | OG-010 重複機會 | **已修復** — dedup |
| Medium | SERPO 未篩選 brand_query | **已修復** |

---

## 5. Security Review 結果

**PASS（修復後）**

| Severity | Finding | 處置 |
|----------|---------|------|
| High | import 跨租戶 probe_set 污染 | **已修復** |
| Medium | entity-check 以 read 寫入 | **已修復** — 改 `site:write` |

---

## 6. 修復紀錄

1. `validate_probe_set` 統一 workspace + site 驗證
2. runs 查詢加 `workspace_id` 過濾
3. `external_url_cited` 欄位支援 OG-010 URL 邏輯
4. entity-check 權限提升

---

## 7. 已知限制

- `automated_provider` 模式尚未串接外部 API（assisted manual / import 可完整運作）
- SERPO v1 以 brand mention 聚合，非完整 SERP crawl

---

## 8. 結論

**PASS** — Phase 6 核心驗收滿足。

**下一 Phase**：Phase 7 Decision Plane
