# ExposureFlow 開發計畫：以自然曝光最大化為核心的新產品

## 一、最終判斷

在完全不考慮開發成本與開發時間的前提下，ExposureFlow 應採用以下路線：

**重寫新產品核心，選擇性移植 ContentFlow 的成熟底層能力。**

這不是在 ContentFlow 既有產品上小修小補，也不是把 ContentFlow 全部推倒不用。更精準的決策是：

```text
ExposureFlow = 新產品核心 + 新資料模型 + 新決策平面 + 新量測平面
             + 選擇性復用 ContentFlow 的 connector / publisher / safety / utility
```

原因是 ContentFlow 的北極星是「全自動 SEO 內容閉環」與「文章生產 pipeline」，而 ExposureFlow 的北極星應是「自然曝光資產最大化」。

兩者的底層心智不同：

| 系統 | 核心問題 | 核心物件 | 主要動作 |
|---|---|---|---|
| ContentFlow | 今天要寫什麼文章？ | Article、Keyword、PipelineRun、SEO Score | generate、refresh、publish |
| ExposureFlow | 哪些自然曝光資產與版位還沒被佔住？ | ExposureOpportunity、SERPSlot、AICitation、TopicCoverage、ExposureAsset | create、refresh、merge、redirect、cite、monitor、prioritize |

因此，ExposureFlow 不應以 `Article` 為第一級物件，而應以 `ExposureOpportunity` 與 `ExposureAsset` 為第一級物件。內容生產只是其中一種執行手段，不是產品核心。

---

## 二、產品定位

ExposureFlow 是一套為「自然曝光最大化」而設計的作業系統。

它不是單純 SEO 工具、文章產生器或內容日曆，而是協助企業與行銷顧問管理以下問題：

- 哪些搜尋情境還沒有被品牌覆蓋？
- 哪些關鍵字具備可取得曝光機會？
- 哪些 SERP 版位可以搶，例如 Featured Snippet、PAA、圖片、影片、Product、FAQ、Breadcrumb？
- 哪些主題應新增頁面，哪些應更新、合併、轉址或不動作？
- 哪些內容具備 AI 搜尋引用機會？
- 品牌是否在 ChatGPT Search、Perplexity、Bing Copilot、Google AI Overviews 中被提及或引用？
- 哪些第三方內容能幫品牌取得自然曝光？
- 哪些技術問題阻礙索引、爬取、AI crawler 存取或 rich result？
- 如何用曝光增量，而不是發文量，管理 SEO 工作？

ExposureFlow 的一句話定位：

**一套把 SEO、SERP、AI 搜尋與第三方引用整合成自然曝光資產管理的系統。**

---

## 三、產品原則

### 1. 曝光資產優先，不是文章優先

系統不應預設每個機會都要寫新文章。每個機會都應先判斷：

- create：新增頁面
- refresh：更新既有頁面
- merge：合併重疊頁面
- redirect：重定向弱頁或重複頁
- enrich：補 FAQ、表格、schema、圖片、影片、資料來源
- outreach：爭取第三方引用或品牌提及
- technical_fix：修復技術阻礙
- no-op：不做任何事

### 2. 曝光版位優先，不只是排名

每個主題都應建立「曝光版位矩陣」，包含：

- Traditional organic result
- Featured Snippet
- People Also Ask
- Images
- Videos
- Product / Shopping organic elements
- Local / Map pack（若適用）
- FAQ / HowTo / Review rich results（若適用）
- Google AI Overviews / AI Mode
- Bing Copilot grounding citations
- ChatGPT Search source link
- Perplexity citation
- Third-party article mention
- Forum / community / review page mention

### 3. 主題總曝光優先，不是單頁 KPI

系統的主分析單位應是 `TopicCluster` 與 `ExposureTheme`，不是單一文章。

例如「運動鞋」主題應看：

- 支柱頁曝光
- 集群頁曝光
- 所有查詢總曝光
- 所有 SERP 版位覆蓋
- AI 引用次數
- 第三方提及
- 品牌搜尋變化

### 4. 零點擊曝光納入價值

若品牌、資料、頁面或第三方引用出現在 SERP 或 AI 回答中，即使沒有點擊，也應記錄為曝光資產。

因此，ExposureFlow 不應把低 CTR 一律視為問題。低 CTR 可能代表：

- 標題描述不吸引人
- SERP 被廣告或 AI Overview 擠壓
- 使用者已在零點擊版位取得答案
- 內容成為品牌曝光而非導流入口

系統需先診斷原因，再決定是否優化 CTR。

### 5. AI 搜尋是核心，不是附加功能

ContentFlow 目前缺少 AI 搜尋曝光管理。ExposureFlow 應從第一版資料模型就納入：

- AI citation
- AI source link
- Brand mention
- AI answer sentiment
- Entity consistency
- AI crawler access
- SERPO
- Prompt set monitoring

---

## 四、是否復用 ContentFlow 的判斷

### 結論

應復用 ContentFlow 的「成熟底層能力」，但不應復用它的「產品核心架構」。

### 應復用或參考的 ContentFlow 檔案

| ContentFlow 檔案 | ExposureFlow 用法 | 判斷 |
|---|---|---|
| `src/contentflow/tools/gsc.py` | 改造成 `connectors/google_search_console.py`，讀取 query/page/country/device/date impressions、clicks、ctr、position | 高度復用 |
| `src/contentflow/tools/ga4.py` | 改造成 `connectors/google_analytics.py`，作為輔助診斷，不作為主 KPI | 選擇性復用 |
| `src/contentflow/tools/serp.py` | 改造成 `connectors/serp_provider.py`，保留 Serper / SerpAPI fallback，但擴充 SERP slot extraction | 高度復用但需重寫資料結構 |
| `src/contentflow/tools/brand_mentions.py` | 作為 brand mention / outreach seed，重寫成 `connectors/brand_web_presence.py` | 概念復用 |
| `src/contentflow/tools/tech_seo.py` | 拆成 CWV、crawlability、indexability、schema validation、AI crawler access checks | 高度復用 |
| `src/contentflow/publishers/wordpress.py` | 改造成 `execution_adapters/wordpress.py`，用於發布、更新與 refresh 執行 | 高度復用 |
| `src/contentflow/publishers/forgebase.py` | 改造成 `execution_adapters/forgebase.py`，若未來與 ForgeBase Lead Engine 串接可用 | 高度復用 |
| `src/contentflow/utils/publish_safety.py` | 改造成 `safety/publish_gate.py`，保留「安全閘」概念 | 高度復用 |
| `src/contentflow/utils/article_schema.py` | 改造成 `schema/article_schema.py`，保留 JSON-LD headline / description 對齊 | 高度復用 |
| `src/contentflow/utils/slug_governance.py` | 改造成 `utils/slug_policy.py` | 復用 |
| `src/contentflow/agents/site_intelligence.py` | 改造成 `services/site_inventory.py` 與 `services/content_overlap.py`，保留 inventory / overlap / freshness / link opportunity 概念 | 邏輯復用，架構重寫 |
| `src/contentflow/agents/analytics_agent.py` | 參考 refresh、cannibalization、performance grading，但改為 exposure-first diagnostics | 邏輯復用 |
| `src/contentflow/agents/cluster_agent.py` | 不直接復用 LLM 分群核心，改用 embeddings + SERP + GSC 共現建立 topic graph | 概念復用 |
| `src/contentflow/agents/refresh_agent.py` | 參考 section-aware refresh、Featured Snippet detector | 部分復用 |
| `src/contentflow/agents/content_compiler/` | 可作為內容執行引擎候選，但 ExposureFlow 不以內容生成為核心 | 降級為 adapter |
| `src/contentflow/scheduler_job_registry.py` | 參考排程任務治理與 job registry 設計 | 概念復用 |
| `src/contentflow/scheduler.py` | 不直接復用，避免帶入 27 jobs 與文章 pipeline 耦合 | 不直接復用 |
| `src/contentflow/models/database.py` | 不直接復用資料模型，因其以 Article / Keyword / PipelineRun 為中心 | 不復用核心 schema |
| `src/contentflow/admin/app.py` | 不直接復用，因其 UI 與路由高度綁文章管理、agent 執行中心 | 不復用 |
| `src/contentflow/agents/strategic_agent.py` | 不直接復用，因其高耦合且以 generate / refresh 文章為中心 | 僅參考已踩過的決策問題 |
| `src/contentflow/agents/orchestrator.py` | 不直接復用為核心，只可作為 ContentExecution adapter 的歷史參考 | 不作核心 |

### 不應復用的核心設計

以下設計若沿用，會讓 ExposureFlow 被 ContentFlow 的文章工廠心智綁住：

- 以 `Article` 作為第一級產品物件
- 以 `ContentCalendar` 作為主工作流
- 以每日自動產文數量作為 pipeline 觸發核心
- 以 `SEO Score` 作為主要品質門檻
- 以低 CTR 自動判定為 meta 問題
- 以 16 agents 作為產品語言
- 以 Admin 文章管理後台作為主介面
- 以 auto publish 作為核心價值

---

## 五、ExposureFlow 目標架構

### 1. 高階架構

```text
ExposureFlow
├── Exposure Plane
│   ├── Exposure Opportunity Engine
│   ├── SERP Slot Matrix
│   ├── AI Visibility Monitor
│   ├── Topic Coverage Graph
│   └── Exposure Prioritization Engine
│
├── Intelligence Connectors
│   ├── Google Search Console
│   ├── Bing Webmaster Tools
│   ├── Google Analytics 4
│   ├── SERP Providers
│   ├── AI Search Probe Providers
│   ├── Brand Mention Providers
│   └── Technical SEO Crawlers
│
├── Decision Plane
│   ├── Action Candidate Generator
│   ├── Exposure Opportunity Scorer
│   ├── Action Selector
│   ├── Policy Gate
│   └── Roadmap Builder
│
├── Execution Plane
│   ├── Content Brief Builder
│   ├── Content Production Adapter
│   ├── Refresh Adapter
│   ├── Schema / SERP Enhancement Adapter
│   ├── Technical Fix Adapter
│   ├── Outreach Task Adapter
│   └── Publisher Adapters
│
├── Measurement Plane
│   ├── Exposure KPI Dashboard
│   ├── Topic Cluster Performance
│   ├── SERP Slot Tracking
│   ├── AI Citation Tracking
│   ├── Brand Entity Tracking
│   └── Action Outcome Evaluation
│
└── Operating Layer
    ├── Workspaces / Tenants
    ├── Users / Roles
    ├── Job Scheduler
    ├── Audit Logs
    ├── Integrations
    └── Reports
```

### 2. 技術建議

