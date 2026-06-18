# ExposureFlow AI 維護工程師實作規格

**狀態**：Draft / Ready for Engineering  
**建立日期**：2026-06-18  
**適用範圍**：Production 運維巡檢、故障偵測、停滯偵測、顧問晨報  
**部署目標**：Linode production (`app.kakusinn.com`)  

---

## 1. 產品定位

「AI 維護工程師」不是取代監控系統，也不是自動修復所有問題的 autonomous agent。

本功能定位為：

```text
規則巡檢系統（客觀偵測）
  → 產生結構化 Health Signals
  → AI Maintenance Agent（判讀、歸納、白話摘要）
  → Internal Admin / Email / Slack / 顧問工作台呈現
  → 人工確認與處置
```

### 1.1 第一版目標

1. 每天固定時間檢查 production 是否健康。
2. 偵測 API / Web / Worker / Beat / DB / Redis / Job queue / Integration 是否故障或停滯。
3. 偵測客戶交付流程是否卡住，例如：
   - GSC 長時間未同步
   - job 連續失敗
   - 顧問 inbox urgent 超過門檻未處理
   - 內容 pipeline 卡在同一狀態太久
4. 產出「每日維護晨報」：
   - 今天整體狀態
   - 重大風險
   - 受影響客戶 / site
   - 建議處理順序
   - 哪些是 AI 可自動做，哪些必須人做
5. 僅允許低風險自動處置，例如重新排隊特定 failed job；高風險動作只開建議，不自動執行。

### 1.2 第一版明確不做

| 不做項目 | 原因 |
|----------|------|
| 不讓 LLM 判斷系統有無故障 | 故障判斷必須由規則與 metrics 決定 |
| 不自動改 production 設定或 secrets | 高風險 |
| 不自動改客戶網站、GSC、ContentFlow 設定 | 需人工與客戶脈絡 |
| 不自動核准內容、決策、關鍵字 | 現有政策要求 human approval |
| 不取代外部 uptime monitor | 5 分鐘級別 availability 仍應由外部服務監控 |

---

## 2. 現有系統可重用能力

| 現有能力 | 路徑 | 用途 |
|----------|------|------|
| Public health | `ops/router.py` `/health` | API 基礎健康 |
| Launch readiness | `launch/readiness.py` | 模組、plan、subscription、報表等上線檢查 |
| Integration health | `internal_admin/service.py` | 整合狀態概覽 |
| Celery beat | `jobs/celery_app.py` | 排程每日巡檢 |
| JobRun | `models` / `jobs/service.py` | queue、failed、running、completed 狀態 |
| Consultant inbox | `consultant/service.py` | 顧問業務待辦與停滯 |
| GSC sitemap health | `jobs/handlers/indexability_sitemap_health.py` | sitemap / GSC 健康訊號 |
| Content pipeline | `content/service.py` | 內容狀態與 publish gate |

---

## 3. 系統架構

### 3.1 元件

```text
Celery Beat
  └── ops.daily_health job
        ├── OpsHealthCollector
        │     ├── Infrastructure checks
        │     ├── Job checks
        │     ├── Integration checks
        │     ├── Consultant inbox checks
        │     └── Content pipeline checks
        ├── OpsSignalClassifier
        │     └── PASS / WARN / CRITICAL
        ├── OpsMaintenanceSummarizer
        │     ├── deterministic summary
        │     └── optional LLM white-label summary
        ├── Persistence
        │     ├── ops_health_runs
        │     └── ops_health_signals
        └── Notification
              ├── internal admin
              ├── email / Slack（可選）
              └── consultant inbox bridge（只放客戶交付相關）
```

### 3.2 分層原則

| 層 | 負責 | 是否用 AI |
|----|------|-----------|
| Collector | 查 DB / HTTP / Docker 狀態 | 否 |
| Classifier | 根據門檻判定 PASS/WARN/CRITICAL | 否 |
| Summarizer | 將 signals 整理成白話晨報 | 可選 |
| Remediator | 低風險自動處置 | 第一版保守開放 |
| Human | 高風險決策與實際修復 | 是最終責任人 |

---

## 4. 健康檢查項目

### 4.1 Infrastructure Checks

| Check ID | 狀態 | 判斷規則 | Severity |
|----------|------|----------|----------|
| `infra.api_health` | API health | `/health` 非 200 | CRITICAL |
| `infra.web_health` | Web health | 首頁或 dashboard shell 非 200 | CRITICAL |
| `infra.db_connectivity` | DB | `select 1` 失敗 | CRITICAL |
| `infra.redis_connectivity` | Redis | ping 失敗 | WARN / CRITICAL |
| `infra.disk_space` | Disk | available < 15% | WARN；< 8% CRITICAL |
| `infra.container_status` | Docker | api/web/worker/beat 不在 running | CRITICAL |

