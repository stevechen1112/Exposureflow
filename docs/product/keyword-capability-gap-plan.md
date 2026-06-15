# 關鍵字能力補強計畫（KW-GAP）

> 依據 `exposureflow-development-plan.md`、`organic-impressions-seo-plan.md` 與 ContentFlow 關鍵字模組對照分析制定。  
> 目標：讓 ExposureFlow 的 Keyword Pyramid 從「資料容器」升級為「顧問可制定、系統可研究、曝光可閉環」的策略工作台。

---

## 一、現況與目標

### 現況（2026-06 補強前）

| 能力 | 狀態 |
|------|------|
| Strategy Intake 版本化 + 核准 | ✅ |
| Keyword Pyramid CRUD（三區塊） | ✅ |
| Intake 規則式推演 + Constraint Rules | ✅（品質不足） |
| Cold-start research | ❌ Stub（僅 echo seed） |
| SERP / PAA / 相關搜尋研究 | ❌ 未接入 Pyramid |
| 搜尋量 / 難度 / 版位 enrichment | ❌ |
| Pyramid ↔ Topic Graph 橋接 | ❌ |
| 曝光機會 Business Fit Gate（OG-017） | ⚠️ 部分（rescore only） |
| 批次 / Excel 匯入 | ⚠️ 前端逐筆 POST |
| 樹狀金字塔 UI | ❌ |
| Exposure Map 欄位對應 | ❌ 錯位 |

### 目標

1. **顧問可制定**：樹狀結構、product scope、目標字標記、批次匯入。
2. **系統可研究**：Cold-start 接 Serper/SerpAPI，擴展 PAA / related searches，寫入 `evidence_json.enrichment`。
3. **推演可信任**：Intake 降噪，不再大量產生「台中市換」類機械組合。
4. **曝光可閉環**：核准節點連結 Topic Graph；GSC 機會生成前檢查 Business Fit；Exposure Map 顯示正確欄位。

---

## 二、任務清單（KW-001 ~ KW-018）

### Phase A — 資料模型與共用模組

| ID | 任務 | 產出 | 驗收 |
|----|------|------|------|
| KW-001 | Migration `020_keyword_pyramid_enrichment_bridge` | `topic_node_id`, `topic_cluster_id`, `keyword_level`, `funnel_stage`, `is_target` 欄位 | Alembic upgrade 成功 |
| KW-002 | `strategy/keyword_enrichment.py` | enrichment schema、`merge_enrichment()`、`targetable_slot_types()` | 單元測試 |
| KW-003 | `strategy/keyword_research.py` | SERP 擴展候選字、PAA/related 解析、`infer_keyword_level()` | 單元測試（mock SERP） |
| KW-004 | `strategy/pyramid_topic_bridge.py` | `link_pyramid_node_to_topic_graph()`, `sync_site_pyramid_links()` | 整合測試 |

### Phase B — 推演與 Cold-start

| ID | 任務 | 產出 | 驗收 |
|----|------|------|------|
| KW-005 | 重構 `keyword_extraction.py` | 停用 bare region；service 需完整片語；comparison/faq 推斷 | `test_keyword_extraction` 通過 |
| KW-006 | 重寫 `cold_start_research.py` | SERP fetch → 候選字 + enrichment → `needs_review` | Job 輸出 `keywords_created`, `serp_fetched` |
| KW-007 | Cold-start 請求擴充 | `max_expansions`, `include_paa`, `include_related` | API schema 更新 |

### Phase C — API 與 Business Fit

| ID | 任務 | 產出 | 驗收 |
|----|------|------|------|
| KW-008 | `POST /keyword-pyramid/bulk-import` | 交易式批次、dedupe、parent_keyword 解析 | 整合測試 |
| KW-009 | `POST /keyword-pyramid/sync-topic-bridge` | 手動觸發全站 pyramid→topic 同步 | API 測試 |
| KW-010 | 核准節點時自動 bridge | `approve_keyword_node` 呼叫 bridge | 核准後 FK 有值 |
| KW-011 | Intake apply 後自動 bridge | `apply_intake_impact` 結尾 sync | lifecycle 測試 |
| KW-012 | GSC 機會 OG-017 | `generate_opportunities_from_gsc` 檢查 fit，blocked 不建立 | 單元測試 |
| KW-013 | OG-016 冷啟動機會 | 已核准 pyramid 高優先節點 → `create_page` 候選 | serp/opportunity 測試 |