若從長期產品角度設計，不必受 ContentFlow 技術棧限制。建議：

- Backend：Python FastAPI 或 TypeScript NestJS。若要復用 ContentFlow connector，優先 Python FastAPI。
- Frontend：Next.js + React。
- Database：PostgreSQL。
- Search / semantic layer：pgvector 或 dedicated vector DB。
- Queue：Redis Queue / Celery / Temporal / BullMQ。若要長期可靠，建議 Temporal。
- Scheduler：Temporal schedules 或 APScheduler-like job registry，但不要沿用 ContentFlow 的大單檔 scheduler。
- Object storage：Cloudflare R2 / S3。
- Auth：Clerk / Auth.js / 自建 RBAC。
- Observability：OpenTelemetry + structured logs + job run table。

---

## 六、核心資料模型

ExposureFlow 的資料模型應從「曝光」出發。

### 1. Workspace / Site

```text
Workspace
- id
- name
- owner_id
- plan
- created_at

Site
- id
- workspace_id
- domain
- site_name
- locale
- target_markets
- industry
- business_model
- exposure_goal_profile
- created_at
```

### 2. Search Surface

```text
SearchSurface
- id
- name
- type: google | bing | chatgpt_search | perplexity | copilot | ai_overview | image | video
- country
- language
- device
- enabled
```

### 3. Exposure Theme / Topic Cluster

```text
ExposureTheme
- id
- site_id
- name
- description
- parent_theme_id
- business_priority
- target_audience
- created_at

TopicCluster
- id
- site_id
- exposure_theme_id
- pillar_keyword
- pillar_url
- cluster_status
- coverage_score
- authority_score
- total_impressions
- ai_visibility_score
- last_analyzed_at

TopicNode
- id
- cluster_id
- keyword
- intent
- keyword_level: head | mid_tail | long_tail
- search_context
- current_best_url
- status: covered | gap | cannibalized | stale | blocked
```

### 4. Exposure Opportunity

```text
ExposureOpportunity
- id
- site_id
- cluster_id
- opportunity_type:
  create_page | refresh_page | merge_pages | redirect_page |
  optimize_snippet | add_schema | add_image_asset | add_video_asset |
  ai_citation_ready | third_party_citation | technical_fix | no_op
- keyword
- search_context
- target_url
- current_url
- estimated_search_volume
- current_impressions
- current_position
- ranking_feasibility_score
- serp_slot_score
- ai_citation_score
- topic_contribution_score
- zero_click_value_score
- total_opportunity_score
- priority
- status: open | planned | executing | completed | rejected | monitoring
- reason
- evidence_json
- created_at
- updated_at
```

### 5. SERP Slot Matrix

```text
SERPQuerySnapshot
- id
- site_id
- keyword
- surface_id
- country
- language
- device
- captured_at
- raw_provider
- raw_json

SERPSlot
- id
- snapshot_id
- slot_type:
  organic | featured_snippet | paa | image | video | product |
  local_pack | knowledge_panel | forum | ai_overview | shopping | faq_rich
- position
- owner_domain
- owner_brand
- url
- title
- snippet
- is_own_site
- is_competitor
- is_third_party

SERPSlotTarget
- id
- opportunity_id
- slot_type
- target_status: target | achieved | blocked | not_applicable
- current_owner
- recommended_action
```

### 6. AI Visibility

```text
AIProbeSet
- id
- site_id
- name
- topic_cluster_id
- prompts_json
- surfaces_json
- schedule
- active

AIProbeRun
- id
- probe_set_id
- surface: chatgpt_search | perplexity | bing_copilot | google_ai_overview
- prompt
- answer_text
- cited_urls_json
- mentioned_brands_json
- sentiment
- our_brand_mentioned
- our_url_cited
- competitor_mentions_json
- run_at

AICitation
- id
- site_id
- surface
- prompt
- cited_url
- cited_domain
- cited_title
- citation_context
- is_own_site
- is_third_party_about_brand
- is_competitor
- captured_at
```

### 7. Brand Entity / SERPO

```text
BrandEntity
- id
- site_id
- canonical_name
- aliases_json
- description
- official_profiles_json
- entity_consistency_score

BrandMention
- id
- site_id
- source_url
- source_domain
- source_type: media | forum | social | directory | review | partner | ai_answer
- mention_text
- linked
- sentiment
- authority_score
- relevance_score
- captured_at

SERPORecord
- id
- site_id
- brand_query
- keyword
- first_page_positive_count
- first_page_neutral_count
- first_page_negative_count
- first_page_wrong_info_count
- recommended_actions_json
- captured_at
```

### 8. Exposure Asset

```text
ExposureAsset
- id
- site_id
- asset_type:
  pillar_page | cluster_page | product_page | comparison_page |
  guide | faq | tool | whitepaper | video | image | third_party_article
- url
- title
- primary_theme_id
- primary_keyword
- exposure_task_json
- current_status
- published_at
- last_refreshed_at
- total_impressions
- total_clicks
- ai_citation_count
- serp_slot_count
- brand_mention_count
```

### 9. Action Candidate / Decision

```text
ActionCandidate
- id
- opportunity_id
- site_id
- action_type
- target_asset_id
- action_payload_json
- expected_exposure_impact
- risk_level
- required_inputs_json
- evidence_json
- created_by: rule | llm | human

ActionDecision
- id
- candidate_id
- decision: approve | reject | defer | needs_review
- selected_by
- rationale
- confidence
- scheduled_for
- created_at
```

### 10. Execution Job / Outcome

```text
ExecutionJob
- id
- decision_id
- job_type
- status
- executor_type: human | content_engine | wordpress | technical_adapter | outreach
- input_json
- output_json
- error
- started_at
- completed_at

ActionOutcome
- id
- execution_job_id
- baseline_snapshot_json
- followup_7d_json
- followup_28d_json
- followup_90d_json
- outcome_status: improved | neutral | declined | insufficient_data
- exposure_delta
- serp_slot_delta
- ai_citation_delta
- notes
```

---

## 七、核心模組設計

### 1. Exposure Intelligence

目標：建立網站目前自然曝光基準與機會池。

功能：

- 匯入 GSC query/page/country/device/date 資料
- 匯入 Bing Webmaster Tools 資料
- 匯入 GA4 作為輔助診斷
- 建立頁面與查詢的曝光基準
- 辨識高曝光低排名、排名 11-30、曝光下滑、無曝光頁面
- 區分 CTR 問題與零點擊曝光
- 建立 ExposureOpportunity 初始清單

可參考 ContentFlow：

- `src/contentflow/tools/gsc.py`
- `src/contentflow/tools/ga4.py`
- `src/contentflow/agents/analytics_agent.py`

不可直接沿用：

- `AnalyticsAgent._compute_action()` 中把 P11-P20 一律導向 refresh 的單一思路。ExposureFlow 應先判斷 SERP slot、AI Overview、零點擊價值與主題貢獻。

### 2. Topic Coverage Graph

目標：將關鍵字、頁面、主題、內鏈、曝光資料整合成主題版圖。

功能：

- 建立 topic cluster graph
- 辨識 pillar / cluster / orphan / duplicate / stale page
- 計算主題覆蓋率
- 計算主題總曝光
- 偵測 cannibalization
- 建議 merge / redirect / differentiate
- 建議內部連結

可參考 ContentFlow：

- `src/contentflow/agents/site_intelligence.py`
- `src/contentflow/agents/cluster_agent.py`
- `src/contentflow/agents/analytics_agent.py`

重寫重點：

- 不使用單次 LLM 分群作為主分群方式。
- 應採用 embeddings + GSC query co-occurrence + SERP similarity + URL hierarchy。
- LLM 只負責命名 cluster 與解釋，而非唯一分群依據。

### 3. SERP Slot Matrix

目標：把 SERP 從「排名」升級成「版位資產」。

功能：

- 針對目標 keyword 抓 SERP snapshot
- 抽取 organic、featured snippet、PAA、image、video、product、forum、AI overview 等 slot
- 判斷我方、競品、第三方、平台占位
- 為每個 keyword 建立 slot availability
- 判斷每個 slot 的可爭取性
- 建議內容格式與技術標記

可參考 ContentFlow：

- `src/contentflow/tools/serp.py`
- `src/contentflow/agents/research_agent.py`
- `src/contentflow/agents/refresh_agent.py` 中 Featured Snippet detector 思路

需新增：

- slot extraction schema
- SERP visual density score
- forum / marketplace / media / ecommerce platform classifier
- AI Overview presence detection

### 4. AI Visibility Monitor

目標：管理 AI 搜尋曝光、引用與品牌提及。

功能：

- 建立 prompt set
- 定期查詢 ChatGPT Search、Perplexity、Bing Copilot、Google AI Overviews
- 記錄品牌是否被提及
- 記錄 URL 是否被引用
- 記錄第三方來源是否提及品牌
- 記錄競品提及
- 記錄回答情緒傾向
- 對錯誤或過時品牌描述產生修正任務
- 檢查 AI crawler access

ContentFlow 可參考：

- `src/contentflow/tools/brand_mentions.py` 僅可作為一般品牌提及 seed
- `src/contentflow/tools/tech_seo.py` 可擴充 AI crawler access

需全新開發：

- AIProbeSet
- AIProbeRun
- AICitation
- prompt management
- citation extraction
- answer sentiment
- entity consistency

### 5. Exposure Opportunity Scorer

目標：將候選機會轉成可排序的自然曝光機會。

核心公式：

```text
ExposureOpportunityScore
= search_volume_potential
× ranking_feasibility
× serp_slot_opportunity
× ai_citation_opportunity
× topic_cluster_contribution
× zero_click_value
× execution_confidence
```

評估維度：

- 搜尋量潛力
- 目前排名與進榜可行性
- SERP 是否有可爭取版位
- AI 是否容易引用該類內容
- 是否補齊主題集群缺口
- 是否有零點擊曝光價值
- 是否需要新內容或只需更新
- 是否有技術阻礙
- 是否需要外部引用

不可沿用 ContentFlow：

- `strategic_controls.py` 中 `awareness / conversion / lead_capture / authority` 的簡化 business goal weighting 可作參考，但不足以作為 ExposureFlow 核心 scorer。

### 6. Decision Plane

目標：把機會轉成可執行任務。

流程：

```text
Observation
→ Opportunity
→ Candidate
→ Decision
→ Execution Job
→ Outcome
```

決策輸出：

- create_page
- refresh_page
- merge_pages
- redirect_page
- optimize_snippet
- add_faq
- add_schema
- add_image_asset
- add_video_asset
- create_linkable_asset
- outreach_to_third_party
- fix_indexability
- fix_ai_crawler_access
- no_op