第一版如果 API container 無法從 app 內查 Docker，可先略過 `container_status`，改由外部 cron 或 Linode script 補。

### 4.2 Job / Worker Checks

| Check ID | 判斷規則 | Severity |
|----------|----------|----------|
| `jobs.failed_24h` | 24h failed jobs > threshold | WARN / CRITICAL |
| `jobs.queue_stuck` | queued 超過 30 分鐘仍未 started | WARN |
| `jobs.running_stuck` | running 超過 job timeout | CRITICAL |
| `jobs.beat_stale` | 重要排程 job 超過預期時間未產生 | CRITICAL |
| `jobs.worker_idle_suspicious` | 有 queued job 但 15 分鐘沒有 completed job | CRITICAL |

建議 threshold：

| 項目 | WARN | CRITICAL |
|------|------|----------|
| failed jobs / 24h | >= 3 | >= 10 |
| queued age | >= 30m | >= 2h |
| running age | >= 60m | >= 4h |
| beat stale | missed 1 run | missed 2 runs |

### 4.3 Integration Checks

| Check ID | 判斷規則 | Severity |
|----------|----------|----------|
| `integration.gsc_error` | `IntegrationSyncState.last_error` not null | WARN |
| `integration.gsc_stale` | GSC last sync > 48h | WARN |
| `integration.credential_missing` | active site 無 GSC credential | WARN |
| `integration.contentflow_error` | publish 連續失敗 | WARN / CRITICAL |
| `integration.oauth_expired` | OAuth refresh / access error | CRITICAL |

### 4.4 Consultant / Delivery Checks

| Check ID | 判斷規則 | Severity |
|----------|----------|----------|
| `delivery.urgent_inbox_aging` | urgent item > 3 天未移動 | WARN |
| `delivery.urgent_inbox_critical_aging` | critical urgent > 1 天未移動 | CRITICAL |
| `delivery.strategy_backlog_growth` | strategy backlog 7 天成長 > 30% | WARN |
| `delivery.site_no_gsc_data` | active site 7 天無 GSC rows | WARN |
| `delivery.content_review_stale` | content `needs_review` > 7 天 | WARN |
| `delivery.claim_blocked_stale` | `claim_blocked` > 3 天 | WARN |

### 4.5 Content Pipeline Checks

| Check ID | 判斷規則 | Severity |
|----------|----------|----------|
| `content.queued_stale` | generation run queued > 30m | WARN |
| `content.pipeline_failed` | generation failed | WARN |
| `content.publish_failed` | publish job failed | CRITICAL if repeated |
| `content.live_publish_noindex` | published URL reachable=false or noindex=true | CRITICAL |
| `content.topic_gap_rebuild_missing` | live publish success but no topic rebuild job | WARN |

---

## 5. 資料模型

新增 Alembic migration，例如：

```text
022_ops_health_runs.py
```

### 5.1 `ops_health_runs`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | UUID PK | run id |
| `started_at` | timestamptz | 開始時間 |
| `completed_at` | timestamptz nullable | 完成時間 |
| `status` | varchar | `pass` / `warn` / `critical` / `failed` |
| `trigger` | varchar | `scheduled` / `manual` / `deploy_smoke` |
| `summary_title` | text | 晨報標題 |
| `summary_markdown` | text nullable | AI 或 deterministic 摘要 |
| `llm_provider` | varchar nullable | `openai` / `none` |
| `llm_model` | varchar nullable | 例如 `gpt-4o-mini` |
| `metadata_json` | JSONB | thresholds、環境、版本 |

### 5.2 `ops_health_signals`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | UUID PK | signal id |
| `run_id` | UUID FK | 對應 `ops_health_runs.id` |
| `workspace_id` | UUID nullable | 若與 client workspace 有關 |
| `site_id` | UUID nullable | 若與 site 有關 |
| `check_id` | varchar | 如 `jobs.failed_24h` |
| `category` | varchar | `infra` / `jobs` / `integration` / `delivery` / `content` |
| `severity` | varchar | `pass` / `warn` / `critical` |
| `title` | text | 短標題 |
| `message` | text | 具體說明 |
| `evidence_json` | JSONB | 數字、job ids、錯誤摘要 |
| `recommended_action` | text | 工程師 / 顧問要做什麼 |
| `action_type` | varchar nullable | `manual` / `safe_retry` / `open_inbox` |
| `created_at` | timestamptz | 建立時間 |

### 5.3 Retention

