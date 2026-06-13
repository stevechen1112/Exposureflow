# KPI Taxonomy

**文件編號**：EF-0001（附屬交付物）  
**狀態**：Phase 0 交付物  
**用途**：定義 ExposureFlow 各層級指標分類，確保所有模組 KPI 可回溯至北極星。

權威北極星定義見 `product-north-star-spec.md`。

---

## 1. 指標層級

```text
L1 北極星指標（Primary）
  └── 自然曝光資產成長

L2 版位與覆蓋指標（Core）
  ├── exposure growth
  ├── slot coverage
  ├── AI visibility
  └── topic coverage

L3 診斷指標（Diagnostic）
  └── CTR、點擊、停留、GA4 行為等

L4 營運指標（Operational）
  └── sync 健康、job 成功率、配額、帳務（不驅動內容優先級）
```

**規則**：L3、L4 不得作為 Opportunity 排序或 Dashboard 北極星；僅輔助解釋 L1/L2。

---

## 2. L1 — 北極星指標

| KPI ID | 名稱 | 定義 | 主要資料源 |
|--------|------|------|------------|
| NS-001 | Total Organic Impressions | 站點在搜尋結果中的總自然曝光數 | GSC、Bing WMT |
| NS-002 | Non-Brand Organic Impressions | 排除品牌詞後的自然曝光 | GSC query 篩選 |
| NS-003 | Topic Cluster Total Impressions | 單一主題集群下所有查詢曝光加總 | GSC + TopicCluster |
| NS-004 | Share of Visibility | 目標主題在 SERP + AI 回答中的可見度占比 | SERP + AI probe |

---

## 3. L2 — 核心維度 A：Exposure Growth（曝光成長）

| KPI ID | 名稱 | 定義 | 模組 |
|--------|------|------|------|
| EG-001 | Impressions MoM Delta | 月環比自然曝光變化 | Dashboard、Reporting |
| EG-002 | Query Coverage Count | 有曝光的獨立查詢數 | Exposure Intelligence |
| EG-003 | Page / Asset Coverage Count | 有曝光的曝光資產數 | ExposureAsset |
| EG-004 | Top 3 / Top 10 / Top 20 Query Count | 排名區間查詢覆蓋數 | GSC aggregation |
| EG-005 | New Indexed Strategic Asset Count | 新索引且具曝光的策略資產數 | Tech SEO + GSC |
| EG-006 | Exposure Delta per Action | 單一行動後的曝光增量 | ActionOutcome |

---

## 4. L2 — 核心維度 B：Slot Coverage（版位覆蓋）

| KPI ID | 名稱 | 定義 | 模組 |
|--------|------|------|------|
| SC-001 | SERP Slot Ownership Count | 我方佔有的版位數（依 slot type） | SERP Matrix |
| SC-002 | Featured Snippet Count | 取得精選摘要的關鍵字數 | SERP Matrix |
| SC-003 | PAA Presence Count | 出現在 PAA 的問題數 | SERP Matrix |
| SC-004 | Image / Video SERP Presence | 圖片／影片搜尋版位曝光 proxy | SERP + asset metadata |
| SC-005 | Slot Target Achieved Rate | `serp_slot_targets` 中 achieved 占比 | SERP Matrix |
| SC-006 | Single-Topic Multi-Slot Count | 單一主題同時可見版位數 | Topic + SERP 聯合 |

---

## 5. L2 — 核心維度 C：AI Visibility（AI 可見性）

| KPI ID | 名稱 | 定義 | 模組 |
|--------|------|------|------|
| AI-001 | AI Citation Count | 我方 URL 被 AI 回答引用次數 | AI Visibility |
| AI-002 | AI Brand Mention Count | 品牌名稱出現在 AI 回答的次數 | AI Visibility |
| AI-003 | AI Citation Rate per Prompt Set | 探測 prompt 集合中的引用率 | AIProbeSet |
| AI-004 | Competitor Citation Gap Count | 競品被引用但我方未引用的主題數 | AI + Competitors |
| AI-005 | Entity Consistency Score | 品牌實體跨來源一致性 | BrandEntity |
| AI-006 | AI Crawler Access Health | AI 搜尋爬蟲可存取性 | Tech SEO |

---

## 6. L2 — 核心維度 D：Topic Coverage（主題覆蓋）