可參考 ContentFlow：

- `SEO_16_AGENT_REFACTOR_PLAN_2026-05-28.md` 中 W1 決策平面整併思路
- `src/contentflow/agents/strategic_controls.py` 中 candidate / decision trace 思路

不建議復用：

- `src/contentflow/agents/strategic_agent.py` 本體，因為太大且與文章 pipeline 耦合。

### 7. Execution Plane

目標：把 approved decision 交給正確執行器。

執行器類型：

- Content Execution Adapter
- Refresh Adapter
- Schema Adapter
- Publisher Adapter
- Technical Fix Adapter
- Outreach Adapter
- Manual Task Adapter

可復用 ContentFlow：

- `src/contentflow/publishers/wordpress.py`
- `src/contentflow/publishers/forgebase.py`
- `src/contentflow/utils/publish_safety.py`
- `src/contentflow/utils/article_schema.py`
- `src/contentflow/agents/content_compiler/` 作為可選 content engine

重點：

ContentFlow 的內容產製能力應被放在 Execution Plane 中，而不是 ExposureFlow 的中心。

### 8. Measurement Plane

目標：用曝光結果評估 action outcome。

KPI：

- Total organic impressions
- Query coverage count
- Page with impressions count
- Top 3 / Top 10 / Top 20 query count
- Topic total impressions
- SERP slot ownership count
- Featured Snippet count
- PAA presence count
- Image / video exposure proxy
- AI citation count
- AI brand mention count
- Third-party brand mention count
- Indexed strategic asset count
- Technical blocker count

Outcome 評估：

- 7 日：是否已索引 / 是否 SERP snapshot 有變化
- 28 日：GSC 曝光與排名變化
- 90 日：主題總曝光、AI citation、第三方引用變化

---

## 八、產品介面設計

### 1. Dashboard

主頁不應顯示「今天寫了幾篇文章」，而應顯示：

- 本月自然曝光增量
- 有曝光查詢數
- 有曝光頁面數
- Top 10 / Top 20 查詢數
- SERP slot achieved
- AI citations / brand mentions
- Open exposure opportunities
- High-priority blockers
- Topic clusters by exposure growth

### 2. Exposure Map

功能：

- 以主題 cluster 顯示曝光版圖
- 顯示每個主題的 pillar、cluster pages、gaps、cannibalization、stale pages
- 顯示總曝光、query count、SERP slots、AI visibility

### 3. Opportunity Queue

功能：

- 列出所有 open opportunities
- 依 exposure opportunity score 排序
- 顯示 action type、reason、evidence、expected impact
- 允許 approve / reject / defer

### 4. SERP Matrix

功能：

- 以 keyword 為列、slot type 為欄
- 顯示 own / competitor / third-party / platform
- 顯示 target status
- 可進入 snapshot detail

### 5. AI Visibility

功能：

- 管理 prompt sets
- 顯示各 AI 平台品牌提及率
- 顯示 citation URL
- 顯示競品出現率
- 顯示 sentiment
- 顯示錯誤品牌描述與修正任務

### 6. Action Outcomes

功能：

- 每個 action 的 baseline、7d、28d、90d 結果
- 曝光增量
- SERP slot 變化
- AI citation 變化
- action 是否值得複製

---

## 九、開發 Task Plan

以下以任務依賴與產品模組拆解，而不是以時間估算呈現。

### Phase 0：產品核心定義

#### EF-0001 定義產品北極星

任務：

- 明確定義 ExposureFlow 的唯一主目標：自然曝光最大化。
- 明確排除 leads、成交、conversion 作為第一版核心 KPI。
- 定義零點擊曝光的價值。

產出物：

- Product North Star Spec
- KPI Taxonomy

驗收：

- 所有模組的 KPI 都能回到 exposure growth、slot coverage、AI visibility、topic coverage。

#### EF-0002 定義 ContentFlow 復用邊界

任務：

- 將 ContentFlow 可復用檔案分類成 connector、publisher、safety、utility、reference only。
- 禁止直接以 ContentFlow `Article` / `ContentCalendar` / `PipelineRun` 作為 ExposureFlow 核心 schema。

產出物：

- Reuse Boundary Document
- Migration / Porting Map

驗收：

- 新 repo 中不得直接複製 ContentFlow 的 `models/database.py` 作為主資料模型。
- `strategic_agent.py` 不作為 ExposureFlow 決策核心。

---

### Phase 1：新產品基礎架構

#### EF-0101 建立新 repo 與專案骨架

建議 repo：

```text
ExposureFlow/
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   ├── connectors/
│   ├── exposure-core/
│   ├── execution-adapters/
│   └── shared/
├── docs/
├── migrations/
└── tests/
```

任務：

- 建立 backend API
- 建立 frontend app
- 建立 shared schemas
- 建立 migrations
- 建立 lint / test / CI

驗收：

- 可啟動 API 與 Web。
- 可連接 PostgreSQL。
- CI 可執行測試。

#### EF-0102 建立租戶與站點模型

任務：

- 建立 Account、Workspace、Organization、User、Role、Site、IntegrationCredential。
- 支援 agency / consultant / enterprise client 三種組織型態。
- 支援一個顧問帳號管理多個客戶 workspace。
- 支援一個 workspace 管理多個 site、market、language、device。
- 所有核心資料表必須包含 `workspace_id` 或可回溯的 tenant boundary。
- IntegrationCredential 必須以 workspace / site scope 管理，不可全域共用。
- 建立 tenant-aware query policy，避免跨租戶資料外洩。
- 建立 workspace-level feature flags、plan limits、usage limits。

驗收：

- 可建立 workspace。
- 可新增 site。
- 可設定 target market。
- 同一使用者可屬於多個 workspace，且角色不同。
- 顧問可切換客戶 workspace，但客戶不可看到其他客戶資料。
- API 層與資料層皆有 tenant isolation 測試。

#### EF-0103 建立 Job 與 Audit 基礎

任務：

- 建立 JobRun、JobDefinition、AuditLog。
- 建立 background job executor。
- 建立 job retry、status、error logging。
- Job 必須支援 workspace-level queue isolation。
- Job 必須記錄 quota consumption、external API cost、provider response。
- AuditLog 必須記錄登入、整合授權、資料匯出、任務核准、發布、刪除與權限變更。

可參考：

- `src/contentflow/scheduler_job_registry.py`
- `src/contentflow/scheduler.py` 的 job registry 概念

不直接沿用：

- ContentFlow 單一大型 scheduler 實作。

#### EF-0104 建立多租戶權限與安全基礎

任務：

- 建立 RBAC：Owner、Admin、Strategist、Editor、Analyst、Client Viewer、Billing Admin、Support Admin。
- 建立 workspace invitation、email verification、2FA、session management。
- 建立 API key / service token scoped permissions。
- 建立 client portal 權限，讓客戶只能看報表、roadmap、核准事項，不可碰全域設定。
- 建立 impersonation 機制，但僅限 internal support 且必須完整稽核。

驗收：

- 每個 API endpoint 都有 workspace scope 與 role check。
- 客戶 viewer 無法讀取其他 workspace 或修改 opportunity。
- Support impersonation 必須留下 audit trail。

---

### Phase 2：資料接入層

#### EF-0201 移植 Google Search Console Connector

參考：

- `src/contentflow/tools/gsc.py`

任務：

- 實作 GSC OAuth / service account 支援。
- 匯入 query/page/date/country/device。
- 寫入 `gsc_performance_rows`。
- 建立 incremental sync。
- 處理 GSC 延遲資料。

驗收：

- 可同步最近 16 個月資料。
- 可依 site/query/page/date 查詢 impressions、clicks、ctr、position。

#### EF-0202 移植 GA4 Connector

參考：

- `src/contentflow/tools/ga4.py`

任務：

- 匯入 page path、sessions、engagement、conversions。
- 標記為輔助資料，不作為 ExposureFlow 主 KPI。

驗收：

- 可將 GA4 page metrics 對應到 ExposureAsset。

#### EF-0203 重建 SERP Provider Connector

參考：

- `src/contentflow/tools/serp.py`

任務：

- 保留 Serper / SerpAPI fallback。
- 新增 slot extraction。
- 新增 snapshot persistence。
- 支援 country、language、device。

驗收：

- 每個 keyword 生成 SERPQuerySnapshot。
- 可抽取 organic、PAA、related searches。
- 可擴充 featured snippet、image、video、product、forum、AI overview presence。

#### EF-0204 建立 Technical SEO Connector

參考：

- `src/contentflow/tools/tech_seo.py`

任務：

- CWV
- sitemap
- robots.txt
- noindex
- canonical
- redirect chain
- 404
- schema validation
- AI crawler access

驗收：

- 每個 Site 產生 TechnicalIssue。
- AI crawler access 可檢查 Googlebot、Bingbot、OAI-SearchBot、PerplexityBot、GPTBot。

---

### Phase 3：Exposure Core

#### EF-0301 建立 ExposureAsset 模型

任務：

- 將 sitemap / GSC page / CMS page 統一為 ExposureAsset。
- 標記 asset_type、topic、primary keyword、status。

驗收：

- 可從 GSC page 自動建立 asset candidate。
- 可手動合併 duplicate assets。

#### EF-0302 建立 ExposureOpportunity 模型

任務：

- 建立 opportunity types。
- 建立 opportunity lifecycle。
- 建立 evidence_json。

驗收：

- 可從 GSC 規則產生第一批 opportunity。

#### EF-0303 建立 Exposure Opportunity Scorer

任務：

- 實作自然曝光機會分數。
- 分數包含 search volume、ranking feasibility、SERP slots、AI citation、topic contribution、zero-click value。

驗收：

- 同一批 keyword 可得到穩定排序。
- 每個分數可回溯 evidence。

---

### Phase 4：Topic Coverage Graph

#### EF-0401 建立 Topic Graph

任務：

- 使用 GSC query co-occurrence。
- 使用 SERP similarity。
- 使用 embeddings。
- 使用 URL hierarchy。
- 建立 ExposureTheme、TopicCluster、TopicNode。

參考：

- `src/contentflow/agents/cluster_agent.py`
- `src/contentflow/agents/site_intelligence.py`

驗收：

- 每個 cluster 有 pillar candidate。
- 每個 cluster 有 coverage score。
- 每個 node 有 covered/gap/stale/cannibalized 狀態。

#### EF-0402 建立 Cannibalization Detector

參考：

- `src/contentflow/agents/analytics_agent.py`
- `src/contentflow/agents/site_intelligence.py`

任務：

- 以 GSC query overlap、SERP URL overlap、semantic similarity 偵測 cannibalization。
- 產生 merge / differentiate / redirect recommendations。

