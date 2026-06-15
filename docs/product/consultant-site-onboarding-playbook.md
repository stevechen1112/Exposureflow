# 目標網站串接 Playbook（Consultant-Led）

**適用對象**：SEO 顧問／代理商（ExposureFlow 操作者）  
**適用範圍**：**每一個**新接入的 client workspace + 目標網站（Site）  
**商業模式**：依 [`gtm-deployment-scope.md`](./gtm-deployment-scope.md) — 人工簽約、顧問代操、客戶現階段不進系統  
**正式環境**：https://app.kakusinn.com（見根目錄 [`README.md`](../../README.md)）

> 本文件為 **任何目標網站** 接入 ExposureFlow 的標準 SOP。  
> 與 `docs/help/onboarding-guide.md`（偏自助）不同，本 Playbook 以 **顧問交付** 為準。

---

## 1. 流程總覽

每一案新網站都走同一條主線：

```text
【線下】簽約 + 收款
    ↓
【平台】開通顧問帳號 → 建立 client workspace
    ↓
【系統】建立 Site（目標網域）→ Strategy / 關鍵字金字塔 / 交付承諾
    ↓
【整合】連 GSC（必備）→ 首次 sync → 確認資料進系統
    ↓
【交付】Opportunity 檢視 → Decision 核准 → Roadmap → 月報（PDF 線下給客戶）
    ↓
【可選】GA4、SERP、Tech SEO、Client Portal（依方案／階段）
```

**現階段驗收（每一案至少）**：

1. Site 建立且 Strategy 已填  
2. GSC sync 成功  
3. Opportunities 可列出  
4. 至少 1 份 report 可匯出  

---

## 2. 前置條件（接案前）

### 2.1 平台與權限

| 項目 | 要求 |
|------|------|
| 顧問登入 | https://app.kakusinn.com/app-entry |
| 角色 | `owner` / `admin` / `strategist`（需 `integration:write` 才能連線與 sync） |
| 開發切角色（staging） | https://app.kakusinn.com/dev/login |
| API 健康檢查 | https://app.kakusinn.com/health |

### 2.2 商業前提（線下完成）

- [ ] 合約已簽署  
- [ ] 收款已約定（**不需** Stripe 自助結帳）  
- [ ] 服務範圍已口頭／書面確認（月報頻率、是否含內容產出等）  
- [ ] 指定 **單一主要聯絡窗口**（客戶端決策者）

### 2.3 目標網站基本條件

- [ ] 網站可公開訪問（HTTPS 建議）  
- [ ] 網域所有權／GSC 驗證可由客戶配合  
- [ ] 已知 **主要轉換目標**（來電、表單、LINE、預約等）

---

## 3. 顧問在系統內的操作（逐步）

以下 `{workspaceId}`、`{siteId}` 為建立後由 URL 取得。

### Phase A — 建立 Workspace 與 Site

| # | 動作 | 路徑／位置 |
|---|------|------------|
| A1 | 登入顧問後台 | `/app-entry` |
| A2 | 建立 **client workspace**（類型 `client`） | Agency 或營運 SOP（若已有 workspace 可略過） |
| A3 | 建立 **Site** | **Settings → 站點管理** `/app/{workspaceId}/settings/sites` |
| A4 | 填寫 Site 基本資料 | domain、site_name、產業等 |
| A5 | 開啟 Onboarding 檢查 | `/app/{workspaceId}/onboarding` |

#### Site 建立方式（2026-06 更新）

| 方式 | 說明 |
|------|------|
| **Settings → 站點管理**（標準） | `/app/{workspaceId}/settings/sites` — 新增、編輯 domain／名稱／市場設定 |
| **Agency 總覽** | 建立 **client workspace** 後導向站點管理 |
| **API** | `POST /api/v1/sites`、`PATCH /api/v1/sites/{id}`（SDK 已接前端） |
| **Dev 登入** | 僅 `APP_ENV=local` 才可能自動建立 `demo.example.com`；**staging／正式顧問環境不會** |

Onboarding 第 1 步「建立站點」→ **站點管理** 頁。

**Site 必填欄位（API schema）**：

| 欄位 | 說明 | 範例 |
|------|------|------|
| `domain` | 主網域，不含 path | `example.com.tw` |
| `site_name` | 顯示名稱 | `恆惠修理紗窗` |
| `primary_locale` | 預設 `zh-TW` | `zh-TW` |
| `target_countries` | 目標國家 | `["TW"]` |
| `target_languages` | 目標語言 | `["zh-TW"]` |
| `industry` | 產業（選填） | `本地居家維修` |
| `business_model` | 商業模式（選填） | `到府服務、電話詢價` |

### Phase B — 策略面談與 Business Scope（顧問主導）

> 依 `exposureflow-development-plan.md` §7：**先面談、再關鍵字佈局**，系統機會發現限於 business scope 內。