- `ops_health_runs` 保留 180 天。
- `ops_health_signals` 保留 180 天。
- 可加每週清理 job：`ops.health.retention_cleanup`。

---

## 6. 後端模組設計

新增 package：

```text
apps/api/exposureflow_api/ops_maintenance/
  __init__.py
  checks.py
  collector.py
  classifier.py
  schemas.py
  service.py
  summarizer.py
  notifications.py
  router.py
```

### 6.1 `checks.py`

定義 check result dataclass：

```python
@dataclass
class OpsCheckResult:
    check_id: str
    category: str
    severity: Literal["pass", "warn", "critical"]
    title: str
    message: str
    recommended_action: str
    workspace_id: UUID | None = None
    site_id: UUID | None = None
    evidence: dict = field(default_factory=dict)
    action_type: str | None = None
```

每個 check 為 async function：

```python
async def check_failed_jobs(db: AsyncSession, window_hours: int = 24) -> list[OpsCheckResult]:
    ...
```

### 6.2 `collector.py`

```python
async def collect_ops_health(db: AsyncSession) -> list[OpsCheckResult]:
    checks = [
        check_db_connectivity,
        check_failed_jobs,
        check_stuck_jobs,
        check_integration_errors,
        check_consultant_inbox_aging,
        check_content_pipeline_stale,
    ]
    ...
```

錯誤處理：

- 單一 check exception 不應中止整個 run。
- 該 check 產生 `critical` signal：`ops.check_failed`。

### 6.3 `service.py`

核心入口：

```python
async def run_daily_ops_health(
    db: AsyncSession,
    *,
    trigger: str = "scheduled",
    use_llm_summary: bool = True,
) -> OpsHealthRun:
    ...
```

流程：

1. 建立 `OpsHealthRun(status="running")`
2. 執行 collector
3. 寫入 signals
4. 根據最高 severity 設定 run status
5. 呼叫 summarizer
6. 發通知
7. commit / flush

### 6.4 `summarizer.py`

第一版必須有 deterministic fallback：

```python
def build_deterministic_summary(signals: list[OpsCheckResult]) -> str:
    ...
```

LLM 僅在以下條件呼叫：

- `OPENAI_API_KEY` 存在
- `use_llm_summary=True`
- 有 `warn` 或 `critical`

LLM prompt 必須要求：

1. 不得捏造未出現在 JSON 的故障。
2. 必須保留 signal severity。
3. 輸出繁體中文。
4. 將建議分成「工程師處理」「顧問處理」「可自動重試」。

範例 prompt：

```text
你是 ExposureFlow 的 AI 維護工程師。以下是規則系統產生的 production health signals。
你只能根據 JSON 內容摘要，不得新增未出現的故障。
請輸出：
1. 今日總結（一句話）
2. Critical
3. Warn
4. 建議處理順序
5. 哪些需要工程師，哪些需要顧問
Signals JSON:
...
```

---

## 7. Celery Job 設計

### 7.1 Registry

在 `jobs/registry.py` 加：

```python
{
    "job_type": "ops.daily_health",
    "display_name": "Daily Ops Health Check",
    "description": "Daily production maintenance engineer check",
    "default_priority": 20,
}
```

### 7.2 Handler

新增：

```text
apps/api/exposureflow_api/jobs/handlers/ops_daily_health.py
```

```python
async def run_ops_daily_health(db: AsyncSession, run: JobRun) -> None:
    try:
        result = await run_daily_ops_health(
            db,
            trigger=str((run.input_json or {}).get("trigger", "scheduled")),
            use_llm_summary=bool((run.input_json or {}).get("use_llm_summary", True)),
        )
        await finalize_job_run(run, success=True, output={"ops_health_run_id": str(result.id)})
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="OPS_DAILY_HEALTH_FAILED",
            error_message=str(exc),
        )
```

### 7.3 Beat Schedule

在 `jobs/celery_app.py`：

```python
"ops-daily-health": {
    "task": "exposureflow_api.jobs.tasks.enqueue_job",
    "schedule": crontab(minute=0, hour=0),  # UTC 00:00 = 台灣 08:00
    "kwargs": {
        "job_type": "ops.daily_health",
        "input_json": {"trigger": "scheduled", "use_llm_summary": True},
        "idempotency_key": "ops-daily-health:{date}",
    },
},
```

若現有 `enqueue_job` task 不支援 date template，第一版可改在 handler 或 service 內用 `datetime.now(UTC).date()` 產生 idempotency key。

---

## 8. API 設計

新增 router：

```text
apps/api/exposureflow_api/ops_maintenance/router.py
```

Prefix：