驗收：

- 可列出 query 被多頁競逐的情況。
- 每個建議有 evidence。

#### EF-0403 建立 Internal Link Opportunity

任務：

- 以 topic graph 建議內鏈。
- 以 anchor relevance score 排序。
- 支援 manual approval。

驗收：

- 每個 cluster 可輸出內鏈建議。

---

### Phase 5：SERP Slot Matrix

#### EF-0501 建立 SERP Slot Schema

任務：

- 定義 slot types。
- 定義 owner classification。
- 定義 target status。

驗收：

- SERP snapshot 可被轉換為 slot matrix。

#### EF-0502 建立 Featured Snippet / PAA Opportunity

參考：

- `src/contentflow/agents/refresh_agent.py`
- `src/contentflow/tools/serp.py`

任務：

- 偵測可搶 Featured Snippet 的 keyword。
- 偵測 PAA 問題缺口。
- 產生 add_answer_block / add_faq / refresh_section opportunity。

驗收：

- 每個 PAA question 可連到建議頁面或 gap。

#### EF-0503 建立 Image / Video / Product Slot Opportunity

任務：

- 偵測 SERP 是否有 image/video/product slot。
- 檢查我方是否有對應 asset。
- 產生 add_image_asset / add_video_asset / add_product_schema opportunity。

驗收：

- 每個 keyword 可顯示圖像與影片版位機會。

---

### Phase 6：AI Visibility Monitor

#### EF-0601 建立 AI Probe Framework

任務：

- 定義 AIProbeSet。
- 支援 prompt list。
- 支援 surface list。
- 支援人工執行與定期執行。

驗收：

- 可建立「扁平足慢跑鞋推薦」一組 prompts。
- 可儲存每次回答。

#### EF-0602 建立 AI Citation Extractor

任務：

- 從 AI answer 中抽取 cited URLs。
- 判斷 own site / third party / competitor。
- 記錄 citation context。

驗收：

- Perplexity 或 ChatGPT Search 回答可儲存 citations。

#### EF-0603 建立 Brand Mention / Sentiment Monitor

任務：

- 抽取 mentioned brands。
- 判斷我方與競品是否出現。
- 記錄 sentiment。
- 偵測錯誤或過時描述。

驗收：

- 可輸出品牌 AI visibility score。

#### EF-0604 建立 Entity Consistency Checker

任務：

- 檢查品牌名稱、別名、公司資料、社群、第三方描述一致性。
- 產生 entity_fix opportunity。

驗收：

- 可列出品牌資訊不一致來源。

---

### Phase 7：Decision Plane

#### EF-0701 建立 Candidate Generator

任務：

- 從 GSC、SERP、AI、Topic Graph、Tech SEO 產生 ActionCandidate。
- 每個 candidate 需有 evidence。

可參考：

- `SEO_16_AGENT_REFACTOR_PLAN_2026-05-28.md` 的 W1 candidate / decision 思路
- `src/contentflow/agents/strategic_controls.py`

驗收：

- 同一批資料可產出 deterministic candidates。

#### EF-0702 建立 Action Selector

任務：

- 將 candidates 排序。
- 可使用 LLM 生成 rationale，但不得讓 LLM 憑空產生 action。
- 支援 human approval。

驗收：

- Decision 可回溯 candidate id、evidence、score。

#### EF-0703 建立 Roadmap Builder

任務：

- 將 approved decisions 排成 4、8、16 週 roadmap。
- 支援依人力、風險、依賴關係排序。

驗收：

- 可輸出自然曝光最大化執行路線圖。

---

### Phase 8：Execution Plane

#### EF-0801 建立 Content Brief Builder

任務：

- 將 opportunity 轉成內容 brief。
- brief 必須包含 exposure task、SERP target、AI target、internal link target、schema target。

可參考：

- `src/contentflow/agents/content_compiler/brief_builder.py`
- `src/contentflow/models/content_contracts.py`

驗收：

- create_page / refresh_page 都可產生 brief。

#### EF-0802 建立 Content Execution Adapter

任務：

- 可串接 ContentFlow content compiler。
- 可串接未來其他內容引擎。
- 不把 content engine 寫死為核心。

可參考：

- `src/contentflow/agents/content_compiler/`
- `src/contentflow/agents/orchestrator.py`

驗收：

- ContentExecutionJob 可產生草稿或更新建議。

#### EF-0803 建立 Publisher Adapters

可復用：

- `src/contentflow/publishers/wordpress.py`
- `src/contentflow/publishers/forgebase.py`

任務：

- 支援 publish draft。
- 支援 update existing page。
- 支援 SEO meta。
- 支援 schema。

驗收：

- 可將 approved content brief / draft 發布到 WordPress draft。

#### EF-0804 建立 Publish Gate

可復用：

- `src/contentflow/utils/publish_safety.py`

任務：

- 新增 exposure-specific gate。
- 檢查 schema、fact risk、brand claim、noindex、canonical、AI crawler policy。

驗收：

- 未通過 gate 不可自動發布。

---

### Phase 9：Dashboard / UX

#### EF-0901 建立 Exposure Dashboard

任務：

- 顯示核心 KPI。
- 顯示本月曝光增量。
- 顯示 open opportunities。
- 顯示 topic cluster performance。

驗收：

- 使用者一進入後台就知道曝光版圖狀態。

#### EF-0902 建立 Opportunity Queue UI

任務：

- 顯示 priority、type、reason、evidence。
- 支援 approve / reject / defer。
- 支援 bulk actions。

驗收：

- 顧問可用此頁安排每週工作。

#### EF-0903 建立 SERP Matrix UI

任務：

- keyword × slot matrix。
- 顯示 achieved / target / blocked。
- 支援 snapshot detail。

驗收：

- 可視覺化同一主題多版位覆蓋。

#### EF-0904 建立 AI Visibility UI

任務：

- prompt set management。
- AI answer history。
- citation table。
- brand mention / competitor mention。
- sentiment。

驗收：

- 可看出品牌在 AI 搜尋中的能見度。

---

### Phase 10：Reporting / Client Deliverables

#### EF-1001 建立自然曝光月報

任務：

- 自動生成月報。
- 包含自然曝光、主題、SERP、AI citation、第三方引用、技術問題、下月任務。

驗收：

- 可輸出 Markdown / PDF / DOCX。

#### EF-1002 建立顧問交付模式

任務：

- 支援「Audit」
- 支援「Roadmap」
- 支援「Monthly Retainer」
- 支援「Execution Tracker」
- 支援白標報表。
- 支援客戶入口。
- 支援批註、核准、任務狀態與月會紀錄。

驗收：

- 顧問可用 ExposureFlow 向客戶展示工作成果。
- 客戶可登入自己的 portal 查看報表、roadmap、待核准事項與歷史交付紀錄。

---

### Phase 11：Multi-Tenant SaaS Commercial Layer

正式對外營運的 ExposureFlow 必須從第一天就是多租戶 SaaS，而不是單站工具。

#### EF-1101 建立 Account / Organization / Workspace 商業結構

任務：

- 建立 Account 作為付費主體。
- 建立 Organization 作為公司或顧問團隊主體。
- 建立 Workspace 作為客戶或專案隔離單位。
- 支援一個 account 擁有多個 workspace。
- 支援 agency 帳號代管多個 client workspace。
- 支援 client workspace 移轉所有權。

驗收：

- 顧問公司可建立多個客戶 workspace。
- 客戶可被邀請進入自己的 workspace。
- Workspace 移轉時資料、整合、報表、帳務歸屬可正確處理。

#### EF-1102 建立訂閱方案與使用配額

任務：

- 建立 Plan：Starter、Professional、Agency、Enterprise。
- 每個 plan 定義 site 數、workspace 數、使用者數、GSC row sync 量、SERP snapshot 量、AI probe 量、report export 量。
- 建立 UsageMeter。
- 建立 QuotaPolicy。
- 建立 overage policy。

驗收：

- 每個 workspace 可計算當月使用量。
- 超出配額時可限制排程、提示升級或產生 overage。
- Enterprise 可客製配額。

#### EF-1103 建立 Billing / Invoice / Payment

任務：

- 串接 Stripe 或等效金流。
- 支援 monthly / annual subscription。
- 支援 add-on：額外站點、額外 SERP snapshots、額外 AI probes、額外使用者。
- 支援 invoice、receipt、tax id、付款失敗 retry。
- 支援 trial、coupon、manual enterprise contract。

驗收：

- 使用者可自助升級與降級方案。
- 付款失敗會進入 dunning flow。
- 帳務狀態會影響 workspace access 與 job execution。

#### EF-1104 建立顧問 / Agency 商業模式

任務：

- 支援 agency master dashboard。
- 支援 client workspace summary。
- 支援 white-label domain / logo / report branding。
- 支援 client-level permission。
- 支援 per-client monthly report。

驗收：

- 顧問可用一個帳號管理多個客戶。
- 顧問可輸出帶自己品牌的客戶報表。
- 客戶登入後只看得到自己的資料與交付內容。

---

### Phase 12：Security / Compliance / Reliability

正式對外營運版本必須具備安全、合規與可靠性設計，否則不適合承載多客戶資料與搜尋整合憑證。

#### EF-1201 建立資料隔離與隱私保護

任務：

- 所有租戶資料以 workspace boundary 隔離。
- Integration credentials 加密儲存。
- Secret 使用 KMS 或 secret manager。
- 支援 credential rotation。
- 支援 data export。
- 支援 data deletion / account deletion。
- 支援 retention policy。

驗收：

- 資料庫層測試證明跨 workspace 查詢被阻擋。
- Credential 不以明文出現在 DB、log、error trace。
- 使用者可匯出與刪除自己的 workspace 資料。

#### EF-1202 建立安全稽核與權限治理

任務：

- AuditLog 覆蓋登入、邀請、權限變更、整合授權、報表匯出、發布、刪除、billing。
- 建立 suspicious activity detection。
- 支援 2FA。
- 支援 SSO / SAML for Enterprise。
- 支援 IP allowlist for Enterprise。

驗收：

- Enterprise workspace 可啟用 SSO。
- Admin 可查看安全事件。
- 權限變更可完整追蹤。

#### EF-1203 建立可靠性與營運標準

任務：

- 定義 SLO：API availability、job completion latency、sync freshness。
- 建立 backup / restore。
- 建立 disaster recovery runbook。
- 建立 provider outage handling。
- 建立 queue backpressure。
- 建立 rate limit。
- 建立 circuit breaker。

驗收：

- GSC / SERP / AI provider 故障不會拖垮整個系統。
- Job 可重試且可恢復。
- 可從備份還原 workspace。