| KPI ID | 名稱 | 定義 | 模組 |
|--------|------|------|------|
| TC-001 | Topic Cluster Coverage Score | 主題集群覆蓋率 | Topic Graph |
| TC-002 | Gap Node Count | 狀態為 gap 的 TopicNode 數 | Topic Graph |
| TC-003 | Cannibalized Node Count | 關鍵字蠶食節點數 | Cannibalization Detector |
| TC-004 | Stale Asset Count | 過時曝光資產數 | ExposureAsset + freshness |
| TC-005 | Internal Link Opportunity Count | 待執行的內鏈建議數 | Topic Graph |
| TC-006 | Pillar Coverage Completeness | 支柱頁與集群頁連結完整度 | Topic Graph |

---

## 7. L3 — 診斷指標（非北極星）

| KPI ID | 名稱 | 用途 | 限制 |
|--------|------|------|------|
| DG-001 | CTR | 診斷標題／SERP 擠壓 | 不得單獨否定高曝光資產 |
| DG-002 | Organic Clicks | 輔助判斷導流 | 非主排序因子 |
| DG-003 | Avg Position | 排名趨勢 | 搭配 impressions 解讀 |
| DG-004 | GA4 Engagement | 著陸頁行為 | 輔助，非主 KPI |
| DG-005 | Index Coverage % | 技術健康 | 支撐 EG-005 |

---

## 8. L4 — 營運指標（SaaS 營運，非內容北極星）

| KPI ID | 名稱 | 用途 |
|--------|------|------|
| OP-001 | GSC Sync Freshness | 資料是否及時 |
| OP-002 | Job Success Rate | 背景任務健康 |
| OP-003 | Provider Error Rate | 外部 API 穩定性 |
| OP-004 | Workspace Usage vs Quota | 配額管理 |
| OP-005 | MRR / Churn | 商業營運（Phase 11+） |

---

## 9. 模組 → KPI 映射（驗收矩陣）

| 模組 | exposure growth | slot coverage | AI visibility | topic coverage |
|------|:---:|:---:|:---:|:---:|
| Exposure Intelligence | ● | ○ | ○ | ○ |
| Topic Coverage Graph | ○ | ○ | ○ | ● |
| SERP Slot Matrix | ○ | ● | ○ | ○ |
| AI Visibility Monitor | ○ | ○ | ● | ○ |
| Brand / SERPO | ○ | ○ | ● | ○ |
| Opportunity Scorer | ● | ● | ● | ● |
| Decision Plane | ● | ● | ● | ● |
| Execution Plane | ● | ● | ● | ● |
| Measurement Dashboard | ● | ● | ● | ● |
| Reporting | ● | ● | ● | ● |
| Technical SEO | ● | ○ | ● | ○ |

圖例：● 直接貢獻；○ 間接或支撐。

**Phase 0 驗收**：上表所有核心模組至少覆蓋 L2 四維度之一，且 Dashboard 必須同時呈現四維度摘要。

---

## 10. Dashboard 北極星卡片（Phase 9 對照）

`GET /api/v1/exposure/dashboard` 回應欄位與 KPI 對照：

| API 欄位 | KPI ID |
|----------|--------|
| `total_impressions` | NS-001 |
| `impressions_delta_pct` | EG-001 |
| `query_coverage_count` | EG-002 |
| `indexed_asset_count` | EG-005 |
| `top_3_count` / `top_10_count` / `top_20_count` | EG-004 |
| `serp_slot_count` | SC-001 |
| `ai_citation_count` | AI-001 |
| `open_opportunity_count` | （營運，非北極星） |
| `critical_blocker_count` | OP-001 衍生 |

---

## 11. 明確排除的 KPI 用法

以下用法在 ExposureFlow 第一版中 **禁止**：

- 以 conversion rate 排序 Opportunity Queue
- 以每日發文數作為 Pipeline 成功指標
- 以單一 SEO Score 作為發布門檻
- 以 CTR 單獨觸發「內容失敗」標記而不診斷零點擊情境
- 以 leads 作為顧問月報主標題指標

---

## 12. 參考

- `product-north-star-spec.md`
- `organic-impressions-seo-plan.md` 第十一節（成效追蹤）
- `exposureflow-development-plan.md` 第七章 Measurement Plane、第十一章 Dashboard response