```text
/api/v1/internal/ops-maintenance
```

### 8.1 查最新晨報

```http
GET /api/v1/internal/ops-maintenance/latest
Permission: ops:read
```

Response：

```json
{
  "run": {
    "id": "...",
    "status": "warn",
    "started_at": "...",
    "completed_at": "...",
    "summary_title": "今日平台大致正常，有 2 項需處理",
    "summary_markdown": "..."
  },
  "signals": [
    {
      "severity": "warn",
      "category": "integration",
      "title": "恆惠 GSC 同步失敗",
      "message": "...",
      "recommended_action": "..."
    }
  ]
}
```

### 8.2 查歷史

```http
GET /api/v1/internal/ops-maintenance/runs?limit=30
Permission: ops:read
```

### 8.3 手動觸發

```http
POST /api/v1/internal/ops-maintenance/run
Permission: ops:read
```

Body：

```json
{
  "use_llm_summary": true
}
```

第一版可直接同步執行；若超過 10 秒，改 enqueue `ops.daily_health`。

---

## 9. 前端 UI

### 9.1 Internal Admin 頁面

新增頁：

```text
apps/web/app/(internal-admin)/internal-admin/ops-maintenance/page.tsx
```

UI 區塊：

1. Overall status card
   - PASS / WARN / CRITICAL
   - last run time
   - next scheduled run
2. AI 維護晨報
   - markdown summary
3. Critical signals
4. Warn signals
5. Recently resolved / pass checks
6. Manual run button

### 9.2 Navigation

在 internal admin nav 加：

```text
維護工程師
```

### 9.3 顧問工作台整合（可選）

只把「客戶交付相關」signals 放入顧問可見區，例如：

- `delivery.urgent_inbox_aging`
- `integration.gsc_error`
- `content.review_stale`

不要把 infra signal（DB / Redis / worker）塞進顧問 inbox；infra 應留在 Internal Admin。

---

## 10. Notification 設計

第一版通知策略：

| Severity | 通知 |
|----------|------|
| PASS | 只寫 DB，不主動通知 |
| WARN | 寄 Email / Slack digest（每日一次） |
| CRITICAL | 立即通知 + 每日 digest |

### 10.1 通知內容

```text
[ExposureFlow Ops] CRITICAL - Worker queue stuck

狀態：CRITICAL
受影響：全平台 / 恆惠修理紗窗
證據：queued jobs 8 筆，最久 2h 14m
建議：先檢查 worker container 是否 running；若 running，查看 celery logs。
連結：https://app.kakusinn.com/internal-admin/ops-maintenance
```

### 10.2 通知管道

第一版優先順序：

1. Internal Admin UI
2. Email（若 SMTP 可用）
3. Slack webhook（可選）

---

## 11. 自動處置政策

### 11.1 允許第一版自動做

| Action | 條件 |
|--------|------|
| retry failed job | job type 在 allowlist、失敗原因非 credential/auth/quota |
| enqueue sitemap health check | site 有 active GSC credential |
| enqueue topic graph rebuild | published URL indexability passed |

Allowlist：

```python
SAFE_RETRY_JOB_TYPES = {
    "topic_graph.rebuild",
    "indexability.sitemap_health",
    "indexability.published_noindex",
}
```

### 11.2 禁止自動做

| Action | 原因 |
|--------|------|
| 修改 integration credential | secret / auth risk |
| 核准 content / decision / keyword | human approval policy |
| 發布內容 | 商業與品牌風險 |
| 改客戶網站設定 | 跨系統高風險 |
| restart Docker container | 第一版不做，避免誤判造成更大中斷 |

---

## 12. 權限與安全

| 操作 | Permission |
|------|------------|
| 查看 ops maintenance | `ops:read` |
| 手動觸發 run | `ops:read` |
| 設定 notification | `ops:read` 或未來 `ops:write` |
| 自動 retry job | 系統內部 job only |

安全要求：

1. API 不回傳 secrets、OAuth token、raw credential。
2. LLM prompt 不包含 secrets。
3. Signal evidence 需過濾敏感 headers / tokens。
4. LLM summary 僅根據 structured signals，不直接查 production DB。
5. 所有 manual trigger 寫 audit log。

---

## 13. 測試計畫

### 13.1 Unit Tests

新增：

```text
apps/api/tests/test_ops_maintenance_checks.py
apps/api/tests/test_ops_maintenance_summarizer.py
apps/api/tests/test_ops_maintenance_permissions.py
```

測試項：

- failed job threshold
- stuck queued job
- running job timeout
- integration last_error
- consultant inbox aging
- deterministic summary 不需 LLM
- LLM unavailable fallback
- evidence 不含 secret 字串