#### EF-1204 建立 Observability

任務：

- Structured logging。
- Metrics：API latency、job latency、provider error rate、quota consumption、sync freshness。
- Tracing：request id、job id、workspace id。
- Alerting：sync failure、billing failure、job backlog、provider quota exhaustion。

驗收：

- Internal team 可在營運後台看到系統健康狀態。
- 重大錯誤可追蹤到 workspace、job、provider 與 root cause。

---

### Phase 13：Product Operations / Internal Admin

對外營運產品必須有內部營運後台，否則客服、除錯、帳務、配額、客戶成功都會無法規模化。

#### EF-1301 建立 Internal Admin Console

任務：

- 查看 accounts、organizations、workspaces、sites、users。
- 查看訂閱方案、使用量、付款狀態。
- 查看 job runs、sync status、provider errors。
- 查看 audit logs。
- 執行安全的 support impersonation。
- 管理 feature flags。

驗收：

- Support 可快速定位客戶問題。
- 任何 support action 都被記錄。
- Internal admin 不可繞過敏感資料保護。

#### EF-1302 建立 Customer Success Dashboard

任務：

- 追蹤 workspace activation。
- 追蹤 onboarding completion。
- 追蹤 first GSC sync、first opportunity、first report、first approved decision。
- 追蹤低使用量客戶與流失風險。

驗收：

- 團隊可知道哪些客戶尚未完成啟用。
- 團隊可主動處理高風險客戶。

#### EF-1303 建立 Support / Notification System

任務：

- 系統通知：sync failure、quota warning、report ready、approval required。
- Email notifications。
- In-app notifications。
- Support ticket linking。
- Status page。

驗收：

- 客戶能收到必要通知。
- 重大服務異常可公開或半公開揭露。

---

### Phase 14：Production Launch / Commercial Readiness

此階段是正式對外營運前的產品完整性驗收，不是縮小版產品驗證。

#### EF-1401 建立正式上線檢查表

任務：

- 完成所有核心模組。
- 完成多租戶隔離。
- 完成 billing。
- 完成 usage metering。
- 完成 internal admin。
- 完成 backup / restore。
- 完成 security review。
- 完成 load test。
- 完成 onboarding。
- 完成 documentation。

驗收：

- 可以讓付費客戶自助註冊、付款、建立 workspace、連接 GSC、看到 opportunity、核准任務、取得報表。
- 顧問客戶可建立多個 client workspace 並輸出白標報表。
- 內部團隊可處理客服、帳務、同步失敗、配額問題與系統異常。

#### EF-1402 建立產品文件與對外材料

任務：

- 建立 help center。
- 建立 onboarding guide。
- 建立 integration setup guide。
- 建立 API / webhook docs。
- 建立 security page。
- 建立 pricing page。
- 建立 terms、privacy policy、DPA template。

驗收：

- 新客戶不需要人工協助即可完成基本啟用。
- Enterprise 客戶可取得安全與合規文件。

#### EF-1403 建立正式營運指標

任務：

- Product activation rate。
- Workspace with successful GSC sync。
- Opportunity approved rate。
- Report generated rate。
- Monthly active workspace。
- Retention。
- Expansion revenue。
- Provider cost per workspace。
- Gross margin by plan。

驗收：

- 營運團隊可判斷產品是否健康成長。
- 可知道哪些方案或客戶型態成本過高。

---

## 十、正式可對外營運產品定義

ExposureFlow 的目標是設計成可正式對外收費營運的多租戶 SaaS 產品。因此完整版本必須同時具備「自然曝光最大化產品能力」與「商業化營運能力」。

### 1. 產品核心能力必須完整

- Site onboarding
- Multi-site management
- GSC / GA4 / SERP / Tech SEO connectors
- ExposureAsset
- ExposureOpportunity
- TopicCluster / TopicGraph
- SERP Slot Matrix
- AI Visibility Monitor
- Brand Entity / SERPO Monitor
- Opportunity Scorer
- Decision Plane
- Roadmap Builder
- Execution Plane
- Publisher Adapters
- Publish Gate
- Exposure Dashboard
- Opportunity Queue
- AI Visibility Dashboard
- Client Reports
- Action Outcome Tracking

### 2. 多租戶 SaaS 能力必須完整

- Account / Organization / Workspace / Site
- Agency master account
- Client workspace
- RBAC
- Client portal
- Workspace isolation
- Integration credential isolation
- Usage metering
- Subscription billing
- Plan limits
- Overage
- Feature flags
- Internal admin console
- Support impersonation with audit
- White-label reports
- Notifications
- Help center
- Status page

### 3. 安全、可靠性與營運能力必須完整

- Tenant isolation tests
- Encryption at rest for credentials
- Secret manager / KMS
- Audit logs
- 2FA
- Enterprise SSO / SAML
- Backup / restore
- Disaster recovery runbook
- Provider outage handling
- Queue isolation
- Rate limiting
- Observability
- Alerting
- Data export
- Data deletion
- Legal documents：Terms、Privacy Policy、DPA

### 4. 正式商用驗收標準

產品完成時，必須可以支援以下完整場景：

- 顧問公司註冊 ExposureFlow。
- 顧問公司建立自己的 agency account。
- 顧問為 20 個客戶建立 20 個 client workspaces。
- 每個客戶 workspace 可連接自己的 GSC、GA4、WordPress、SERP provider。
- 每個客戶只能看到自己的 dashboard、roadmap、報表與待核准事項。
- 顧問可以跨客戶查看自然曝光成長、未處理 opportunity、報表狀態與同步健康。
- 系統可以按 workspace 計算 SERP snapshot、AI probe、GSC rows、report export 使用量。
- 系統可以依訂閱方案限制功能與配額。
- 顧問可以輸出白標月報給客戶。
- 客戶可以登入 portal 核准內容更新、技術修復、報表或 roadmap。
- 內部 support 可以排查同步失敗與帳務問題，但所有操作都留下 audit log。
- 當外部 provider 故障時，系統不會造成全站不可用。
- 當客戶取消服務時，可以匯出資料、停用整合、刪除資料。

### 5. 產品上線門檻

ExposureFlow 只有在以下條件滿足後，才算達到「可正式對外營運」：

- 能承載多租戶、多站點、多使用者。
- 能處理付費訂閱、方案限制與配額。
- 能安全儲存與管理客戶整合憑證。
- 能產生自然曝光機會、roadmap、執行任務與 outcome 評估。
- 能讓顧問以白標方式服務客戶。
- 能讓客戶以 client portal 參與核准與查看成果。
- 能讓內部團隊管理客服、帳務、異常、feature flags 與用量。
- 能在 provider 不穩、job 失敗、配額耗盡時穩定降級。
- 能通過基本 security review、load test、backup restore test。

---

## 十一、RD 直接開發交付規格

本節將前述產品藍圖轉成 RD 可直接拆工、建 repo、建 schema、寫 API、切頁面、接整合、寫測試與部署的工程規格。若 RD 需要啟動開發，應以本節作為第一版 implementation spec。

### 1. 固定技術選型

為降低初期決策發散，ExposureFlow 正式商用版採用以下技術組合：

- Monorepo：`pnpm` workspace 或 `turbo`
- Frontend：Next.js 15、React、TypeScript、Tailwind CSS、shadcn/ui
- Backend：Python FastAPI
- ORM / Migration：SQLAlchemy 2.x、Alembic
- Database：PostgreSQL 16
- Vector：pgvector
- Cache / Queue broker：Redis
- Worker：Celery 或 Temporal。若團隊熟悉 Python，第一正式版採 Celery；若追求長期工作流可靠性，可替換為 Temporal。
- Object Storage：S3-compatible storage，例如 AWS S3 或 Cloudflare R2
- Auth：Auth.js / Clerk / 自建 JWT 皆可；若自建，必須支援 workspace role claim。
- Billing：Stripe
- Observability：OpenTelemetry、structured logging、Prometheus-compatible metrics、Sentry
- Deployment：Docker、Kubernetes 或 managed container platform

### 2. Repo 結構

RD 應建立以下 repo 結構：

```text
ExposureFlow/
├── apps/
│   ├── api/
│   │   ├── exposureflow_api/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── auth/
│   │   │   ├── tenants/
│   │   │   ├── billing/
│   │   │   ├── integrations/
│   │   │   ├── exposure/
│   │   │   ├── serp/
│   │   │   ├── ai_visibility/
│   │   │   ├── decision/
│   │   │   ├── execution/
│   │   │   ├── reporting/
│   │   │   ├── admin/
│   │   │   ├── jobs/
│   │   │   └── common/
│   │   ├── alembic/
│   │   └── tests/
│   └── web/
│       ├── app/
│       │   ├── (auth)/
│       │   ├── (dashboard)/
│       │   ├── (client-portal)/
│       │   └── (internal-admin)/
│       ├── components/
│       ├── lib/
│       └── tests/
├── packages/
│   ├── shared-types/
│   ├── ui/
│   └── sdk/
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── runbooks/
│   └── product/
├── infra/
│   ├── docker/
│   ├── k8s/
│   └── terraform/
└── scripts/
```

### 3. 環境與設定

必須支援：

- `local`
- `staging`
- `production`
- `preview`

必要環境變數：

```text
DATABASE_URL
REDIS_URL
APP_ENV
APP_BASE_URL
JWT_SECRET
ENCRYPTION_KEY
S3_ENDPOINT
S3_BUCKET
S3_ACCESS_KEY_ID
S3_SECRET_ACCESS_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
SERPAPI_KEY
SERPER_API_KEY
OPENAI_API_KEY
PERPLEXITY_API_KEY
SENTRY_DSN
```

安全要求：

- `ENCRYPTION_KEY` 不可提交 repo。
- 所有 integration credential 必須加密後再進 DB。
- production 必須使用 secret manager。

### 4. 資料庫 Schema 規格

以下為第一個可開發版本必備 schema。欄位型別可依 ORM 慣例微調，但資料邊界不可改。

#### 4.1 多租戶與權限

```text
accounts
- id uuid pk
- name text not null
- account_type text not null check in ('direct','agency','enterprise')
- billing_customer_id text null
- billing_status text not null default 'active'
- created_at timestamptz not null
- updated_at timestamptz not null

organizations
- id uuid pk
- account_id uuid fk accounts.id
- name text not null
- logo_url text null
- created_at timestamptz not null
- updated_at timestamptz not null

workspaces
- id uuid pk
- account_id uuid fk accounts.id
- organization_id uuid fk organizations.id
- name text not null
- workspace_type text not null check in ('agency_internal','client','enterprise')
- client_name text null
- status text not null default 'active'
- default_locale text not null default 'zh-TW'
- created_at timestamptz not null
- updated_at timestamptz not null

users
- id uuid pk
- email citext unique not null
- name text not null
- avatar_url text null
- status text not null default 'active'
- last_login_at timestamptz null
- created_at timestamptz not null
- updated_at timestamptz not null

workspace_memberships
- id uuid pk
- workspace_id uuid fk workspaces.id
- user_id uuid fk users.id
- role text not null check in ('owner','admin','strategist','editor','analyst','client_viewer','billing_admin')
- status text not null default 'active'
- invited_by uuid fk users.id null
- created_at timestamptz not null
- unique(workspace_id, user_id)
```

