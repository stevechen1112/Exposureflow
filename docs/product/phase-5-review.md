# Phase 5 Code Review — SERP Slot Matrix（完整版）

**日期**：2026-06-14  
**狀態**：PASS  
**範圍**：EF-0501、EF-0502、EF-0503；第十六章 EF-0504、EF-0505  
**Commit**：_(見本次 commit)_

---

## 1. 變更清單

| 類別 | 路徑 |
|------|------|
| 模型 | `models/serp.py`（`SerpSlotTarget`） |
| Migration | `alembic/versions/006_serp_matrix.py` |
| Matrix | `serp/matrix.py`、`serp/service.py` |
| Opportunities | `serp/opportunities.py`（OG-002、OG-007、OG-008、OG-009） |
| Owner classification | `serp/owner.py`（EF-0505） |
| API | `serp/router.py`、`serp/schemas.py` |
| Job 整合 | `jobs/handlers/serp_snapshot.py` 同步 slot targets |
| 測試 | `test_serp_matrix.py`、`test_serp_opportunities.py`、`test_serp_owner.py`、`test_serp_isolation.py` |

---

## 2. EF-xxxx 逐項驗收

| Ticket | 結果 | 證據 |
|--------|------|------|
| EF-0501 SERP Slot Schema | PASS | `MATRIX_SLOT_TYPES`、matrix_status、snapshot → matrix |
| EF-0502 Featured Snippet / PAA | PASS | OG-002、OG-007 + `generate_serp_opportunities` |
| EF-0503 Image / Video / Product | PASS | OG-008、OG-009 規則與測試 |
| EF-0504 SERPSlotTarget API | PASS | `GET/PATCH /api/v1/serp/slot-targets` |
| EF-0505 SERP owner classification | PASS | `apply_owner_classification` + competitor registry |

---

## 3. 測試執行紀錄

| 命令 | 結果 |
|------|------|
| `ruff check exposureflow_api` | **All checks passed** |
| `pytest tests/test_serp_*.py`（unit） | **6 passed** |
| `pytest tests/test_serp_isolation.py` | skip（需 Postgres，CI 執行） |

---

## 4. Bugbot Review 結果

| Severity | Finding | 處置 |
|----------|---------|------|
| Medium | OG-008 image/video 共用 dedup key | **已修復** — 加入 `opportunity_type` |
| Medium | `build_site_matrix` 未驗證 cluster 歸屬 | **已修復** |
| Low | 重複 `db.flush()` in serp_snapshot | **已修復** |

---

## 5. Security Review 結果

**PASS** — 所有 SERP 端點使用 `get_site_in_workspace` + `workspace_id` 過濾；slot-target PATCH 驗證租戶；snapshot run 綁定 workspace job。

---

## 6. 修復紀錄

1. Opportunity 去重 key 加入 `opportunity_type`
2. Matrix `cluster_id` 驗證 site/workspace
3. 移除 serp_snapshot 重複 flush

---

## 7. 已知限制

- `has_image`/`has_video` 為 site 級判斷，未細分到 URL
- 整合測試需 CI Postgres

---

## 8. 結論

**PASS** — Phase 5 核心驗收滿足。

**下一 Phase**：Phase 6 AI Visibility Monitor
