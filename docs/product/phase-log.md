# ExposureFlow Phase 執行紀錄

本文件記錄各 Phase 完成狀態，供跨 session 延續開發使用。  
執行準則見根目錄 **`AGENTS.md` 憲章四原則**。

**驗收規則：**

- 驗收單位 = **一個 Phase**
- 每 Phase：完整 Code Review → 修復 → Commit → 標記 `completed` → **直接進下一 Phase**
- **不需**每 Phase 向使用者確認
- **唯一使用者回報**：Phase 0–14 全部完成後

## 狀態說明

- `pending`：尚未開始
- `in_progress`：進行中
- `review`：實作完成，review / 測試中
- `completed`：review 通過且已 commit
- `blocked`：阻塞，需記錄原因

## Phase 總表

| Phase | 名稱 | 狀態 | Commit | 完成日期 | 備註 |
|-------|------|------|--------|----------|------|
| 0 | 產品核心定義 | completed | 791ec51 | 2026-06-14 | EF-0001、EF-0002 |
| 1 | 多租戶基礎架構 | completed | 06d85f4 | 2026-06-14 | EF-0101–0104 |
| 2 | 資料接入層 | in_progress | — | — | EF-0201–0205 |
| 3 | Exposure Core | pending | — | — | |
| 4 | Topic Graph | pending | — | — | |
| 5 | SERP Matrix | pending | — | — | |
| 6 | AI Visibility | pending | — | — | |
| 7 | Decision Plane | pending | — | — | |
| 8 | Execution Plane | pending | — | — | |
| 9 | Dashboard / UX | pending | — | — | |
| 10 | Reporting | pending | — | — | |
| 11 | SaaS Commercial | pending | — | — | |
| 12 | Security / Reliability | pending | — | — | |
| 13 | Internal Admin / CS | pending | — | — | |
| 14 | Production Launch | pending | — | — | |

## Phase 詳細紀錄

---

### Phase 0 — 產品核心定義

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- `docs/product/product-north-star-spec.md`（EF-0001）
- `docs/product/kpi-taxonomy.md`（EF-0001）
- `docs/product/contentflow-reuse-boundary.md`（EF-0002）
- `docs/product/contentflow-porting-map.md`（EF-0002）
- `docs/product/phase-0-review.md`

**驗收證據：**

- EF-0001 / EF-0002 檢查表全數 PASS（見 `phase-0-review.md`）
- KPI 映射矩陣覆蓋全部核心模組（`kpi-taxonomy.md` §9）
- ContentFlow 基準：`977734cc` @ `git@github.com:stevechen1112/ContentFlow.git`

**已知限制：**

- 無（Phase 0 為定義階段，無程式碼變更）

---

### Phase 1 — 多租戶基礎架構

**狀態**：completed  
**完成日期**：2026-06-14

**交付物：**

- 租戶模型與 Alembic migration（`apps/api/exposureflow_api/models/`、`alembic/versions/001_initial_tenant.py`）
- 租戶 API（workspaces、sites、members、invitations、integrations、api-keys、jobs）
- RBAC 權限矩陣（`auth/permissions.py`）
- Celery job 基礎（`jobs/`）
- Audit log helper（`common/audit.py`）
- 2FA / impersonation endpoints（`auth/router.py`）
- 整合測試（`tests/test_tenant_isolation.py`）
- `docs/product/phase-1-review.md`

**驗收證據：**

- EF-0101–0104 檢查表全數 PASS（見 `phase-1-review.md`）
- `ruff check exposureflow_api` 通過
- CI 含 Postgres service 執行 pytest

**已知限制：**

- 生產認證待 Phase 11 接入 Clerk
- Job handler 為佔位，實際 connector 邏輯於 Phase 2

**下一 Phase 前置：**

- 開始 Phase 2：GSC / GA4 / SERP / Tech SEO / Bing connectors