索引：

- `workspaces(account_id)`
- `workspace_memberships(user_id)`
- `workspace_memberships(workspace_id, role)`

#### 4.2 Site 與整合

```text
sites
- id uuid pk
- workspace_id uuid fk workspaces.id
- domain text not null
- site_name text not null
- primary_locale text not null
- target_countries jsonb not null default '[]'
- target_languages jsonb not null default '[]'
- industry text null
- business_model text null
- status text not null default 'active'
- created_at timestamptz not null
- updated_at timestamptz not null
- unique(workspace_id, domain)

integration_credentials
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id null
- provider text not null check in ('gsc','ga4','wordpress','forgebase','serpapi','serper','openai','perplexity','bing_webmaster')
- credential_scope text not null check in ('workspace','site')
- encrypted_payload bytea not null
- status text not null default 'active'
- last_verified_at timestamptz null
- created_at timestamptz not null
- updated_at timestamptz not null
```

#### 4.3 Exposure Core

```text
exposure_themes
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- parent_theme_id uuid fk exposure_themes.id null
- name text not null
- description text null
- business_priority int not null default 3
- target_audience text null
- created_at timestamptz not null
- updated_at timestamptz not null

topic_clusters
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- exposure_theme_id uuid fk exposure_themes.id
- name text not null
- pillar_keyword text not null
- pillar_url text null
- coverage_score numeric(5,2) not null default 0
- authority_score numeric(5,2) not null default 0
- total_impressions bigint not null default 0
- ai_visibility_score numeric(5,2) not null default 0
- status text not null default 'active'
- last_analyzed_at timestamptz null
- created_at timestamptz not null
- updated_at timestamptz not null

exposure_assets
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- topic_cluster_id uuid fk topic_clusters.id null
- asset_type text not null
- url text not null
- title text null
- primary_keyword text null
- status text not null default 'active'
- published_at timestamptz null
- last_refreshed_at timestamptz null
- total_impressions bigint not null default 0
- total_clicks bigint not null default 0
- ai_citation_count int not null default 0
- serp_slot_count int not null default 0
- created_at timestamptz not null
- updated_at timestamptz not null
- unique(workspace_id, site_id, url)

exposure_opportunities
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- topic_cluster_id uuid fk topic_clusters.id null
- exposure_asset_id uuid fk exposure_assets.id null
- opportunity_type text not null
- keyword text null
- search_context text null
- target_url text null
- current_url text null
- current_impressions bigint not null default 0
- current_position numeric(6,2) null
- ranking_feasibility_score numeric(5,2) not null default 0
- serp_slot_score numeric(5,2) not null default 0
- ai_citation_score numeric(5,2) not null default 0
- topic_contribution_score numeric(5,2) not null default 0
- zero_click_value_score numeric(5,2) not null default 0
- total_opportunity_score numeric(5,2) not null default 0
- priority text not null check in ('low','medium','high','critical')
- status text not null check in ('open','planned','executing','completed','rejected','monitoring')
- reason text not null
- evidence_json jsonb not null default '{}'
- created_at timestamptz not null
- updated_at timestamptz not null
```

必要索引：

- 所有業務資料表必須建立 `workspace_id` index。
- `exposure_opportunities(workspace_id, status, priority)`
- `exposure_opportunities(site_id, total_opportunity_score desc)`
- `exposure_assets(site_id, url)`
- `topic_clusters(site_id, total_impressions desc)`

#### 4.4 GSC / SERP / AI Visibility

```text
gsc_performance_rows
- id bigserial pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- date date not null
- query text not null
- page text not null
- country text null
- device text null
- impressions bigint not null
- clicks bigint not null
- ctr numeric(8,6) not null
- position numeric(8,3) not null
- created_at timestamptz not null
- unique(site_id, date, query, page, country, device)

serp_query_snapshots
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- keyword text not null
- surface text not null default 'google'
- country text not null
- language text not null
- device text not null
- raw_provider text not null
- raw_json jsonb not null
- captured_at timestamptz not null

serp_slots
- id uuid pk
- workspace_id uuid fk workspaces.id
- snapshot_id uuid fk serp_query_snapshots.id
- slot_type text not null
- position int null
- owner_domain text null
- owner_brand text null
- url text null
- title text null
- snippet text null
- is_own_site boolean not null default false
- is_competitor boolean not null default false
- is_third_party boolean not null default false

ai_probe_sets
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id
- topic_cluster_id uuid fk topic_clusters.id null
- name text not null
- prompts_json jsonb not null
- surfaces_json jsonb not null
- schedule text null
- active boolean not null default true
- created_at timestamptz not null
- updated_at timestamptz not null

ai_probe_runs
- id uuid pk
- workspace_id uuid fk workspaces.id
- probe_set_id uuid fk ai_probe_sets.id
- surface text not null
- prompt text not null
- answer_text text not null
- cited_urls_json jsonb not null default '[]'
- mentioned_brands_json jsonb not null default '[]'
- sentiment text null
- our_brand_mentioned boolean not null default false
- our_url_cited boolean not null default false
- competitor_mentions_json jsonb not null default '[]'
- run_at timestamptz not null
```

#### 4.5 Decision / Execution / Reporting

```text
action_candidates
- id uuid pk
- workspace_id uuid fk workspaces.id
- opportunity_id uuid fk exposure_opportunities.id
- action_type text not null
- target_asset_id uuid fk exposure_assets.id null
- action_payload_json jsonb not null default '{}'
- expected_exposure_impact numeric(8,2) not null default 0
- risk_level text not null check in ('low','medium','high')
- required_inputs_json jsonb not null default '[]'
- evidence_json jsonb not null default '{}'
- created_by text not null check in ('rule','llm','human')
- created_at timestamptz not null

action_decisions
- id uuid pk
- workspace_id uuid fk workspaces.id
- candidate_id uuid fk action_candidates.id
- decision text not null check in ('approve','reject','defer','needs_review')
- selected_by uuid fk users.id
- rationale text not null
- confidence numeric(5,2) null
- scheduled_for date null
- created_at timestamptz not null

execution_jobs
- id uuid pk
- workspace_id uuid fk workspaces.id
- decision_id uuid fk action_decisions.id
- job_type text not null
- status text not null check in ('queued','running','succeeded','failed','cancelled')
- executor_type text not null
- input_json jsonb not null default '{}'
- output_json jsonb not null default '{}'
- error text null
- started_at timestamptz null
- completed_at timestamptz null
- created_at timestamptz not null

reports
- id uuid pk
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id null
- report_type text not null check in ('monthly_exposure','audit','roadmap','client_summary')
- period_start date null
- period_end date null
- status text not null default 'draft'
- title text not null
- storage_url text null
- created_by uuid fk users.id
- created_at timestamptz not null
```

#### 4.6 Billing / Usage / Audit

```text
plans
- id uuid pk
- name text not null
- plan_code text unique not null
- limits_json jsonb not null
- price_monthly_cents int not null
- price_yearly_cents int not null
- active boolean not null default true

subscriptions
- id uuid pk
- account_id uuid fk accounts.id
- plan_id uuid fk plans.id
- stripe_subscription_id text null
- status text not null
- current_period_start timestamptz null
- current_period_end timestamptz null
- created_at timestamptz not null
- updated_at timestamptz not null

usage_events
- id uuid pk
- account_id uuid fk accounts.id
- workspace_id uuid fk workspaces.id
- site_id uuid fk sites.id null
- metric text not null
- quantity int not null
- provider text null
- cost_cents int not null default 0
- idempotency_key text not null
- created_at timestamptz not null
- unique(idempotency_key)

audit_logs
- id uuid pk
- workspace_id uuid fk workspaces.id null
- account_id uuid fk accounts.id null
- actor_user_id uuid fk users.id null
- action text not null
- target_type text not null
- target_id text null
- ip_address inet null
- user_agent text null
- metadata_json jsonb not null default '{}'
- created_at timestamptz not null
```

### 5. API Contract

所有 API 必須遵守：

- Base path：`/api/v1`
- Auth：Bearer token
- Workspace scope：需要 workspace 的 endpoint 必須帶 `X-Workspace-Id`
- Pagination：`limit`、`cursor`
- Error format 固定：

```json
{
  "error": {
    "code": "WORKSPACE_ACCESS_DENIED",
    "message": "You do not have access to this workspace.",
    "details": {}
  }
}
```

#### 5.1 Auth / Workspace

```text
GET    /api/v1/me
GET    /api/v1/workspaces
POST   /api/v1/workspaces
GET    /api/v1/workspaces/{workspace_id}
PATCH  /api/v1/workspaces/{workspace_id}
POST   /api/v1/workspaces/{workspace_id}/invite
GET    /api/v1/workspaces/{workspace_id}/members
PATCH  /api/v1/workspaces/{workspace_id}/members/{member_id}
DELETE /api/v1/workspaces/{workspace_id}/members/{member_id}
```

#### 5.2 Sites / Integrations

```text
GET    /api/v1/sites
POST   /api/v1/sites
GET    /api/v1/sites/{site_id}
PATCH  /api/v1/sites/{site_id}
DELETE /api/v1/sites/{site_id}

GET    /api/v1/integrations
POST   /api/v1/integrations/{provider}/connect
POST   /api/v1/integrations/{provider}/verify
DELETE /api/v1/integrations/{credential_id}
```

#### 5.3 Exposure

```text
GET    /api/v1/exposure/dashboard?site_id=
GET    /api/v1/exposure/assets?site_id=&status=&type=
GET    /api/v1/exposure/assets/{asset_id}
PATCH  /api/v1/exposure/assets/{asset_id}
GET    /api/v1/exposure/opportunities?site_id=&status=&priority=&type=
GET    /api/v1/exposure/opportunities/{opportunity_id}
POST   /api/v1/exposure/opportunities/{opportunity_id}/reject
POST   /api/v1/exposure/opportunities/{opportunity_id}/reopen
```

Dashboard response 必須包含：

