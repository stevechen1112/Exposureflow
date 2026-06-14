# Integration Setup Guide

## Google Search Console (GSC)

### OAuth（推薦）

1. Settings → Integrations → Add GSC
2. 選擇 OAuth，完成 Google 授權
3. 指定 Search Console property URL
4. 觸發 **Sync GSC**

### Service Account

1. 於 Google Cloud 建立 service account 並下載 JSON key
2. 在 Search Console 將 service account email 加為使用者
3. 於 ExposureFlow 上傳 encrypted credential

### 疑難排解

| 症狀 | 處理 |
|------|------|
| Sync 失敗 | 檢查 credential 是否過期；查看 Notifications |
| 無資料 | 確認 property URL 與 site 網域一致 |
| 403 | 確認 RBAC 具 integration:write |

## Google Analytics 4 (GA4)

1. 建立 GA4 service account credential
2. 授予 property 讀取權限
3. 觸發 GA4 sync job

## SERP Providers

設定環境變數：

- `SERPER_API_KEY` 或 `SERPAPI_API_KEY`

於 Serp Matrix 頁面觸發 snapshot。

## Bing Webmaster

1. 取得 Bing API key
2. 新增 Bing integration credential
3. 觸發 Bing sync

## Tech SEO Crawl

Settings → Integrations → **Tech SEO Crawl**

## Webhook 與 API

詳見 [API Documentation](../api/README.md) 與 [Webhooks](../api/webhooks.md)。
