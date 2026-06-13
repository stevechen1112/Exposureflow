# Product North Star Spec

**文件編號**：EF-0001  
**狀態**：Phase 0 交付物  
**權威關係**：本文件為 ExposureFlow 產品決策的最高業務準則；工程實作細節以 `exposureflow-development-plan.md` 為準。

---

## 1. 一句話定義

ExposureFlow 是一套把 **SEO、SERP 版位、AI 搜尋引用與第三方品牌曝光** 整合成 **自然曝光資產管理** 的多租戶 SaaS 作業系統。

---

## 2. 唯一北極星

### 主目標

**自然曝光（Organic Impressions）最大化。**

系統存在的目的，是讓品牌在更多相關搜尋情境、SERP 版位、AI 回答與第三方來源中被看見——而不是優先追求發文量、短期流量或成交轉換。

### 管理的核心問題

- 哪些搜尋情境還沒有被品牌覆蓋？
- 哪些關鍵字具備可取得的曝光機會？
- 哪些 SERP 版位可以搶（精選摘要、PAA、圖片、影片、Product、AI Overview 等）？
- 哪些主題應新增、更新、合併、轉址或不動作？
- 哪些內容具備 AI 搜尋引用機會？
- 品牌是否在 ChatGPT Search、Perplexity、Copilot、Google AI Overviews 中被提及或引用？
- 哪些技術問題阻礙索引、爬取或 AI crawler 存取？
- 如何用 **曝光增量** 而非發文量管理 SEO 工作？

---

## 3. 核心物件（第一級產品語言）

| 物件 | 角色 |
|------|------|
| `ExposureOpportunity` | 待處理的自然曝光機會 |
| `ExposureAsset` | 已存在或計畫中的曝光資產（頁面、工具、白皮書等） |
| `TopicCluster` / `TopicNode` | 主題覆蓋與缺口 |
| `SERPSlot` / `SERPSlotTarget` | SERP 版位觀察與目標 |
| `AICitation` / `AIProbeRun` | AI 搜尋引用與探測紀錄 |
| `BrandEntity` / `BrandMention` / `SERPORecord` | 品牌實體與搜尋結果頁曝光 |
| `ActionCandidate` / `ActionDecision` | 證據導向的決策 |
| `ActionOutcome` | 行動後的曝光成效 |

**不是**第一級物件：`Article`、`ContentCalendar`、`PipelineRun`、`SEO Score`（ContentFlow 文章工廠心智）。

---

## 4. 第一版明確排除的主 KPI

以下指標 **不得** 作為 ExposureFlow 第一版的核心決策依據或 Dashboard 北極星：

- Leads 數量
- 成交數 / Revenue
- Conversion Rate 作為內容優先級主排序因子
- 每日自動產文數
- 單一 `SEO Score` 作為品質門檻
- 低 CTR 一律視為失敗（需先診斷零點擊曝光情境）

上述指標可作為 **輔助診斷** 或未來擴充，但不改變北極星。

---

## 5. 零點擊曝光的價值

### 定義

當品牌、頁面、資料或第三方引用出現在 SERP 或 AI 回答中，**即使使用者未點擊**，仍計入自然曝光資產。

### 包含情境

- 傳統自然搜尋結果中的展示（impressions）
- SERP 特殊版位（精選摘要、PAA、圖片、影片等）中的品牌或內容露出
- AI 摘要中的支援連結或來源標示
- AI 回答中的 citation、brand mention
- 第三方文章、論壇、媒體中的品牌提及

### 產品含義

- Dashboard 與報表以 **impressions、版位覆蓋、引用次數** 為主，不以 CTR 單獨否定曝光價值。
- 低 CTR 觸發的是 **診斷流程**（標題、SERP 擠壓、零點擊版位、AI 摘要），不是自動判定內容失敗。
- Opportunity Scorer 含 `zero_click_value_score` 維度。

---

## 6. 決策原則

每個曝光機會先判斷動作類型，而非預設「寫新文章」：

| 動作 | 說明 |
|------|------|
| `create` | 新增頁面或資產 |
| `refresh` | 更新既有頁面 |
| `merge` / `redirect` | 治理關鍵字蠶食 |
| `enrich` | 補 FAQ、表格、schema、圖片、影片 |
| `outreach` | 爭取第三方引用 |
| `technical_fix` | 修復索引 / 爬蟲 / 技術阻礙 |
| `no_op` | 經證據判斷無需動作 |

所有決策須 **evidence-backed**；LLM 可解釋與排序，**不可憑空產生 action**。Human approval 為預設發布與高風險動作閘門。

---

## 7. 與 ContentFlow 的產品切割

| 維度 | ContentFlow | ExposureFlow |
|------|-------------|--------------|
| 北極星 | 全自動 SEO 內容閉環 | 自然曝光資產最大化 |
| 核心問題 | 今天要寫什麼文章？ | 哪些曝光版位還沒被佔住？ |
| 主工作流 | generate → publish | observe → opportunity → decide → execute → measure |
| 主介面 | 文章管理、Agent 執行中心 | Exposure Map、Opportunity Queue、SERP Matrix、AI Visibility |

ContentFlow 的 connector / publisher 能力可作 **Execution Plane adapter**，不得定義產品核心。

---

## 8. 模組與北極星對齊（驗收用）

| 模組 / Phase | 必須服務的北極星維度 |
|--------------|----------------------|
| Exposure Intelligence (P2–P3) | exposure growth、query/page coverage |
| Topic Graph (P4) | topic coverage |
| SERP Matrix (P5) | slot coverage |
| AI Visibility (P6) | AI visibility、brand mention |
| Decision Plane (P7) | 將觀察轉為可執行曝光行動 |
| Execution Plane (P8) | 執行 approved 決策以擴大曝光 |
| Measurement / Dashboard (P9) | 曝光增量、版位、主題、AI 可見性 |
| Reporting (P10) | 向客戶證明曝光資產成長 |
| SaaS / Security / Admin (P11–P13) | 支撐多租戶營運，不取代曝光北極星 |
| Production Launch (P14) | 可對外營運的完整曝光管理平台 |

---

## 9. 成功定義（產品層級）

Phase 0–14 全部完成後，ExposureFlow 應能讓顧問或企業：

1. 連接站點與搜尋資料源，建立曝光基準線。
2. 自動發現並排序自然曝光機會。
3. 以主題、SERP 版位、AI 引用多維度檢視曝光版圖。
4. 經證據與審核執行內容、技術、外聯等行動。
5. 量測行動對曝光、版位、引用的成效。
6. 以多租戶 SaaS 模式服務多客戶並計費營運。

---

## 10. 參考文件

- `docs/product/organic-impressions-seo-plan.md` — 策略方法論
- `docs/product/kpi-taxonomy.md` — KPI 分類
- `docs/product/exposureflow-development-plan.md` — 工程與 Phase 規格
- `AGENTS.md` — 開發憲章