```json
{
  "total_impressions": 123456,
  "impressions_delta_pct": 18.4,
  "query_coverage_count": 2400,
  "indexed_asset_count": 180,
  "top_3_count": 24,
  "top_10_count": 120,
  "top_20_count": 310,
  "serp_slot_count": 48,
  "ai_citation_count": 12,
  "open_opportunity_count": 86,
  "critical_blocker_count": 4
}
```

#### 5.4 Topic / SERP / AI

```text
GET    /api/v1/topics/clusters?site_id=
GET    /api/v1/topics/clusters/{cluster_id}
POST   /api/v1/topics/clusters/rebuild

GET    /api/v1/serp/snapshots?site_id=&keyword=
POST   /api/v1/serp/snapshots/run
GET    /api/v1/serp/matrix?site_id=&cluster_id=

GET    /api/v1/ai/probe-sets?site_id=
POST   /api/v1/ai/probe-sets
PATCH  /api/v1/ai/probe-sets/{probe_set_id}
POST   /api/v1/ai/probe-sets/{probe_set_id}/run
GET    /api/v1/ai/probe-runs?probe_set_id=
GET    /api/v1/ai/visibility/dashboard?site_id=
```

#### 5.5 Decision / Execution / Reporting

```text
GET    /api/v1/decisions/candidates?site_id=&status=
POST   /api/v1/decisions/candidates/{candidate_id}/approve
POST   /api/v1/decisions/candidates/{candidate_id}/reject
POST   /api/v1/decisions/candidates/{candidate_id}/defer
GET    /api/v1/roadmaps?site_id=
POST   /api/v1/roadmaps/build

GET    /api/v1/execution/jobs?site_id=&status=
GET    /api/v1/execution/jobs/{job_id}
POST   /api/v1/execution/jobs/{job_id}/cancel
POST   /api/v1/execution/jobs/{job_id}/retry

GET    /api/v1/reports?site_id=&type=
POST   /api/v1/reports/monthly-exposure
GET    /api/v1/reports/{report_id}
POST   /api/v1/reports/{report_id}/export
```

#### 5.6 Billing / Admin

```text
GET    /api/v1/billing/subscription
POST   /api/v1/billing/checkout
POST   /api/v1/billing/portal
GET    /api/v1/billing/usage
POST   /api/v1/webhooks/stripe

GET    /api/v1/internal/accounts
GET    /api/v1/internal/workspaces
GET    /api/v1/internal/jobs
GET    /api/v1/internal/provider-errors
POST   /api/v1/internal/impersonation/start
POST   /api/v1/internal/impersonation/stop
```

### 6. 前端頁面規格

#### 6.1 Agency Dashboard

路徑：

```text
/app/agency
```

顯示：

- 所有 client workspaces
- 每個客戶本月自然曝光變化
- open opportunities
- report status
- sync health
- quota usage

操作：

- 建立 client workspace
- 邀請客戶
- 進入客戶 workspace
- 產出白標月報

#### 6.2 Workspace Exposure Dashboard

路徑：

```text
/app/[workspaceId]/sites/[siteId]/dashboard
```

顯示：

- Total organic impressions
- Query coverage
- Indexed assets
- Top 3 / Top 10 / Top 20
- SERP slot ownership
- AI citations
- Open opportunities
- Critical technical blockers
- Topic cluster growth

#### 6.3 Opportunity Queue

路徑：

```text
/app/[workspaceId]/sites/[siteId]/opportunities
```

欄位：

- priority
- opportunity type
- keyword
- current URL
- score
- reason
- evidence
- recommended action
- status

操作：

- approve
- reject
- defer
- assign owner
- convert to roadmap item
- bulk approve

#### 6.4 SERP Matrix

路徑：

```text
/app/[workspaceId]/sites/[siteId]/serp-matrix
```

功能：

- keyword × slot type matrix
- slot status：owned、competitor、third-party、available、blocked
- snapshot detail
- run new snapshot
- generate slot opportunity

#### 6.5 AI Visibility

路徑：

```text
/app/[workspaceId]/sites/[siteId]/ai-visibility
```

功能：

- prompt set list
- run probe
- AI citation history
- brand mention rate
- competitor mention rate
- sentiment
- entity inconsistency

#### 6.6 Roadmap

路徑：

```text
/app/[workspaceId]/sites/[siteId]/roadmap
```

功能：

- 4 / 8 / 16 週 roadmap
- action dependencies
- owner
- status
- due date
- client approval status

#### 6.7 Client Portal

路徑：

```text
/client/[workspaceId]
```

客戶可看：

- monthly report
- roadmap
- waiting approvals
- completed actions
- exposure trend

客戶不可看：

- internal scoring details
- provider credentials
- other clients
- billing unless role is billing admin

#### 6.8 Internal Admin

路徑：

```text
/internal
```

功能：

- accounts
- workspaces
- users
- subscriptions
- usage
- job runs
- provider errors
- audit logs
- feature flags
- support impersonation

### 7. 權限矩陣

| 功能 | Owner | Admin | Strategist | Editor | Analyst | Client Viewer | Billing Admin | Support Admin |
|---|---|---|---|---|---|---|---|---|
| 管理 workspace | Yes | Yes | No | No | No | No | No | Support |
| 管理成員 | Yes | Yes | No | No | No | No | No | Support |
| 連接整合 | Yes | Yes | No | No | No | No | No | Support |
| 查看 dashboard | Yes | Yes | Yes | Yes | Yes | Limited | No | Support |
| 核准 opportunity | Yes | Yes | Yes | No | No | Limited | No | No |
| 編輯內容任務 | Yes | Yes | Yes | Yes | No | No | No | No |
| 查看 client report | Yes | Yes | Yes | Yes | Yes | Yes | No | Support |
| 管理 billing | Yes | No | No | No | No | No | Yes | Support |
| Internal admin | No | No | No | No | No | No | No | Yes |

### 8. Worker Jobs

必備 job：

```text
gsc.sync.site
ga4.sync.site
serp.snapshot.keyword
serp.snapshot.cluster
tech_seo.audit.site
topic_graph.rebuild.site
opportunity.generate.site
opportunity.score.site
ai_probe.run.set
decision.candidates.generate
roadmap.build.site
wordpress.publish_draft
wordpress.update_post
report.monthly.generate
usage.rollup.account
billing.sync.stripe
notifications.dispatch
```

Job 要求：

- 每個 job 必須帶 `workspace_id`。
- 每個 external API job 必須記錄 usage event。
- 所有 job 必須 idempotent。
- 支援 retry with exponential backoff。
- 支援 dead letter queue。
- 支援 manual retry。

### 9. ContentFlow 移植開發票

#### EF-CF-001 移植 GSC connector

來源：

```text
ContentFlow/src/contentflow/tools/gsc.py
```

交付：

- `apps/api/exposureflow_api/integrations/gsc/client.py`
- `apps/api/exposureflow_api/jobs/gsc_sync.py`
- tests for sync and incremental import

驗收：

- 可同步 query/page/date/country/device。
- 可寫入 `gsc_performance_rows`。
- 失敗時不影響其他 workspace。

#### EF-CF-002 移植 SERP connector

來源：

```text
ContentFlow/src/contentflow/tools/serp.py
```

交付：

- `integrations/serp/providers/serper.py`
- `integrations/serp/providers/serpapi.py`
- `serp/slot_extractor.py`

驗收：

- 支援 Serper / SerpAPI fallback。
- 產生 `serp_query_snapshots` 與 `serp_slots`。

#### EF-CF-003 移植 WordPress publisher

來源：

```text
ContentFlow/src/contentflow/publishers/wordpress.py
```

交付：

- `execution/publishers/wordpress.py`
- publish draft
- update post
- SEO meta
- featured image best effort

驗收：

- 能將 approved execution job 發布為 WordPress draft。
- credential 使用 site scope。

#### EF-CF-004 移植 Publish Gate

來源：

```text
ContentFlow/src/contentflow/utils/publish_safety.py
```

交付：

- `execution/safety/publish_gate.py`
- schema gate
- fact risk gate
- noindex / canonical gate
- AI crawler policy gate

驗收：

- gate 未通過時 execution job 不可進入 publish。

### 10. Engineering Backlog

以下 tickets 可直接匯入 Linear / Jira。

#### EPIC-A：多租戶基礎

- EF-A001 建立 monorepo 與 CI
- EF-A002 建立 FastAPI app skeleton
- EF-A003 建立 Next.js app skeleton
- EF-A004 建立 PostgreSQL / Alembic
- EF-A005 建立 Account / Organization / Workspace schema
- EF-A006 建立 User / Membership / RBAC
- EF-A007 建立 workspace middleware
- EF-A008 建立 audit log middleware
- EF-A009 建立 invitation flow
- EF-A010 建立 tenant isolation tests

#### EPIC-B：Site 與整合

- EF-B001 建立 Site CRUD
- EF-B002 建立 IntegrationCredential encrypted storage
- EF-B003 建立 GSC connect flow
- EF-B004 建立 GA4 connect flow
- EF-B005 建立 WordPress credential verification
- EF-B006 建立 SERP provider settings
- EF-B007 建立 integration health check

#### EPIC-C：Exposure Core

- EF-C001 建立 ExposureAsset schema / API
- EF-C002 建立 GSC import to asset matching
- EF-C003 建立 ExposureOpportunity schema / API
- EF-C004 建立 opportunity generator v1
- EF-C005 建立 opportunity scorer v1
- EF-C006 建立 dashboard metrics API
- EF-C007 建立 action outcome tracking

#### EPIC-D：Topic / SERP / AI

- EF-D001 建立 TopicCluster schema / API
- EF-D002 建立 topic graph rebuild job
- EF-D003 建立 cannibalization detector
- EF-D004 建立 SERP snapshot job
- EF-D005 建立 SERP slot extractor
- EF-D006 建立 SERP Matrix UI
- EF-D007 建立 AIProbeSet schema / API
- EF-D008 建立 AI probe run job
- EF-D009 建立 AI citation extractor
- EF-D010 建立 AI Visibility UI

#### EPIC-E：Decision / Execution

- EF-E001 建立 ActionCandidate schema / API
- EF-E002 建立 approve / reject / defer flow
- EF-E003 建立 Roadmap Builder
- EF-E004 建立 ExecutionJob schema / API
- EF-E005 建立 Content Brief Builder
- EF-E006 建立 WordPress publish draft job
- EF-E007 建立 Publish Gate
- EF-E008 建立 execution retry / cancel

#### EPIC-F：Reporting / Client Portal

- EF-F001 建立 report schema
- EF-F002 建立 monthly exposure report generator
- EF-F003 建立 PDF / DOCX export
- EF-F004 建立 client portal dashboard
- EF-F005 建立 client approval flow
- EF-F006 建立 white-label branding