### Phase D — 前端工作台

| ID | 任務 | 產出 | 驗收 |
|----|------|------|------|
| KW-014 | Pyramid 樹狀視圖 | `buildPyramidTree()` + TreeSection UI | 瀏覽器可見層級 |
| KW-015 | Cold-start 面板 | seed 輸入 + 觸發 job + 狀態提示 | 顧問可操作 |
| KW-016 | 批次匯入改用 bulk API | CSV/文字 → 單次 POST | 減少 N 次請求 |
| KW-017 | 表單補齊 | product scope、funnel、is_target、enrichment 欄位顯示 | 表單完整 |
| KW-018 | 修正 Exposure Map | 對齊 `keyword`, `keyword_level`, `status` | 欄位正確顯示 |

### Phase E — SDK / Types / 文件

| ID | 任務 | 產出 |
|----|------|------|
| KW-019 | `shared-types` + SDK | `KeywordPyramidNode` 新欄位、`coldStartResearch`, `bulkImportKeywordPyramid`, `syncPyramidTopicBridge` |
| KW-020 | 更新 `phase-log.md` | 記錄 KW-GAP 完成項 |

---

## 三、資料契約

### `evidence_json.enrichment`

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

### `keyword_level` 對照

| Pyramid `node_type` | `keyword_level` |
|---------------------|-----------------|
| core | head |
| pillar | mid_tail |
| cluster, comparison, solution | mid_tail |
| long_tail, faq | long_tail |

### Business Fit Gate（OG-017）

- `business_fit_score = 0` 或 `blocked = true` → 不建立新 ExposureOpportunity
- 既有 open opportunity 在 Intake rescore 時更新分數（已存在）

---

## 四、實作順序

```text
KW-001 → KW-002/003/004 → KW-005/006 → KW-008~013 → KW-014~018 → KW-019 → 測試
```

---

## 五、不在本次範圍（後續）

- DataForSEO search volume / difficulty（需額外 API 合約）
- Excel `.xlsx` 二進位上傳（本次以 CSV/文字 bulk API 代替）
- 完整 Keyword × SERP Slot 矩陣獨立頁（已有 serp-matrix，本次在 pyramid 顯示 enrichment）
- LLM 批次標記意圖（維持規則 + 顧問手動）

---

## 六、完成定義（Definition of Done）

- [x] 所有 KW-001 ~ KW-019 程式碼落地
- [x] `apps/api/tests/test_keyword_*.py` 單元測試通過
- [x] Pyramid 頁可：樹狀檢視、cold-start、bulk import、顯示 SERP enrichment
- [x] 核准 pyramid 節點後觸發 `link_pyramid_node_to_topic_graph`
- [x] GSC 機會生成跳過 blocked 關鍵字（OG-001/004 + OG-016 pyramid）
- [x] Exposure Map 顯示正確 API 欄位

---

## 七、實作紀錄（2026-06-15）

> 完整更動紀錄（含部署事故、UX 修正、正式納入辨識改版）：[`keyword-pyramid-changelog-2026-06.md`](keyword-pyramid-changelog-2026-06.md)

| 模組 | 路徑 |
|------|------|
| 計畫文件 | `docs/product/keyword-capability-gap-plan.md` |
| Migration | `apps/api/alembic/versions/020_keyword_pyramid_enrichment_bridge.py`（revision: `020_keyword_pyramid_bridge`） |
| Enrichment | `apps/api/exposureflow_api/strategy/keyword_enrichment.py` |
| Research | `apps/api/exposureflow_api/strategy/keyword_research.py` |
| Bridge | `apps/api/exposureflow_api/strategy/pyramid_topic_bridge.py` |
| Cold-start | `apps/api/exposureflow_api/jobs/handlers/cold_start_research.py` |
| API | bulk-import / sync-topic-bridge / cold-start 擴充 |
| UI | keyword-pyramid 樹狀 + cold-start + exposure-map 修正 |
