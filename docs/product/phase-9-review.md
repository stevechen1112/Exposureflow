# Phase 9 Code Review — Dashboard / UX

**Phase**：9 — Dashboard / UX  
**Review 日期**：2026-06-14  
**結論**：PASS（修復 Bugbot / Security High 後）

---

## 1. 變更清單

### 後端
| 路徑 | 說明 |
|------|------|
| `apps/api/exposureflow_api/exposure/dashboard.py` | 曝光 KPI 聚合 |
| `apps/api/exposureflow_api/exposure/router.py` | `GET /api/v1/exposure/dashboard` |
| `apps/api/exposureflow_api/exposure/schemas.py` | `DashboardResponse`、topic cluster 項目 |
| `apps/api/exposureflow_api/ai_visibility/dashboard.py` | AI 能見度儀表板聚合 |
| `apps/api/exposureflow_api/ai_visibility/router.py` | `GET /api/v1/ai-visibility/dashboard` |
| `apps/api/exposureflow_api/decision/outcomes.py` | 行動成果列表 |
| `apps/api/exposureflow_api/decision/router.py` | `GET /api/v1/outcomes` |
| `apps/api/exposureflow_api/decision/candidate_generator.py` | blocked 候選不再獲 technical rank boost |
| `apps/api/exposureflow_api/content/service.py` | claim_blocked 需 override；re-compile 使 claim gate stale |
| `apps/api/exposureflow_api/execution/publish_gate.py` | stale claim gate 阻擋 publish |

### 前端（Next.js 15）
| 路徑 | 說明 |
|------|------|
| `apps/web/app/(dashboard)/app/[workspaceId]/sites/[siteId]/*` | EF-0901–0904、EF-0905–0910 全路由 |
| `apps/web/components/AppShell.tsx` | 側欄導航 |
| `apps/web/components/SessionBootstrap.tsx` | dev auth 環境閘門 |
| `apps/web/lib/api-client.ts`、`lib/hooks.ts` | API client 與 site context |
| `packages/sdk/src/index.ts` | 擴充 SDK 方法 |
| `packages/shared-types/src/index.ts` | Dashboard / AI 型別 |

### 測試
| 路徑 | 說明 |
|------|------|
| `apps/api/tests/test_exposure_dashboard.py` | dashboard 聚合單元測試 |
| `apps/api/tests/test_decision_candidate_generator.py` | blocked technical 不加分 |
| `apps/web/components/KpiCard.test.tsx` | component smoke test |

---

## 2. EF-xxxx 逐項驗收

| EF | 狀態 | 證據 |
|----|------|------|
| EF-0901 Exposure Dashboard | PASS | `dashboard/page.tsx` + `GET /exposure/dashboard` + KPI 卡片 |
| EF-0902 Opportunity Queue UI | PASS | `opportunities/page.tsx` approve/reject/defer + bulk |
| EF-0903 SERP Matrix UI | PASS | `serp-matrix/page.tsx` + matrix grid + snapshot list |
| EF-0904 AI Visibility UI | PASS | `ai-visibility/page.tsx` probe sets + citations + SERPO KPI |
| EF-0905 Exposure Map UI | PASS | `exposure-map/page.tsx` clusters + nodes |
| EF-0906 Technical Issues UI | PASS | `technical-issues/page.tsx` + crawl trigger |
| EF-0907 Action Outcomes UI | PASS | `outcomes/page.tsx` + `GET /outcomes` |
| EF-0908 Settings / Integrations | PASS | `settings/*` sync states + GSC/crawl trigger |
| EF-0909 Onboarding UI | PASS | `onboarding/page.tsx` checklist + 進入儀表板 |
| EF-09010 Brand / SERPO UI | PASS | `brand/page.tsx`、`serpo/page.tsx` |

---

## 3. 測試執行紀錄

| 命令 | 環境 | 結果 |
|------|------|------|
| `ruff check exposureflow_api`（Phase 9 相關檔） | Python 3.10 | PASS |
| `pytest tests/test_exposure_dashboard.py tests/test_decision_candidate_generator.py -q` | 本機 | 8 passed |
| `pnpm --filter @exposureflow/web lint` | Node 22 | PASS |
| `pnpm --filter @exposureflow/web test` | Vitest | 1 passed |
| `pnpm --filter @exposureflow/web build` | Next.js 15 | PASS（21 routes） |
| Postgres 整合測試（tenant isolation on new APIs） | Docker 未啟動 | SKIP — 新 API 沿用 `get_site_in_workspace` 模式；CI 3.11 執行 |

---

## 4. Bugbot Review 結果

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | blocked technical 仍 +25 rank | **已修** — `candidate_generator.py` |
| High | claim_blocked 無 override 可 approve | **已修** — `content/service.py` |
| Medium | home redirect demo slug | **已修** — 錯誤訊息取代硬編碼 demo |
| Medium | brief needs_review | 已知 — Phase 8 business fit 邊界，非 Phase 9 阻塞 |
| Medium | claim 重複 insert | 已知 — 記錄於 known_limitations |

---

## 5. Security Review 結果

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | 無條件 dev-token + localStorage | **已修** — `DEV_AUTH_ENABLED` 閘門 |
| High | re-compile 後 stale claim gate | **已修** — invalidate + publish_gate |
| — | 新 dashboard API 租戶隔離 | PASS — require_permission + get_site_in_workspace |

Clerk 正式登入：Phase 11 範圍；本 Phase 本機以 `NEXT_PUBLIC_ENABLE_DEV_AUTH=true` 開發。

---

## 6. 修復紀錄

- Bugbot High：blocked rank boost、claim_blocked approve
- Security High：dev auth 閘門、stale claim gate
- ESLint：Fragment import、useCallback for load
- SDK：重複 export 型別衝突

---

## 7. 已知限制

- 正式 Clerk UI 尚未接入（Phase 11）
- Dashboard / outcomes API 缺 Postgres 跨 workspace 整合測試（本 session Docker 未啟動）
- Python 3.10 本機部分舊測試 `datetime.UTC` import 失敗（CI 3.11）
- Content review 頁目前列出 execution jobs，非完整 generation run 審核 UI（gate API 需 job_id）

---

## 8. 結論

**PASS** — EF-0901 至 EF-0910 交付完成；lint / unit test / web build 通過；Bugbot 與 Security High 已修復。Commit 待使用者指示。
