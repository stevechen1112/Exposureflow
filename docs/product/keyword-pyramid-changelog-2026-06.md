# 關鍵字金字塔更動紀錄（2026-06）

**文件編號**：EF-KW-CHANGELOG-2026-06  
**狀態**：已部署 production（https://app.kakusinn.com）  
**關聯文件**：[`keyword-capability-gap-plan.md`](keyword-capability-gap-plan.md)、[`linode-deploy-runbook.md`](linode-deploy-runbook.md)

本文件記錄 2026-06 關於 **Keyword Pyramid（關鍵字金字塔）** 的完整更動：能力補強（KW-GAP）、部署事故、顧問操作 UX 修正，以及「正式納入」辨識性改版。

---

## 一、背景與目標

### 問題

對照 `exposureflow-development-plan.md`、`organic-impressions-seo-plan.md` 與 ContentFlow 關鍵字模組，ExposureFlow 的 Keyword Pyramid 原先僅是「資料容器」：

- Intake 推演產生大量 region×service 雜訊（如 `台中市換`）
- Cold-start 為 stub，無 SERP 研究
- 無 Pyramid ↔ Topic Graph 橋接
- 前端無樹狀視圖、批次匯入、bulk API
- 頁面無法一眼分辨「哪些字已正式納入專案 scope」

### 目標

1. **顧問可制定**：樹狀結構、product scope、目標字、批次匯入、編輯／核准／排除／刪除
2. **系統可研究**：Cold-start 接 Serper/SerpAPI，寫入 `evidence_json.enrichment`
3. **曝光可閉環**：核准節點連結 Topic Graph；Business Fit Gate（OG-017）
4. **UI 可理解**：正式納入 vs 待審草稿 vs 排除，視覺與文案一致

---

## 二、時程摘要

| 日期 | 項目 |
|------|------|
| 2026-06-15 | KW-GAP 後端／前端／SDK 實作；單元測試 11 passed |
| 2026-06-15 | 首次部署 Linode；Alembic revision 超長導致 api/worker 重啟循環 |
| 2026-06-15 | 修復 revision → `020_keyword_pyramid_bridge`；web `--no-cache` 重建 |
| 2026-06-15 | 瀏覽器驗收（ezfix）：Cold-start 面板、樹狀、sync bridge、曝光地圖 |
| 2026-06-15 | UX：編輯表單捲動、核准／排除確認、排除區恢復待審 |
| 2026-06-15 | UX：正式納入辨識改版（統計卡、綠色正式區、納入狀態 badge） |

---

## 三、後端更動（KW-001～KW-019）

### 3.1 Migration 020

**檔案**：`apps/api/alembic/versions/020_keyword_pyramid_enrichment_bridge.py`  
**Revision ID（production）**：`020_keyword_pyramid_bridge`（≤32 字元，符合 `alembic_version.version_num`）

新增欄位：

| 欄位 | 用途 |
|------|------|
| `topic_node_id` | 連結 Topic Graph 節點 |
| `topic_cluster_id` | 連結 Topic Cluster |
| `keyword_level` | head / mid_tail / long_tail |
| `funnel_stage` | tofu / mofu / bofu |
| `is_target` | 本季目標字（watchlist） |

### 3.2 新增／重寫模組

| 模組 | 路徑 | 說明 |
|------|------|------|
| Enrichment | `strategy/keyword_enrichment.py` | `evidence_json.enrichment`、SERP 版位計數 |
| Research | `strategy/keyword_research.py` | PAA/related 擴展、意圖／漏斗／level 推斷 |
| Bridge | `strategy/pyramid_topic_bridge.py` | 核准節點 → TopicNode/TopicCluster |
| Cold-start | `jobs/handlers/cold_start_research.py` | Serper/SerpAPI → `needs_review` 候選 |
| Extraction | `strategy/keyword_extraction.py` | 降噪：停用 bare region、短 service 組合 |
| Intake impact | `strategy/intake_impact.py` | apply 後 sync bridge；blocked → rejected |
| Service/Router | `strategy/service.py`、`router.py` | bulk-import、sync-topic-bridge、cold-start 參數 |
| Exposure | `exposure/service.py` | OG-017 blocked 不建 GSC opp；OG-016 pyramid create_page |

### 3.3 API 端點（新增或擴充）

```
GET    /api/v1/strategy/keyword-pyramid
POST   /api/v1/strategy/keyword-pyramid
PATCH  /api/v1/strategy/keyword-pyramid/{node_id}
DELETE /api/v1/strategy/keyword-pyramid/{node_id}
POST   /api/v1/strategy/keyword-pyramid/{node_id}/approve
POST   /api/v1/strategy/keyword-pyramid/bulk-import
POST   /api/v1/strategy/keyword-pyramid/sync-topic-bridge
POST   /api/v1/strategy/cold-start-research  （擴充 seed / PAA / related 參數）
```

