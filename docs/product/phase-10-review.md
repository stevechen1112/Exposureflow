# Phase 10 Code Review — Reporting / Client Deliverables

**Phase**：10 — Reporting / Client Deliverables  
**Review 日期**：2026-06-14  
**結論**：PASS（Bugbot / Security High 已修）

---

## 1. 變更清單

### 後端
| 路徑 | 說明 |
|------|------|
| `alembic/versions/013_reports.py` | reports 表 |
| `alembic/versions/014_client_deliverables.py` | delivery_mode、meeting_notes、annotations |
| `models/reporting.py` | Report ORM |
| `models/client_deliverables.py` | ClientMeetingNote、DeliveryAnnotation |
| `reporting/monthly_report.py` | 月報 Markdown 生成 |
| `reporting/delivery_reports.py` | Audit / Roadmap / Execution Tracker |
| `reporting/exporters.py` | Markdown / PDF / DOCX 匯出 |
| `reporting/router.py` | CRUD、generate、export、async job |
| `reporting/client_portal.py` | 客戶 dashboard 聚合 |
| `reporting/client_router.py` | client portal API、核准、月會、批註 |
| `reporting/service.py` | roadmap client approval（含 site 驗證） |
| `jobs/handlers/report_monthly_generate.py` | `report.monthly.generate` |
| `auth/permissions.py` | `client:approve` 權限 |

### 前端
| 路徑 | 說明 |
|------|------|
| `apps/web/app/(client-portal)/client/[workspaceId]/page.tsx` | 客戶入口 UI |
| `packages/sdk` | reports / client portal / export 方法 |

### 測試
| 路徑 | 說明 |
|------|------|
| `tests/test_report_exporters.py` | MD/PDF/DOCX 匯出 |
| `tests/test_reporting_delivery.py` | delivery mode 映射 |
| `tests/test_client_approval.py` | 核准 service + site mismatch 403 |

---

## 2. EF-xxxx 逐項驗收

| EF | 狀態 | 證據 |
|----|------|------|
| EF-1001 自然曝光月報 | PASS | `build_monthly_exposure_markdown` + `POST /reports/monthly-exposure` + export md/pdf/docx |
| EF-1002 顧問交付模式 | PASS | delivery_mode: audit/roadmap/monthly_retainer/execution_tracker；client portal；核准/月會/批註；白標 branding_json |

---

## 3. 測試執行紀錄

| 命令 | 結果 |
|------|------|
| `ruff check exposureflow_api/reporting` | PASS |
| `pytest tests/test_report_exporters.py tests/test_reporting_delivery.py tests/test_client_approval.py` | 8 passed |
| `pnpm --filter @exposureflow/web build` | PASS（含 `/client/[workspaceId]`） |
| Postgres 整合測試 reports tenant isolation | SKIP（本機 Docker 未啟動；API 層 workspace_id + get_site_in_workspace） |

---

## 4. Bugbot Review

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | `tenants_router` import 遺失 | **已修** — `main.py` |
| High | `run_execution_job` import 遺失 | **已修** — `handlers/__init__.py` |
| High | brief needs_review（Phase 8） | known_limitations |
| Medium | UsageEvent import | **已修** — `models/__init__.py` |

---

## 5. Security Review

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | client approve 未綁 site_id | **已修** — `ClientApprovalRequest.site_id` + service 403 |
| — | 跨 workspace 報表讀取 | PASS — workspace_id 比對 |

---

## 6. 修復紀錄

- main.py tenants_router import
- execution job handler import
- client approval site_id 驗證
- UsageEvent model export

---

## 7. 已知限制

- Clerk 客戶登入 Phase 11
- PDF 中文以 latin-1 降級（白標英文場景優先；中文 PDF 待字型嵌入）
- reports / client-portal Postgres 跨 workspace 整合測試待 CI
- Python 3.10 本機無法 import 全 app（datetime.UTC）；CI 3.11

---

## 8. 結論

**PASS** — EF-1001、EF-1002 交付完成；三格式匯出、四種 delivery mode、client portal 與核准流程就緒。Commit 待使用者指示。
