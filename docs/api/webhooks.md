# Webhooks

## Stripe Billing

```http
POST /api/v1/webhooks/stripe
Stripe-Signature: <signature>
```

### 處理事件

| Event | 行為 |
|-------|------|
| `checkout.session.completed` | 建立/更新 subscription |
| `customer.subscription.updated` | 同步方案與狀態 |
| `customer.subscription.deleted` | 標記 canceled |
| `invoice.payment_failed` | 更新 billing_status |

### 設定

1. Stripe Dashboard → Webhooks → Add endpoint
2. URL: `https://api.exposureflow.com/api/v1/webhooks/stripe`
3. 設定 `STRIPE_WEBHOOK_SECRET` 環境變數

### 驗證

Webhook handler 使用 `stripe.Webhook.construct_event` 驗證簽章。無效簽章回 400。

## Clerk（Production Auth）

```http
POST /api/v1/auth/clerk/webhook
```

（Phase 11+ 整合；同步 user create/update/delete）

### 建議事件

- `user.created`
- `user.updated`
- `user.deleted`

## 重試

- Stripe 自動重試 failed webhooks
- 實作 idempotent 處理（subscription id、stripe event id）

## 測試

Local 使用 Stripe CLI：

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```