### 3.4 `evidence_json.enrichment` 契約

```json
{
  "enrichment": {
    "targetable_slot_count": 3,
    "serp_features": ["paa", "featured_snippet", "related_search"],
    "paa_questions": ["..."],
    "related_searches": ["..."],
    "organic_top_domains": ["example.com"],
    "last_enriched_at": "2026-06-15T12:00:00Z",
    "source": "cold_start_serp",
    "provider": "serper"
  }
}
```

### 3.5 測試

- `apps/api/tests/test_keyword_enrichment.py`（新增）
- `apps/api/tests/test_keyword_extraction.py`（更新）
- 本地 pytest：extraction + enrichment + constraint_engine **11 passed**

### 3.6 刻意不在本次範圍

- DataForSEO **搜尋量／難度** enrichment（需額外 API 合約）
- Excel `.xlsx` 二進位上傳（以 CSV/文字 bulk API 代替）
- Keyword Pyramid 表單必填 search volume（ExposureFlow 以核准 scope + GSC 曝光為主，見產品討論）

---

## 四、前端／SDK 更動

### 4.1 頁面

**路徑**：`apps/web/app/(dashboard)/app/[workspaceId]/sites/[siteId]/keyword-pyramid/page.tsx`

| 功能 | 說明 |
|------|------|
| Cold-start 面板 | seed 輸入、觸發 job |
| 批次匯入 | 單次 `bulk-import` API |
| 同步 Topic Graph | `sync-topic-bridge` |
| 樹狀視圖 | `buildPyramidTree()`（後期改為**僅已核准**） |
| Exposure Map 修正 | 對齊 `keyword`、`keyword_level`、`status` |

**Helper**：`apps/web/lib/keyword-pyramid-form.ts`

### 4.2 SDK / Types

**路徑**：`packages/sdk/src/index.ts`、`packages/shared-types/src/index.ts`

新增方法：`coldStartResearch`、`bulkImportKeywordPyramid`、`syncPyramidTopicBridge`、`listProductScopes`

---

## 五、部署紀錄（Linode）

| 項目 | 值 |
|------|-----|
| 伺服器 | `root@172.233.67.244` |
| 目錄 | `/opt/exposureflow` |
| Compose | `infra/docker/docker-compose.prod.yml` |
| URL | https://app.kakusinn.com |

### 5.1 事故：Alembic revision 過長

- **現象**：revision `020_keyword_pyramid_enrichment_bridge`（35 字元）超過 DB `alembic_version.version_num` VARCHAR(32)
- **結果**：migration 更新 version 失敗 → **api/worker 不斷 Restarting**
- **修復**：revision 改為 **`020_keyword_pyramid_bridge`**，重新 build api/worker

### 5.2 Web 快取

- 首次 deploy 時 `pnpm build` 多步驟 **CACHED**，新 UI 未進 image
- **修復**：`docker compose build --no-cache web` 後 restart

### 5.3 驗證

- `alembic current` → `020_keyword_pyramid_bridge (head)`
- `/health` → `{"status":"ok","version":"0.1.0"}`
- ezfix 站點：sync bridge 產生 3 topic nodes；曝光地圖可篩選 cluster

---

## 六、顧問操作 UX 修正（2026-06-15 晚）

### 6.1 問題：「編輯」按了沒反應

- **原因**：編輯表單在頁面上方開啟，待審表格在下方，無捲動／無提示
- **修復**：
  - 表單固定於訊息列下方（頂部）
  - `scrollIntoView` + 綠框 + 提示「正在編輯 xxx」
  - 取消編輯時清除提示訊息

### 6.2 編輯／核准／排除／刪除 一併檢視

| 操作 | 行為 | 修正 |
|------|------|------|
| **編輯** | 開啟頂部表單，PATCH 節點 | 待審不可在表單改為 `in_scope`（須按核准） |
| **核准** | POST approve；設 `approved_at`；sync Topic Graph | 加入 confirm；`out_of_scope` 也可核准納入（後端） |
| **排除** | PATCH → `out_of_scope` | 加入 confirm |
| **刪除** | DELETE；子節點 parent 清空 | 維持 confirm |
| **恢復待審** | 排除區 PATCH → `needs_review` | 新增按鈕 |
| **核准納入** | 排除區直接 approve | 新增按鈕 |

**後端**：`approve_keyword_node` 將 `out_of_scope` 核准時一併改為 `in_scope`。

**前端**：`NodeTable` 依 `actionMode`（active / candidate / excluded）顯示不同按鈕組。

---

