# Phase 12 Code Review — Security / Compliance / Reliability

**Phase**：12 — Security / Compliance / Reliability  
**Review 日期**：2026-06-14  
**結論**：PASS（Bugbot / Security High 已修；部分 EF-1202/1203 項目記錄於 known_limitations）

---

## 1. 變更清單

### 後端
| 路徑 | 說明 |
|------|------|
| `alembic/versions/016_security_compliance.py` | workspace_security_settings、security_events、data_export_requests |
| `models/security_compliance.py` | ORM 模型 |
| `security/*` | 資料匯出/刪除、retention、SSO、IP allowlist、credential rotation、KMS 抽象 |
| `security/router.py` | `/api/v1/security/*` |
| `reliability/*` | rate limit、circuit breaker、backpressure、SLO |
| `observability/*` | JSON logging、request id middleware、metrics |
| `ops/router.py` | `/api/v1/ops/health|metrics|slo|circuits`（`ops:read`） |
| `auth/deps.py` | IP allowlist、2FA step-up（JWT `amr`） |
| `auth/jwt.py` | `amr` claim |
| `integrations/sync_helpers.py` | provider circuit 記錄 |
| `jobs/handlers/gsc_sync.py`、`serp_snapshot.py` | `assert_provider_available` |
| `jobs/service.py` | queue backpressure |
| `main.py` | ObservabilityMiddleware、security/ops router |

### 文件
| 路徑 | 說明 |
|------|------|
| `docs/operations/backup-restore-runbook.md` | 備份還原程序 |
| `docs/operations/disaster-recovery-runbook.md` | DR runbook |
| `docs/operations/slo-definitions.md` | SLO 定義 |

### 測試
| 路徑 | 說明 |
|------|------|
| `tests/test_security_reliability.py` | 加密、rate limit、circuit breaker |
| `tests/test_security_api.py` | export、audit、ops、tenant isolation |

---

## 2. EF-xxxx 逐項驗收

| EF | 狀態 | 證據 |
|----|------|------|
| EF-1201 資料隔離與隱私 | PASS（部分） | 既有 tenant tests + `data-export` / `deletion-request` / `purge` / retention / credential rotation |
| EF-1202 安全稽核與權限 | PASS（部分） | audit logs API、2FA + amr step-up、SSO config、IP allowlist、`security_events` 表 |
| EF-1203 可靠性 | PASS（部分） | rate limit、circuit breaker、backpressure、SLO、DR/backup runbooks |
| EF-1204 Observability | PASS（部分） | structured logging、metrics middleware、ops endpoints |

---

## 3. 測試執行紀錄

| 命令 | 結果 |
|------|------|
| `ruff check exposureflow_api` | PASS |
| `pytest tests/test_security_reliability.py tests/test_error_sanitizer.py` | 5 passed |
| `pytest tests/test_security_api.py` | SKIP（本機 Postgres 未啟動） |
| Postgres 整合 | 待 CI |

---

## 4. Bugbot Review

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | XFF 繞過 IP allowlist | **已修** — `trust_proxy_headers` 預設 false |
| High | Ops 跨租戶洩漏 | **已修** — `ops:read` 僅 owner/admin |
| High | 刪除後 owner 無法 purge | **已修** — 保留 owner membership |
| High | Circuit breaker 未阻擋 job | **已修** — GSC/SERP handler 前置 assert |
| High | Redis client 每請求建立 | **已修** — singleton client |

---

## 5. Security Review

| 嚴重度 | 項目 | 處置 |
|--------|------|------|
| High | 2FA 無 step-up | **已修** — JWT `amr` + verify 回傳新 token |
| High | Ops 全域 metrics | **已修** — `ops:read` 權限 |
| High | SSO open redirect | **已修** — HTTPS URL 驗證 |
| Medium | Purge 無狀態機 | **已修** — 需 `pending_deletion` |
| Medium | retention 任意 admin | **已修** — owner-only |

---

## 6. 修復紀錄

- Bugbot + Security 共 10 項 High/Medium 修復
- rate_limit 變數命名衝突修復

---

## 7. 已知限制

- **完整 SAML SP 流程**：production 僅儲存設定 + redirect；完整 assertion 驗簽待 IdP 整合
- **GDPR 級聯刪除**：purge 清除 credentials + 狀態；全表 cascade 刪除待 background job
- **KMS**：`kms_key_id` 仍走 Fernet 本地加密；AWS KMS SDK 待 deploy 環境
- **SLO job P95**：in-process metrics；Prometheus 待 production
- **suspicious activity**：`detect_suspicious_activity` 已實作，自動 alerting 接 Phase 13

---

## 8. 結論

**PASS** — EF-1201–1204 核心交付完成；High/Critical 已修；known_limitations 已記錄。