### 13.2 Integration Tests

需要 Postgres：

- 建立多 workspace / site / job rows
- 跑 `run_daily_ops_health`
- 驗證：
  - run status 正確
  - signals 數量正確
  - workspace/site scope 正確
  - `ops:read` 才可查 internal endpoint

### 13.3 E2E / Browser

- Internal Admin 能看到最新晨報
- Manual run button 可觸發
- Critical / Warn 分區顯示
- 無 signals 時顯示 PASS empty state

---

## 14. 部署與驗收

### 14.1 Migration

1. 新增 `022_ops_health_runs.py`
2. 部署前在 staging / local Postgres 跑 migration
3. Production deploy 時確認 alembic current / upgrade head

### 14.2 Production Smoke Test

部署後執行：

```bash
curl -sS https://app.kakusinn.com/health
curl -sS https://app.kakusinn.com/api/v1/launch/readiness
```

手動觸發：

```http
POST /api/v1/internal/ops-maintenance/run
```

驗收：

- `ops_health_runs` 新增一筆
- status 為 pass/warn/critical，不是 failed
- Internal Admin 顯示晨報
- 無敏感資料出現在 summary / signals

### 14.3 Definition of Done

| 項目 | 必須 |
|------|------|
| DB migration | ✅ |
| Daily Celery schedule | ✅ |
| Internal Admin UI | ✅ |
| Deterministic summary fallback | ✅ |
| LLM optional summary | ✅ |
| Permission guard `ops:read` | ✅ |
| Unit tests | ✅ |
| Ruff / pytest / tsc | ✅ |
| Security review | ✅ |
| Production deployment | ✅ |

---

## 15. 實作順序

### Step 1：資料模型與 service

1. 新增 models：`OpsHealthRun`, `OpsHealthSignal`
2. Alembic migration
3. 新增 `ops_maintenance` package
4. 實作 deterministic collector + classifier

### Step 2：Job 與 API

1. 註冊 `ops.daily_health`
2. 新增 handler
3. 加 beat schedule
4. 新增 internal API

### Step 3：UI

1. Internal Admin 頁
2. SDK methods
3. nav link
4. manual run button

### Step 4：LLM Summary

1. 加 optional summarizer
2. fallback 測試
3. secret redaction 測試

### Step 5：Notifications

1. 先只寫 DB
2. 再接 Email / Slack
3. Critical immediate alert

---

## 16. 後續升級方向

### 16.1 AI 維護工程師 v2

- 對 repeated failures 做 root-cause grouping
- 自動比對最近 deploy time 與 failure spike
- 產生「工程師 runbook 建議」
- 針對低風險 job 自動 retry 並記錄結果

### 16.2 AI 維護工程師 v3

- 建立「維護待辦」生命週期：
  - open
  - acknowledged
  - investigating
  - resolved
  - muted
- 支援 mute 某類 known issue
- 支援每個 client workspace 的 SLA / priority

### 16.3 不建議方向

- 不建議讓 LLM 直接 ssh production。
- 不建議讓 LLM 直接改資料庫。
- 不建議讓 LLM 自動核准商業 / 內容 / SEO 決策。

---

## 17. 範例晨報

```markdown
# 今日維護晨報 — WARN

整體平台可用，API / Web health 正常；但有 2 個客戶交付項目需要顧問處理，另有 1 個 job queue 停滯風險。

## Critical

目前沒有 Critical。

## Warn

1. 恆惠修理紗窗 GSC sitemap health 仍有錯誤，已持續 3 天。
   - 建議：到技術問題頁確認 live sitemap 是否仍含錯誤網域；修正後手動觸發 GSC sync。

2. 有 3 筆 content generation job 失敗。
   - 建議：查看 job detail；若錯誤為 transient provider timeout，可重新排隊。

## 今日建議順序

1. 先處理 GSC sitemap，因為會影響索引與後續機會判斷。
2. 再看 failed content jobs，確認是否需要 retry。
3. 最後整理策略待辦，安排本週 brief。

## AI 可協助

- 可協助整理錯誤原因。
- 可協助產生修復 runbook。
- 不會自動改站、不會自動核准、不會自動發布。
```

---

## 18. 工程注意事項

1. 本功能是 internal ops，不應暴露給 client viewer。
2. 嚴格區分 platform infra signals 與 consultant delivery signals。
3. 所有 threshold 先寫常數，後續再做設定表。
4. LLM summary 失敗不得影響 health run 成功。
5. 不要把 raw exception stacktrace 直接送 LLM；先 redaction。
6. Production 第一版以「看得到、可追蹤」為主，不急著自動修復。