## 七、「正式納入」辨識改版（2026-06-15）

### 7.1 使用者困惑原因

1. 舊「金字塔結構」混合正式 + 待審，視覺相同  
2. 舊「正式關鍵字組」用 `business_fit_status === in_scope`，**不等於**顧問已核准  
3. 待審候選數量遠多於正式字，淹沒重點  

### 7.2 「正式納入」定義（UI 與 Onboarding 對齊）

**正式納入**（頁面綠色區）：

```
business_fit_status === 'in_scope'
AND approved_at IS NOT NULL
```

**Onboarding「建立 Keyword Pyramid」步驟**（更嚴）：

```
in_scope + approved_at + node_type ∈ { pillar, cluster, long_tail }
```

**不算正式納入**：

- `needs_review`（待審候選）
- `in_scope` 但無 `approved_at`（待按核准，橘色警示區）
- `out_of_scope` / `blocked`

### 7.3 UI 改版內容

| 元件 | 說明 |
|------|------|
| **本專案關鍵字一覽** | 四格統計：已正式納入／待按核准／待審候選／已排除 |
| **✅ 已正式納入的關鍵字** | 綠色區塊 + 表格 + **僅已核准**金字塔樹 |
| **⚠ 待按核准** | 橘色區（僅在有資料時顯示） |
| **納入狀態 badge** | 已正式納入／待按核准／待審候選／已排除／已封鎖 |
| **表格欄** | 「狀態」→「納入狀態」；「核准」→「核准時間」 |
| **+ 新增正式關鍵字** | 建立後**自動呼叫 approve**，直接進綠色區 |
| **Page 副標** | 明確指向綠色「已正式納入」區塊 |

**Helper 新增**（`keyword-pyramid-form.ts`）：

- `inclusionStatus()` / `inclusionStatusLabel()` / `inclusionStatusHint()`
- `isPendingApprovalNode()` / `isApprovedOfficialNode()`

### 7.4 ezfix 站點範例（部署驗收時）

| 分類 | 數量 | �例 |
|------|------|------|
| 已正式納入 | 3 | 台中紗窗維修、修理紗窗、換紗窗價格 |
| 待審候選 | 15 | 台中市修理、台中市換…（Intake 雜訊） |
| 待按核准 | 0 | — |
| 已排除 | 0 | — |

---

## 八、檔案清單（變更觸及）

### 後端

```
apps/api/alembic/versions/020_keyword_pyramid_enrichment_bridge.py
apps/api/exposureflow_api/strategy/keyword_enrichment.py
apps/api/exposureflow_api/strategy/keyword_research.py
apps/api/exposureflow_api/strategy/pyramid_topic_bridge.py
apps/api/exposureflow_api/strategy/keyword_extraction.py
apps/api/exposureflow_api/strategy/intake_impact.py
apps/api/exposureflow_api/strategy/service.py
apps/api/exposureflow_api/strategy/router.py
apps/api/exposureflow_api/strategy/schemas.py
apps/api/exposureflow_api/models/strategy.py
apps/api/exposureflow_api/jobs/handlers/cold_start_research.py
apps/api/exposureflow_api/exposure/service.py
apps/api/tests/test_keyword_enrichment.py
apps/api/tests/test_keyword_extraction.py
```

### 前端

```
apps/web/app/.../keyword-pyramid/page.tsx
apps/web/app/.../exposure-map/page.tsx
apps/web/lib/keyword-pyramid-form.ts
packages/sdk/src/index.ts
packages/shared-types/src/index.ts
```

### 文件

```
docs/product/keyword-capability-gap-plan.md   （KW-GAP 任務定義）
docs/product/keyword-pyramid-changelog-2026-06.md   （本文件）
```

---

## 九、顧問操作速查

```
草稿（Intake / Cold-start）
  → 編輯修正
  → 核准 ──→ 已正式納入（綠色區）──→ 同步 Topic Graph ──→ 曝光地圖

不需要的字
  → 排除（可恢復待審）或 刪除（永久）

直接新增策略字
  → 「+ 新增正式關鍵字」（自動核准）
  或
  → 「+ 新增待審候選」→ 編輯 → 核准
```

---

## 十、後續建議

| 項目 | 說明 |
|------|------|
| KW-021 | DataForSEO search volume / difficulty enrichment（參考值，非 Pyramid 必填） |
| ezfix 清理 | 批次排除／刪除 15 筆 Intake 雜訊候選 |
| Cold-start E2E | production 跑一輪 seed → 核准 → bridge 驗證 |
| phase-log | 可將本文件摘要併入 `phase-log.md` |

---

## 十一、修訂紀錄

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0 | 2026-06-15 | 初版：KW-GAP + 部署 + UX + 正式納入辨識 |