#### EPIC-G：Billing / Usage / Admin

- EF-G001 建立 Plan / Subscription schema
- EF-G002 串接 Stripe checkout
- EF-G003 串接 Stripe webhook
- EF-G004 建立 usage event tracking
- EF-G005 建立 quota enforcement
- EF-G006 建立 billing page
- EF-G007 建立 internal admin accounts page
- EF-G008 建立 internal job monitor
- EF-G009 建立 support impersonation with audit
- EF-G010 建立 customer success dashboard

#### EPIC-H：Production Readiness

- EF-H001 建立 structured logging
- EF-H002 建立 metrics / tracing
- EF-H003 建立 Sentry
- EF-H004 建立 backup / restore runbook
- EF-H005 建立 provider outage handling
- EF-H006 建立 rate limiting
- EF-H007 建立 load test
- EF-H008 建立 security review checklist
- EF-H009 建立 help center docs
- EF-H010 建立 production launch checklist

### 11. Definition of Done

每張 RD ticket 必須符合：

- 有 migration 或確認不需要 migration。
- 有 API tests 或 component tests。
- 有 tenant isolation test，若涉及 workspace data。
- 有 role permission test，若涉及操作權限。
- 有 audit log，若涉及敏感操作。
- 有 usage event，若涉及外部 API 成本。
- 有 error handling。
- 有 observability log。
- 有 staging 驗證。
- 有文件更新。

### 12. 測試策略

必備測試：

- Unit tests：scorer、slot extractor、credential encryption、quota policy
- API tests：workspace access、CRUD、permission denied、pagination
- Integration tests：GSC sync、SERP snapshot、WordPress publish draft、Stripe webhook
- Tenant isolation tests：跨 workspace 讀寫必須失敗
- Worker tests：retry、idempotency、dead letter
- E2E tests：agency 建立 client workspace、連接 GSC、產生 opportunity、核准 decision、輸出 report
- Load tests：dashboard、opportunity list、job queue throughput
- Security tests：credential leakage、role escalation、support impersonation audit

### 13. 部署與營運規格

Production 必須至少包含：

- API service
- Web service
- Worker service
- Scheduler service
- PostgreSQL
- Redis
- Object storage
- Secret manager
- Metrics collector
- Error tracking
- Backup job

部署要求：

- zero-downtime migration strategy
- blue/green 或 rolling deploy
- staging 與 production 分離
- database backup daily
- object storage lifecycle policy
- worker autoscaling
- provider API quota alerts

### 14. RD 開發啟動順序

RD 應依以下順序開工：

1. 建 repo、CI、local dev、PostgreSQL、Redis。
2. 建 Account / Workspace / User / RBAC / tenant middleware。
3. 建 Site / IntegrationCredential / encrypted storage。
4. 移植 GSC connector，完成第一個資料接入閉環。
5. 建 ExposureAsset / ExposureOpportunity / dashboard API。
6. 建前端 Dashboard / Opportunity Queue。
7. 移植 SERP connector，完成 SERP Matrix。
8. 建 Decision / Execution / WordPress draft。
9. 建 Reporting / Client Portal。
10. 建 Billing / Usage / Internal Admin。
11. 補齊 AI Visibility。
12. 完成 production readiness。

完成第 1 到第 10 步後，產品已具備商業 SaaS 主體；第 11 與第 12 步使其符合 ExposureFlow 的完整差異化與正式營運標準。

---

## 十二、不要做的事

為避免 ExposureFlow 變成 ContentFlow 2.0，以下事項應避免：

- 不以「每天自動寫幾篇文章」作為產品核心。
- 不把 16 個 agent 當成產品賣點。
- 不以 SEO score 作為唯一品質指標。
- 不把低 CTR 一律視為錯誤。
- 不把 conversion、leads、revenue 混入第一階段主 KPI。
- 不先做社群排程。
- 不先做通用內容日曆工具。
- 不讓 AI agent 憑空決定 action，所有決策需來自 evidence-backed candidate。
- 不把全自動發布作為預設模式；正式商用版仍應以 human-approved workflow 為主，Enterprise 可另行開啟更高自動化。

---

## 十三、ContentFlow 到 ExposureFlow 的移植策略

### 1. Library Extraction

將以下檔案抽成可移植 library：

```text
ContentFlow/src/contentflow/tools/gsc.py
ContentFlow/src/contentflow/tools/ga4.py
ContentFlow/src/contentflow/tools/serp.py
ContentFlow/src/contentflow/tools/tech_seo.py
ContentFlow/src/contentflow/tools/brand_mentions.py
ContentFlow/src/contentflow/publishers/wordpress.py
ContentFlow/src/contentflow/publishers/forgebase.py
ContentFlow/src/contentflow/utils/publish_safety.py
ContentFlow/src/contentflow/utils/article_schema.py
ContentFlow/src/contentflow/utils/slug_governance.py
```

每個 library 都要：

- 移除對 ContentFlow settings 的硬依賴。
- 改成 dependency injection。
- 改成 ExposureFlow schema。
- 增加 adapter tests。

### 2. Logic Translation

以下檔案不直接搬，但翻譯其商業邏輯：

```text
ContentFlow/src/contentflow/agents/site_intelligence.py
ContentFlow/src/contentflow/agents/analytics_agent.py
ContentFlow/src/contentflow/agents/cluster_agent.py
ContentFlow/src/contentflow/agents/refresh_agent.py
ContentFlow/src/contentflow/agents/content_compiler/
```

翻譯方式：

- 從 article-centric 改成 exposure-centric。
- 從 recommendation 改成 evidence-backed opportunity。
- 從 single page performance 改成 topic-level performance。

### 3. Reference Only

以下檔案只作為反面經驗或歷史參考：

```text
ContentFlow/src/contentflow/models/database.py
ContentFlow/src/contentflow/admin/app.py
ContentFlow/src/contentflow/agents/strategic_agent.py
ContentFlow/src/contentflow/agents/orchestrator.py
ContentFlow/src/contentflow/scheduler.py
```

不直接搬的原因：

- 以文章與 pipeline 為中心。
- 檔案過大，耦合高。
- 會把 ExposureFlow 拉回 ContentFlow 的產品心智。

---

## 十四、風險與對策

### 風險 1：新產品又長回文章工廠

對策：

- 所有頁面與報表以 ExposureOpportunity、TopicCluster、SERPSlot、AICitation 為主。
- Article 只能是 ExposureAsset 的一種。

### 風險 2：AI 搜尋資料不可穩定自動化

對策：

- 正式產品同時支援 scheduled probe、manual probe 與人工補錄，避免把 AI 搜尋資料穩定性完全押在單一自動化來源。
- 不承諾精準排名。
- 追蹤 brand mention、citation、sentiment、competitor presence 即可。

### 風險 3：SERP API 不完整

對策：

- 設計 provider abstraction。
- raw snapshot 永久保存。
- slot extractor 可迭代。

### 風險 4：過度自動決策

對策：

- Candidate deterministic。
- LLM 只排序與解釋。
- Human approval 預設開啟。

### 風險 5：顧問服務場景需要彈性

對策：

- 支援 export report。
- 支援 manual task。
- 支援 opportunity override。

### 風險 6：多租戶資料外洩

對策：

- 從資料模型、API middleware、job queue、object storage、report export 全層實作 tenant boundary。
- 每個核心 query 都必須帶 workspace scope。
- 建立跨租戶讀寫的自動化測試。
- Support impersonation 必須預設關閉，開啟時需完整 audit。

### 風險 7：外部 API 成本失控

對策：

- SERP snapshots、AI probes、GSC row sync、report exports 全部進入 usage metering。
- 每個 plan 有硬配額與 soft warning。
- Provider cost 必須能回算到 workspace 與 account。
- 高成本任務需排程、快取與去重。

### 風險 8：正式商用後客服無法規模化

對策：

- 建立 internal admin console。
- 建立 job run detail、sync health、provider error、billing state。
- 建立 customer success activation dashboard。
- 建立 help center、status page 與產品內通知。

---

## 十五、開發順序總表

| Phase | 目標 | 核心交付 |
|---|---|---|
| 0 | 產品核心定義 | North Star、KPI、復用邊界 |
| 1 | 多租戶基礎架構 | Account、Organization、Workspace、Site、RBAC、Job、Audit |
| 2 | 資料接入 | GSC、GA4、SERP、Tech SEO |
| 3 | Exposure Core | ExposureAsset、Opportunity、Scorer |
| 4 | Topic Graph | Cluster、Coverage、Cannibalization、Internal Links |
| 5 | SERP Matrix | SERP Slot、Slot Target、PAA / Snippet Opportunity |
| 6 | AI Visibility | Probe、Citation、Brand Mention、Sentiment |
| 7 | Decision Plane | Candidate、Decision、Roadmap |
| 8 | Execution Plane | Brief、Content Adapter、Publisher、Gate |
| 9 | UX | Dashboard、Opportunity Queue、SERP Matrix、AI Visibility |
| 10 | Reporting | 月報、顧問交付、DOCX/PDF |
| 11 | Multi-Tenant SaaS Commercial Layer | Account 結構、方案、配額、Billing、Agency 模式 |
| 12 | Security / Compliance / Reliability | 資料隔離、加密、SSO、Backup、SLO、Observability |
| 13 | Product Operations / Internal Admin | 營運後台、客服支援、Customer Success、通知 |
| 14 | Production Launch / Commercial Readiness | 正式上線檢查、對外文件、商業營運指標 |

---

## 十六、最終結論

若完全不考慮開發成本與時間，ExposureFlow 應該乾淨重寫產品核心，並且從一開始就以「可正式對外營運的多租戶 SaaS」為產品規格，而不是以縮小版產品或單站工具為規格。

但這不代表完全不使用 ContentFlow。ContentFlow 已有許多成熟底層能力，應被拆出來作為 adapter 或 library 使用，而不是保留原本的文章工廠架構。

最終建議：

```text
新建 ExposureFlow repo
新建 exposure-first database schema
新建 exposure-first decision plane
新建 SERP / AI visibility measurement plane
新建 multi-tenant SaaS commercial layer
新建 billing / quota / usage metering
新建 internal admin / support / customer success layer
新建 security / reliability / compliance layer
選擇性移植 ContentFlow connectors、publishers、safety utilities
把 ContentFlow content pipeline 降級為可選 execution adapter
```

這樣才能避免長期被「文章自動化」心智綁住，也能確保 ExposureFlow 不是顧問自用工具，而是一套可對外收費、可支援多客戶、多站點、多團隊與長期營運的自然曝光最大化 SaaS 產品。
