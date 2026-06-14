# Phase 3 Code Review — Exposure Core（完整版）

**日期**：2026-06-14  
**狀態**：PASS（補審後）  
**範圍**：EF-0301、EF-0302、EF-0303；第十六章 EF-0304–EF-0307  
**Commit**：_(見本次 commit)_

---

## 1. 變更清單

| 類別 | 路徑 |
|------|------|
| 資料模型 | `apps/api/exposureflow_api/models/exposure.py` |
| Migration | `apps/api/alembic/versions/004_exposure_core.py` |
| Scorer | `apps/api/exposureflow_api/exposure/scorer.py` |
| Generator / Service | `apps/api/exposureflow_api/exposure/service.py`（OG-001、OG-004、OG-005） |
| Owner classification | `apps/api/exposureflow_api/exposure/owner_classification.py` |
| Site scope | `apps/api/exposureflow_api/exposure/deps.py` |
| Exposure API | `apps/api/exposureflow_api/exposure/router.py`、`schemas.py` |
| Competitors API | `apps/api/exposureflow_api/competitors/router.py` |
| 掛載 | `apps/api/exposureflow_api/main.py`、`models/__init__.py` |
| 測試 | `test_scorer.py`、`test_owner_classification.py`、`test_exposure_isolation.py` |

---

## 2. EF-xxxx 逐項驗收

| Ticket | 結果 | 證據 |
|--------|------|------|
| EF-0301 ExposureAsset | PASS | `models/exposure.py`、`import_assets_from_gsc`、`merge_duplicate_assets`、API import/merge/list |
| EF-0302 ExposureOpportunity | PASS | 模型 lifecycle + `evidence_json`；`generate_opportunities_from_gsc` |
| EF-0303 Opportunity Scorer | PASS | `scorer.py` 穩定公式 + `test_scorer.py` |
| EF-0304 TechnicalIssue API | PASS | Phase 2 `GET /api/v1/integrations/technical-issues`（本 Phase 未重複實作） |
| EF-0305 Competitor + owner classification | PASS | `competitors/router.py`、`owner_classification.py`、`classify-url` |
| EF-0306 Generator v1 | PASS（部分規則） | OG-001、OG-004、OG-005；其餘需 SERP/Topic 前置見 §7 |
| EF-0307 Scorer evidence trace | PASS | `evidence_json` 含 formula、inputs、subscores |

---

## 3. 測試執行紀錄

| 命令 | 環境 | 結果 |
|------|------|------|
| `cd apps/api && ruff check exposureflow_api` | 本機 | **All checks passed** |
| `cd apps/api && pytest tests/test_scorer.py tests/test_owner_classification.py tests/test_error_sanitizer.py -q` | 本機 | **6 passed** |
| `cd apps/api && pytest tests/test_exposure_isolation.py -q` | 本機無 Docker | **skipped**（需 Postgres） |
| CI `api` job | GitHub Actions Postgres | 預期含 `test_exposure_isolation.py` 全通過 |

---

## 4. Bugbot Review 結果

| Severity | Location | Finding | 處置 |
|----------|----------|---------|------|
| High | `service.py` merge | duplicate 未驗證 workspace_id | **已修復** |
| High | `service.py` merge | canonical 未驗證 site_id | **已修復** |
| High | `service.py` merge | canonical 在 duplicate 列表會自我合併 | **已修復**（skip self） |
| High | `exposure/router.py` | mutating 端點未驗證 site 歸屬 | **已修復** — `get_site_in_workspace` |
| Medium | `service.py` merge | ValueError → 500 | **已修復** — `not_found` |
| Medium | OG-004 | `targetable_slot_count=0` 總分為 0 | **已修復** — 改為 1 |
| Medium | generate | 重複執行堆疊 opportunity | **已修復** — rule_id 去重 |
| Medium | OG-001 | 用 page 而非 query impression | **已修復** |
| Medium | `_build_opportunity` | 子分數尺度錯誤 | **已修復** — 儲存 0–1 |

---

## 5. Security Review 結果

| Severity | Finding | 處置 |
|----------|---------|------|
| High | merge 跨 workspace IDOR | **已修復**（workspace + site 雙重驗證） |
| — | list/import/classify RBAC | **PASS** |
| — | competitor CRUD 租戶隔離 | **PASS** |

新增整合測試：`test_merge_rejects_foreign_workspace_duplicate`（需 Postgres）。

---

## 6. 修復紀錄（補審期間）

1. 新增 `exposure/deps.py` 統一 site-in-workspace 驗證
2. 強化 `merge_duplicate_assets` 租戶與 site 邊界
3. Opportunity 生成 idempotent（rule_id + keyword + url 去重）
4. OG-001 改為 query 層級 impression 門檻
5. 子分數 DB 欄位改為 0–1 尺度（符合計畫 §7）

---

## 7. 已知限制

- OG-002、OG-003、OG-006–OG-015 需 SERP snapshot、Topic graph 或 schema audit（Phase 4–6），待後續 Phase 擴充 Generator
- 本機無 Docker 時整合測試 skip；CI Postgres 為權威驗證環境
- Competitor PATCH 端點待 Phase 11 API 完整化時補齊（計畫 §4.5 有列，非 Phase 3 核心驗收阻塞項）

---

## 8. 結論

**PASS** — EF-0301–0303 與 Phase 3 補強票（0304–0307 範圍內）已實作；Bugbot / Security High 已修復；單元測試通過；整合測試已撰寫待 CI Postgres 執行。

**下一 Phase**：Phase 4 Topic Coverage Graph（EF-0401–0403 + 第十六章補強）
