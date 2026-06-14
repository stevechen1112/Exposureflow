# Phase 4 Code Review — Topic Coverage Graph（完整版）

**日期**：2026-06-14  
**狀態**：PASS（補審後）  
**範圍**：EF-0401、EF-0402、EF-0403；第十六章 EF-0404、EF-0405  
**Commit**：_(見本次 commit)_

---

## 1. 變更清單

| 類別 | 路徑 |
|------|------|
| 資料模型 | `apps/api/exposureflow_api/models/topic.py` |
| Migration | `apps/api/alembic/versions/005_topic_graph.py` |
| Graph builder | `apps/api/exposureflow_api/topics/graph_builder.py` |
| Cannibalization | `apps/api/exposureflow_api/topics/cannibalization.py` |
| Internal links | `apps/api/exposureflow_api/topics/internal_links.py` |
| Service / API | `topics/service.py`、`topics/router.py`、`topics/schemas.py` |
| Job | `jobs/handlers/topic_graph_rebuild.py`、`jobs/registry.py` |
| 測試 | `test_graph_builder.py`、`test_cannibalization.py`、`test_internal_links.py`、`test_topic_isolation.py` |

---

## 2. EF-xxxx 逐項驗收

| Ticket | 結果 | 證據 |
|--------|------|------|
| EF-0401 Topic Graph | PASS | GSC co-occurrence、SERP overlap、URL hierarchy、token similarity；`ExposureTheme`/`TopicCluster`/`TopicNode` |
| EF-0402 Cannibalization | PASS | `detect_gsc_cannibalization` + semantic；`CannibalizationCase` + node status |
| EF-0403 Internal Link | PASS | `suggest_internal_links` + approval API |
| EF-0404 TopicNode API | PASS | `GET/PATCH /api/v1/topics/nodes` |
| EF-0405 Manual lock | PASS | `cluster_assignment_locked`；rebuild 跳過鎖定節點；audit log |

---

## 3. 測試執行紀錄

| 命令 | 環境 | 結果 |
|------|------|------|
| `ruff check exposureflow_api` | 本機 | **All checks passed** |
| `pytest tests/test_graph_builder.py tests/test_cannibalization.py tests/test_internal_links.py -q` | 本機 | **10 passed** |
| `pytest tests/test_topic_isolation.py -q` | 本機無 Docker | **skipped**（需 Postgres） |
| CI `api` job | GitHub Actions Postgres | 預期全通過 |

---

## 4. Bugbot Review 結果

| Severity | Finding | 處置 |
|----------|---------|------|
| High | rebuild 刪 cluster 時 InternalLinkSuggestion FK 失敗 | **已修復** — 先刪 suggestions |
| Medium | semantic cannibalization 漏標 paired query | **已修復** |
| Medium | gap 節點無 URL 無法產生內鏈 | **已修復** — proposed_page URL |
| Medium | rebuild-sync 未跑 cannibalization | **已修復** |

---

## 5. Security Review 結果

| 結論 | 說明 |
|------|------|
| **PASS** | 跨 workspace IDOR 已阻擋；rebuild 全程 tenant + site scoped |
| Hardening | `get_cluster` 補 `get_site_in_workspace` |

---

## 6. 修復紀錄

1. rebuild 前刪除將移除 cluster 的 internal link suggestions
2. semantic cannibalization 同步標記 paired query
3. gap 節點以 `proposed_page` URL 產生內鏈建議
4. `rebuild-sync` 與 job handler 行為對齊

---

## 7. 已知限制

- 真實 embedding / Leiden clustering 待向量化基礎設施就緒後升級（目前以 token Jaccard 代理語意邊）
- OG-006+ 需 topic graph 整合至 opportunity generator（Phase 5+）
- 整合測試需 CI Postgres

---

## 8. 結論

**PASS** — Phase 4 核心驗收滿足；Bugbot High 已修復；Security Review 無 medium+ 問題。

**下一 Phase**：Phase 5 SERP Slot Matrix