| # | 動作 | 路徑 |
|---|------|------|
| B1 | 記錄面談摘要、服務項目、不做的項目 | `/app/{workspaceId}/sites/{siteId}/strategy` |
| B2 | 建立 **關鍵字金字塔** | `/app/{workspaceId}/sites/{siteId}/keyword-pyramid` |
| B3 | 設定 **Delivery Commitments**（每月交付量） | `/app/{workspaceId}/sites/{siteId}/delivery-commitments` |
| B4 | 確認 onboarding「Strategy」步驟 | `/app/{workspaceId}/onboarding` |

**關鍵字金字塔建議結構**：

| 層級 | 內容 |
|------|------|
| 核心品牌／服務詞 | 主業務 3～8 個 |
| 主題支柱 | 各服務線 1 個支柱頁概念 |
| 集群關鍵字 | 區域 + 服務組合 |
| 長尾／問題型 | 「如何判斷」「價格」「保養」等 |
| **排除** | 與客戶業務無關、不承接的 query → 標 `out_of_scope` |

### Phase C — 整合與首次 Sync（GSC 必備）

| # | 動作 | 路徑 |
|---|------|------|
| C1 | 確認客戶已提供 GSC 權限（§5） | 線下 |
| C2 | 新增 GSC credential | `/app/{workspaceId}/settings/integrations` |
| C3 | 觸發 **GSC sync** | Integrations →「觸發 GSC 同步」 |
| C4 | 確認 sync state 成功 | Integrations 同步歷史；Onboarding GSC 步驟 |
| C5 | 檢視 Dashboard 是否有曝光資料 | `/app/{workspaceId}/sites/{siteId}/dashboard` |

**GSC Property 必須與 Site 網域一致**，常見格式：

- `https://example.com/`（URL prefix property）  
- `sc-domain:example.com`（網域 property）

**現況（工程）**：

- Integrations UI「設定連線」→ **OAuth 待實作（Step 3）**  
- 暫時可用 **Service Account** + API `POST /api/v1/integrations/credentials`（需工程或 runbook 協助）  
- Sync handler 與後端 job **已存在**，credential 就緒後即可觸發  

詳見 [`integration-setup.md`](../help/integration-setup.md)。

### Phase D — 機會、決策、報表

| # | 動作 | 路徑 |
|---|------|------|
| D1 | 檢視 Exposure Opportunities | `.../opportunities` |
| D2 | 核准／延後 Decision | `.../opportunities` 或 Decision 佇列 |
| D3 | 檢視 Roadmap | `.../roadmap` |
| D4 | 產生月報 | Dashboard / Reporting |
| D5 | 匯出 **PDF** 線下交客戶 | 報表匯出（現階段不開 Client Portal） |

### Phase E — 可選整合（依方案）

| 整合 | 用途 | 客戶需提供 | 平台 env |
|------|------|------------|----------|
| GA4 | 流量、轉換 | GA4 讀取權限或 SA | credential |
| SERP | 排名／版位矩陣 | — | `SERPER_API_KEY` 或 `SERPAPI_API_KEY` |
| Tech SEO | 爬蟲技術問題 | 無（seed URL 即可） | Integrations 觸發 crawl |
| Bing WMT | Bing 搜尋資料 | Bing API key | credential |
| WordPress | 內容發布 | WP API | credential |

---

## 4. 向客戶索取的資料清單（標準模板）

每一案新網站請客戶（或從官網整理後向客戶**確認**）提供以下項目。

### 4.1 必備

| # | 項目 | 用途 | 客戶動作 |
|---|------|------|----------|
| 1 | **GSC 完整使用者權限** | 搜尋曝光／點擊／query 資料 | 在 Search Console 新增顧問 Google 帳號為「完整」使用者 |
| 2 | **GSC Property URL** | 與 Site 對齊 | 告知是 `https://…/` 或 `sc-domain:…` |
| 3 | **服務範圍確認** | Business scope | 書面或會議確認：做哪些服務、哪些區域、不做哪些 |
| 4 | **3～6 個月目標** | 策略與 KPI | 例：詢價量、區域曝光、特定服務詞排名 |
| 5 | **主要聯絡人** | 決策與核准 | 姓名、email、電話（不需 ExposureFlow 帳號） |

### 4.2 建議（第二週內）

| # | 項目 | 用途 |
|---|------|------|
| 6 | GA4 property 讀取權 | 流量與轉換分析 |
| 7 | 競爭對手 3～5 家網域 | SERP／機會比較 |
| 8 | 品牌 Logo、主色 | 月報白標（後續） |
| 9 | 過去 SEO／廣告報告 | 面談參考 |

### 4.3 現階段 **不需要** 客戶提供

- ExposureFlow 登入帳號（Client Portal 未上線）  
- 信用卡／Stripe  
- 自行操作後台或 Integrations  
- SERP／OpenAI API key（由平台營運設定）

---

## 5. GSC 授權說明（可轉寄客戶）

以下文字可直接寄給客戶 IT 或站長：

---

**主旨：請協助開啟 Google Search Console 權限（SEO 顧問服務）**

我們需要讀取貴站 **Google Search Console** 的搜尋成效資料（曝光、點擊、查詢詞），以便產出 SEO 分析與月報。

請協助：

