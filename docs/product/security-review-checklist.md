# Security Review Checklist（EF-H008）

Phase 12–14 安全驗收檢查表。High/Critical 必須修復後才可標記 launch ready。

## Authentication & Authorization

- [ ] Production 禁用 `/api/v1/auth/dev-token`
- [ ] JWT secret 非預設值（production）
- [ ] RBAC 拒絕案例有整合測試
- [ ] `support_admin` 僅由平台 provisioning 授予
- [ ] Impersonation token 含 `impersonated_by` claim 且 TTL ≤ 60 分鐘
- [ ] 2FA step-up 於 `require_2fa` workspace 強制執行

## Multi-Tenant Isolation

- [ ] 所有 workspace-scoped API 驗證 `X-Workspace-Id`
- [ ] 跨 workspace 存取回 403（整合測試）
- [ ] Integration credentials 加密儲存
- [ ] Knowledge / embeddings 不可跨租戶檢索

## Data Protection

- [ ] GDPR data export 可用
- [ ] Audit log 覆蓋敏感操作（impersonation、feature flags、security settings）
- [ ] Sync error 經 `sanitize_sync_error` 過濾
- [ ] Internal admin 不暴露 credential plaintext

## Billing & Abuse

- [ ] Quota enforcement 於 job enqueue 前
- [ ] Stripe webhook signature 驗證
- [ ] Rate limiting / backpressure 已啟用

## Operations

- [ ] Backup 每日執行且 verify script PASS
- [ ] Restore drill 於 staging 完成
- [ ] Status incident 預設 `is_public=false`
- [ ] Platform support bootstrap 不在 production 執行

## Review Record

| Date | Reviewer | Result | Notes |
|------|----------|--------|-------|
| | | | |