1. 登入 [Google Search Console](https://search.google.com/search-console)  
2. 選擇貴站 property（例如：`https://您的網域/`）  
3. **設定 → 使用者與權限 → 新增使用者**  
4. 加入顧問 Email：`_______________`  
5. 權限：**完整**  

完成後請告知 property 的完整 URL（例如 `https://example.com/` 或 `sc-domain:example.com`）。

我們僅用於 SEO 分析，不會修改貴站設定。

---

**Service Account 替代方案**（若客戶不願加個人 Google 帳號）：

1. 顧問／平台提供 Service Account email  
2. 客戶在 GSC 加該 email 為使用者  
3. 顧問透過 API 上傳 SA JSON credential（見 `integration-setup.md`）

---

## 6. 平台營運／工程 checklist（每一案）

| # | 項目 | 負責 |
|---|------|------|
| 1 | 簽約後建立 client workspace | 營運 |
| 2 | 顧問 Clerk 邀請（Step 2 完成後） | 營運 |
| 3 | Linode `.env` 具備 SERP／AI keys（若方案含） | 工程 |
| 4 | GSC OAuth 或 SA credential 就緒 | 工程／顧問 |
| 5 | 首次 sync 成功驗證 | 顧問 |
| 6 | 備份正常（Postgres） | 工程 |

部署見 [`linode-deploy-runbook.md`](./linode-deploy-runbook.md)。

---

## 7. 驗收標準（Case 結案定義）

### 7.1 第一案最小驗收（MVP Delivery）

- [ ] Site 已建且 domain 正確  
- [ ] Strategy + 關鍵字金字塔已填  
- [ ] GSC sync `last_success_at` 有值  
- [ ] Opportunities 至少 1 筆可檢視  
- [ ] 至少 1 個 Decision 已核准或刻意 defer 並有紀錄  
- [ ] 月報 PDF 已交付客戶（線下）

### 7.2 常見阻塞

| 症狀 | 可能原因 | 處理 |
|------|----------|------|
| GSC sync 失敗 | 無 credential、property 不符、權限不足 | 核對 §5；Integrations 錯誤訊息 |
| Dashboard 無資料 | sync 未跑完；GSC 新站資料少 | 等 24～72h；確認 GSC 本身有資料 |
| Opportunities 空 | sync 無 query；business scope 未建 | 完成 Strategy；重跑 sync |
| API 403 | 角色無權；workspace 錯 | 用 owner/admin；確認 URL workspaceId |
| 整合按鈕「待實作」 | OAuth UI 未完成 | Step 3 或 SA + API 上傳 credential |

---

## 8. 時程參考（新案）

| 週 | 顧問 | 客戶 |
|----|------|------|
| W0 | 簽約、建 workspace + site | 簽約 |
| W1 | 面談、Strategy、關鍵字金字塔 | 提供 GSC 權限、確認服務範圍 |
| W1～2 | GSC 連線 + 首次 sync | — |
| W2～3 | Opportunities、Decision、Roadmap | 必要時核准方向（線下） |
| W4 | 第一份月報 PDF | 接收月報 |

---

## 9. 參考案例：ezfix.com.tw（恆惠修理紗窗）

**網站**：[https://ezfix.com.tw/](https://ezfix.com.tw/)  
**類型**：台中本地到府服務（紗窗、鋁門窗、防霾網）

| 欄位 | 建議值 |
|------|--------|
| domain | `ezfix.com.tw` |
| site_name | `恆惠修理紗窗` |
| industry | 本地居家維修 |
| business_model | 到府服務、電話/LINE 詢價 |

**Business scope（從官網整理，需客戶確認）**：

- 服務：紗窗修理訂製、折疊式紗窗、鋁門窗維修、防霾網  
- 區域：台中各區及周邊（太平、大里、豐原等）  
- 轉換：來電、LINE  

**關鍵字方向（示例）**：

- 台中紗窗修理、折疊式紗窗、鋁門窗維修、防霾網安裝  
- 台中{區名} + 服務詞  

**待客戶確認**：GSC property、顧問 Google 帳號授權、優先推廣服務與區域。

---

## 10. 相關文件

| 文件 | 用途 |
|------|------|
| [`gtm-deployment-scope.md`](./gtm-deployment-scope.md) | 商業模式、現階段不做項目 |
| [`linode-deploy-runbook.md`](./linode-deploy-runbook.md) | 正式環境 URL、重部署 |
| [`integration-setup.md`](../help/integration-setup.md) | GSC／GA4 技術設定 |
| [`onboarding-guide.md`](../help/onboarding-guide.md) | 產品內 onboarding 步驟（偏自助參考） |
| [`launch-checklist.md`](./launch-checklist.md) | GA 全量檢查（顧問模式見 GTM scope） |
| [`exposureflow-development-plan.md`](./exposureflow-development-plan.md) §7 | 顧問面談與關鍵字方法論 |

---

## 11. 修訂紀錄

| 日期 | 變更 |
|------|------|
| 2026-06-14 | 初版：顧問-led 標準 SOP；含客戶資料模板、GSC 授權信、ezfix 參考案 |
