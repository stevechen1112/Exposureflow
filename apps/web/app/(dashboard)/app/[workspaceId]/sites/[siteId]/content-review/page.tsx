"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { useSiteContext } from "@/lib/hooks";
import { useWorkspaceAuth } from "@/lib/auth-context";
import type { ActionCandidate } from "@exposureflow/shared-types";
import {
  formatCandidateLabel,
  isContentGenerationCandidate,
} from "@/lib/candidate-utils";

type GenerationRun = {
  id: string;
  execution_job_id: string;
  content_brief_id: string;
  generation_mode: string;
  review_level: string;
  provider: string | null;
  model: string | null;
  output_markdown: string | null;
  unsupported_claims_json: unknown[];
  status: string;
  created_at: string;
  updated_at: string;
};

/** Status values returned by the content generation API. */
const REVIEWABLE_STATUSES = new Set([
  "needs_review",
  "draft",
  "claim_verified",
  "claim_blocked",
]);

const STATUS_CLASS: Record<string, string> = {
  draft: "",
  needs_review: "badge-high",
  claim_verified: "",
  claim_blocked: "badge-critical",
  needs_changes: "badge-critical",
  approved: "",
  published: "",
  queued: "",
};

const STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  needs_review: "待審核",
  claim_verified: "Claim 通過",
  claim_blocked: "Claim 阻擋",
  needs_changes: "需修改",
  approved: "已核准",
  publish_ready: "可發布",
  published: "已發布",
  queued: "排隊中",
};

function isReviewable(status: string) {
  return REVIEWABLE_STATUSES.has(status);
}

function canPublishDraft(status: string) {
  return status === "approved" || status === "publish_ready";
}

function canPublishLive(status: string) {
  return status === "published";
}

const REVIEW_LEVEL_LABEL: Record<string, string> = {
  editor_review: "編輯審核",
  manager_review: "主管審核",
  auto_publish: "自動發布",
};

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type ActivePanel =
  | { type: "preview"; run: GenerationRun }
  | { type: "changes"; run: GenerationRun }
  | null;

export default function ContentReviewPage() {
  const { siteId, client } = useSiteContext();
  const { can } = useWorkspaceAuth();
  const canReview = can("site:write");
  const canPublish = can("job:write");
  const [runs, setRuns] = useState<GenerationRun[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [panel, setPanel] = useState<ActivePanel>(null);
  const [changesNote, setChangesNote] = useState("");
  // ---- Content generation workflow ----
  const [approvedCandidates, setApprovedCandidates] = useState<ActionCandidate[]>([]);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [workflowStep, setWorkflowStep] = useState<"idle" | "building_source_pack" | "building_brief" | "creating_job" | "creating_run">("idle");
  const [sourcePackId, setSourcePackId] = useState("");
  const [briefId, setBriefId] = useState("");
  const [executionJobId, setExecutionJobId] = useState("");
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [workflowSuccess, setWorkflowSuccess] = useState<string | null>(null);

  const [schedule, setSchedule] = useState<Record<string, unknown> | null>(null);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleSuccess, setScheduleSuccess] = useState<string | null>(null);
  const [batchBusy, setBatchBusy] = useState(false);
  const [batchResult, setBatchResult] = useState<{ triggered: number; skipped: number; message: string } | null>(null);

  const loadSchedule = useCallback(async () => {
    if (!siteId) return;
    setScheduleLoading(true);
    try {
      const s = await client.getContentSchedule(siteId);
      setSchedule(s);
      setScheduleError(null);
    } catch (err) {
      // 404 or network error — no schedule configured yet
      setSchedule(null);
      setScheduleError(null);
    } finally {
      setScheduleLoading(false);
    }
  }, [client, siteId]);

  useEffect(() => { loadSchedule(); }, [loadSchedule]);

  // Auto-dismiss batch result after 8s
  useEffect(() => {
    if (!batchResult) return;
    const t = setTimeout(() => setBatchResult(null), 8000);
    return () => clearTimeout(t);
  }, [batchResult]);

  async function saveSchedule() {
    if (!siteId) return;
    setScheduleError(null);
    setScheduleSuccess(null);
    try {
      const body = {
        enabled: (schedule?.enabled as boolean) ?? false,
        articles_per_week: (schedule?.articles_per_week as number) ?? 2,
        priority_filter: (schedule?.priority_filter as string) ?? "P1",
        schedule_days_json: (schedule?.schedule_days_json as string[]) ?? ["mon", "thu"],
      };
      const result = await client.upsertContentSchedule(siteId, body);
      setSchedule(result);
      setScheduleSuccess("排程設定已儲存");
    } catch (err) {
      setScheduleError(err instanceof Error ? err.message : "儲存失敗");
    }
  }

  async function runBatchGenerate() {
    if (!siteId) return;
    setBatchBusy(true);
    setBatchResult(null);
    setError(null);
    try {
      const result = await client.batchGenerateContent({
        site_id: siteId,
        count: (schedule?.articles_per_week as number) ?? 2,
        priority_filter: (schedule?.priority_filter as string) ?? "P1",
      });
      setBatchResult(result);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "批次生成失敗");
    } finally {
      setBatchBusy(false);
    }
  }

  const DAY_OPTIONS = [
    { value: "mon", label: "週一" },
    { value: "tue", label: "週二" },
    { value: "wed", label: "週三" },
    { value: "thu", label: "週四" },
    { value: "fri", label: "週五" },
  ];

  const toggleDay = (day: string) => {
    if (!schedule) return;
    const days = (schedule.schedule_days_json as string[]) ?? ["mon", "thu"];
    const next = days.includes(day) ? days.filter(d => d !== day) : [...days, day];
    setSchedule({ ...schedule, schedule_days_json: next });
  };
  const [pipelineBusy, setPipelineBusy] = useState<string | null>(null);
  const [pipelineResult, setPipelineResult] = useState<{
    run_id: string;
    pipeline_status: string;
    seo_score: number;
    agent_decisions: Array<Record<string, unknown>>;
  } | null>(null);

  const loadApprovedCandidates = useCallback(async () => {
    if (!siteId) return;
    try {
      const rows = await client.listCandidates(siteId, "approved");
      const contentEligible = rows.filter(isContentGenerationCandidate);
      const seen = new Set<string>();
      const deduped: ActionCandidate[] = [];
      for (const r of contentEligible) {
        if (!seen.has(r.id)) {
          seen.add(r.id);
          deduped.push(r);
        }
      }
      setApprovedCandidates(deduped);
      setCandidatesError(null);
    } catch (err) {
      setCandidatesError(err instanceof Error ? err.message : "載入候選項目失敗");
    }
  }, [client, siteId]);

  useEffect(() => { loadApprovedCandidates(); }, [loadApprovedCandidates]);

  async function runWorkflow() {
    if (!selectedCandidateId) { setWorkflowError("請先選擇已核准的候選項目"); return; }
    const candidate = approvedCandidates.find(c => c.id === selectedCandidateId);
    if (!candidate) { setWorkflowError("找不到該候選項目"); return; }
    setWorkflowError(null);
    setWorkflowSuccess(null);

    try {
      // Step 1: Build Source Pack
      setWorkflowStep("building_source_pack");
      const sp = await client.buildSourcePack({
        site_id: siteId,
        opportunity_id: candidate.opportunity_id,
        market: "tw",
        language: "zh-TW",
      });
      setSourcePackId(sp.id as string);

      // Step 2: Build Content Brief
      setWorkflowStep("building_brief");
      const brief = await client.buildContentBrief({
        site_id: siteId,
        opportunity_id: candidate.opportunity_id,
        source_pack_id: sp.id as string,
      });
      setBriefId(brief.id as string);

      // Step 3: Create Execution Job
      setWorkflowStep("creating_job");
      const job = await client.createExecutionJob({
        site_id: siteId,
        job_type: "content_generation",
        opportunity_id: candidate.opportunity_id,
      });
      setExecutionJobId(job.id as string);

      // Step 4: Create Generation Run
      setWorkflowStep("creating_run");
      await client.createGenerationRun({
        site_id: siteId,
        execution_job_id: job.id as string,
        content_brief_id: brief.id as string,
        generation_mode: "grounded_llm",
        review_level: "editor_review",
        auto_compile: false,
      });

      setWorkflowSuccess("內容生成已觸發！請稍候片刻後重新整理查看結果");
      setWorkflowStep("idle");
      setSelectedCandidateId("");
      setSourcePackId("");
      setBriefId("");
      setExecutionJobId("");
      await load();
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : "工作流失敗");
      setWorkflowStep("idle");
    }
  }

  const load = useCallback(async () => {
    if (!siteId) {
      setRuns([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const rows = await client.listGenerationRuns(siteId);
      setRuns(rows as unknown as GenerationRun[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }, [client, siteId]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered =
    statusFilter === "all" ? runs : runs.filter((r) => r.status === statusFilter);

  async function approve(runId: string) {
    setBusy(runId);
    setSuccess(null);
    try {
      await client.approveGenerationRun(runId);
      setSuccess("已核准該版本");
      setPanel(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "核准失敗");
    } finally {
      setBusy(null);
    }
  }

  async function requestChanges(runId: string) {
    if (!changesNote.trim()) {
      setError("請填寫修改說明");
      return;
    }
    setBusy(runId);
    setSuccess(null);
    try {
      await client.requestChangesGenerationRun(runId, changesNote);
      setSuccess("已送出修改要求");
      setChangesNote("");
      setPanel(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setBusy(null);
    }
  }

  async function runPipeline(runId: string) {
    setPipelineBusy(runId);
    setPipelineResult(null);
    setError(null);
    try {
      const result = await client.runGenerationPipeline(runId);
      setPipelineResult(result as typeof pipelineResult);
      setSuccess("Pipeline 執行完成！");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pipeline 執行失敗");
    } finally {
      setPipelineBusy(null);
    }
  }

  async function publishToSite(runId: string, siteStatus: "draft" | "published") {
    setBusy(runId);
    setSuccess(null);
    try {
      const result = await client.publishGenerationRun(runId, { site_status: siteStatus });
      const slug = typeof result.slug === "string" ? result.slug : "";
      const postUrl = typeof result.post_url === "string" ? result.post_url : "";
      const indexability = result.indexability_verify as
        | { ok?: boolean; has_noindex?: boolean; url_reachable?: boolean }
        | undefined;
      let indexNote = "";
      if (siteStatus === "published" && indexability) {
        if (indexability.ok) {
          indexNote = "；已上線，待 Google 自然收錄";
        } else if (indexability.has_noindex) {
          indexNote = "；警告：頁面含 noindex";
        } else if (indexability.url_reachable === false) {
          indexNote = "；警告：上線 URL 無法開啟";
        } else {
          indexNote = "；索引可發現性警告，請至技術問題檢視";
        }
      }
      setSuccess(
        siteStatus === "published"
          ? `已正式上線恆惠站${postUrl ? `：${postUrl}` : slug ? `（${slug}）` : ""}${indexNote}`
          : `已推送草稿至恆惠站${postUrl ? `：${postUrl}` : slug ? `（${slug}）` : ""}`,
      );
      setPanel(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "發布至恆惠站失敗");
    } finally {
      setBusy(null);
    }
  }

  function seoScoreBadge(score: number) {
    const color = score >= 85 ? "#15803d" : score >= 60 ? "#c2410c" : "#b91c1c";
    const bg = score >= 85 ? "rgba(22,163,74,0.12)" : score >= 60 ? "rgba(234,88,12,0.12)" : "rgba(220,38,38,0.1)";
    return (
      <span style={{
        display: "inline-block", padding: "0.15rem 0.5rem", borderRadius: 999,
        fontSize: "0.85rem", fontWeight: 700, background: bg, color,
      }}>
        {score}/100
      </span>
    );
  }

  const statusOptions = [
    "all",
    "needs_review",
    "needs_changes",
    "claim_verified",
    "claim_blocked",
    "approved",
    "publish_ready",
    "draft",
    "published",
  ];

  const statusCount = (s: string) => runs.filter((r) => r.status === s).length;
  const pendingCount = statusCount("needs_review");
  const changesCount = statusCount("needs_changes");

  return (
    <>
      <PageHeader
        title="內容審核"
        subtitle={
          canReview
            ? "Generation runs 的 claim 核驗、人工審核與發布 Gate"
            : "檢視 generation runs（您的角色無法核准或退件）"
        }
      />

      {/* Summary bar */}
      <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="card" style={{ borderColor: pendingCount > 0 ? "var(--warning)" : "var(--border)" }}>
          <div className="kpi-label">待審核</div>
          <div className="kpi-value" style={{ color: pendingCount > 0 ? "var(--warning)" : undefined }}>
            {pendingCount}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>需人工審核</div>
        </div>
        <div className="card" style={{ borderColor: changesCount > 0 ? "var(--danger)" : "var(--border)" }}>
          <div className="kpi-label">需修改</div>
          <div className="kpi-value" style={{ color: changesCount > 0 ? "var(--danger)" : undefined }}>
            {changesCount}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>退件修改中</div>
        </div>
        <div className="card">
          <div className="kpi-label">已核准</div>
          <div className="kpi-value">{statusCount("approved")}</div>
        </div>
        <div className="card">
          <div className="kpi-label">已發布</div>
          <div className="kpi-value">{statusCount("published")}</div>
        </div>
      </div>

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? (
        <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p>
      ) : null}

      {/* Content generation workflow */}
      {canReview && (
        <>
          {/* Workflow step indicator */}
          <div className="workflow-steps">
            {[
              { step: 1, label: "選擇機會", active: workflowStep === "idle", done: sourcePackId !== "" },
              { step: 2, label: "Source Pack", active: workflowStep === "building_source_pack", done: sourcePackId !== "" && briefId !== "" },
              { step: 3, label: "Content Brief", active: workflowStep === "building_brief", done: briefId !== "" && executionJobId !== "" },
              { step: 4, label: "觸發生成", active: workflowStep === "creating_job" || workflowStep === "creating_run", done: workflowSuccess !== null },
            ].map(s => (
              <div key={s.step} className={`workflow-step${s.active ? " active" : ""}${s.done && !s.active ? " done" : ""}`}>
                {s.label}
              </div>
            ))}
          </div>

          <div className="card card-primary" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>內容生成工作區</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 0 }}>
            從已核准的候選項目建立 Source Pack → Content Brief → Execution Job → 觸發 AI 生成
          </p>
          {workflowError ? <p style={{ color: "var(--danger)", fontSize: "0.85rem" }}>{workflowError}</p> : null}
          {workflowSuccess ? <p style={{ color: "var(--success)", fontSize: "0.85rem" }}>{workflowSuccess}</p> : null}
          {candidatesError ? <p style={{ color: "var(--warning)", fontSize: "0.85rem" }}>{candidatesError}</p> : null}
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                已核准候選項目
              </label>
              <select
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                style={{ width: "100%" }}
                disabled={workflowStep !== "idle"}
              >
                <option value="">— 選擇候選項目 —</option>
                {approvedCandidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {formatCandidateLabel(c)}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              disabled={!selectedCandidateId || workflowStep !== "idle"}
              onClick={runWorkflow}
            >
              {workflowStep === "idle"
                ? "建立 Source Pack → 觸發生成"
                : workflowStep === "building_source_pack"
                  ? "建立 Source Pack…"
                  : workflowStep === "building_brief"
                    ? "建立 Content Brief…"
                    : workflowStep === "creating_job"
                      ? "建立 Execution Job…"
                      : "觸發 Generation Run…"}
            </button>
            <button type="button" className="btn" onClick={loadApprovedCandidates} disabled={workflowStep !== "idle"}>
              刷新候選
            </button>
          </div>
          {sourcePackId && (
            <div style={{ marginTop: "0.75rem", fontSize: "0.8rem", color: "var(--muted)" }}>
              Source Pack: <code>{sourcePackId}</code>
              {briefId && <> → Brief: <code>{briefId}</code></>}
              {executionJobId && <> → Job: <code>{executionJobId}</code></>}
            </div>
          )}
        </div>
        </>
      )}

      {/* ---- Content Schedule & Batch Generation ---- */}
      {canReview && (
        <div className="card card-secondary" style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "1rem", margin: 0 }}>📅 內容排程與批次生成</h2>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={batchBusy}
                onClick={runBatchGenerate}
              >
                {batchBusy ? "批次生成中…" : `⚡ 批次生成 ${schedule?.articles_per_week ?? 2} 篇`}
              </button>
              <button type="button" className="btn" onClick={loadSchedule} disabled={scheduleLoading}>
                刷新
              </button>
            </div>
          </div>

          {batchResult && (
            <div style={{
              marginTop: "0.75rem", padding: "0.5rem 0.75rem",
              background: "rgba(22,163,74,0.1)", borderRadius: 8,
              fontSize: "0.85rem", color: "var(--success)",
            }}>
              {batchResult.message}（觸發 {batchResult.triggered}，跳過 {batchResult.skipped}）
            </div>
          )}

          {scheduleError && <p style={{ color: "var(--danger)", fontSize: "0.85rem", marginTop: "0.5rem" }}>{scheduleError}</p>}
          {scheduleSuccess && <p style={{ color: "var(--success)", fontSize: "0.85rem", marginTop: "0.5rem" }}>{scheduleSuccess}</p>}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem", marginTop: "1rem" }}>
            {/* Enable toggle */}
            <div>
              <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.9rem" }}>
                <input
                  type="checkbox"
                  checked={(schedule?.enabled as boolean) ?? false}
                  onChange={(e) => setSchedule(schedule ? { ...schedule, enabled: e.target.checked } : { enabled: e.target.checked })}
                />
                啟用自動排程
              </label>
              <p style={{ fontSize: "0.75rem", color: "var(--muted)", margin: "0.25rem 0 0" }}>
                每週一/四自動從已核准候選觸發生成
              </p>
            </div>

            {/* Articles per week */}
            <div>
              <label style={{ fontSize: "0.85rem", color: "var(--muted)", display: "block", marginBottom: "0.25rem" }}>
                每週篇數
              </label>
              <select
                value={(schedule?.articles_per_week as number) ?? 2}
                onChange={(e) => setSchedule(schedule ? { ...schedule, articles_per_week: Number(e.target.value) } : { articles_per_week: Number(e.target.value) })}
                style={{ width: "100%" }}
              >
                {[1, 2, 3, 4, 5, 7, 10].map(n => (
                  <option key={n} value={n}>{n} 篇/週</option>
                ))}
              </select>
            </div>

            {/* Priority filter */}
            <div>
              <label style={{ fontSize: "0.85rem", color: "var(--muted)", display: "block", marginBottom: "0.25rem" }}>
                優先級篩選
              </label>
              <select
                value={(schedule?.priority_filter as string) ?? "P1"}
                onChange={(e) => setSchedule(schedule ? { ...schedule, priority_filter: e.target.value } : { priority_filter: e.target.value })}
                style={{ width: "100%" }}
              >
                <option value="P0">P0 — 緊急</option>
                <option value="P1">P1 — 高優先</option>
                <option value="P2">P2 — 中優先</option>
                <option value="P3">P3 — 低優先</option>
              </select>
            </div>

            {/* Schedule days */}
            <div>
              <label style={{ fontSize: "0.85rem", color: "var(--muted)", display: "block", marginBottom: "0.25rem" }}>
                執行日
              </label>
              <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                {DAY_OPTIONS.map(d => {
                  const days = (schedule?.schedule_days_json as string[]) ?? ["mon", "thu"];
                  const active = days.includes(d.value);
                  return (
                    <button
                      key={d.value}
                      type="button"
                      className={`btn ${active ? "btn-primary" : ""}`}
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
                      onClick={() => toggleDay(d.value)}
                    >
                      {d.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
            <button type="button" className="btn btn-primary" onClick={saveSchedule}>
              儲存排程設定
            </button>
            {typeof schedule?.last_run_at === "string" ? (
              <span style={{ fontSize: "0.8rem", color: "var(--muted)", alignSelf: "center" }}>
                上次執行：{fmtTime(schedule.last_run_at)}
              </span>
            ) : null}
          </div>
        </div>
      )}

      {/* Filter & refresh */}
      <div className="form-row" style={{ marginBottom: "1rem" }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">全部狀態</option>
          {statusOptions.slice(1).map((s) => (
            <option key={s} value={s}>
              {STATUS_LABEL[s] ?? s}
            </option>
          ))}
        </select>
        <button type="button" className="btn" disabled={loading} onClick={load}>
          重新整理
        </button>
      </div>

      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>狀態</th>
              <th>生成模式</th>
              <th>審核層級</th>
              <th>Claim 問題</th>
              <th>模型</th>
              <th>更新時間</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)" }}>
                  載入中…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)" }}>
                  此狀態下沒有 generation run
                </td>
              </tr>
            ) : (
              filtered.map((run) => (
                <tr key={run.id}>
                  <td>
                    <span className={`badge ${STATUS_CLASS[run.status] ?? ""}`}>
                      {STATUS_LABEL[run.status] ?? run.status}
                    </span>
                  </td>
                  <td>
                    <code style={{ fontSize: "0.78rem" }}>{run.generation_mode}</code>
                  </td>
                  <td>
                    {REVIEW_LEVEL_LABEL[run.review_level] ?? run.review_level}
                  </td>
                  <td>
                    {run.unsupported_claims_json.length > 0 ? (
                      <span style={{ color: "var(--danger)", fontWeight: 600 }}>
                        {run.unsupported_claims_json.length} 項待處理
                      </span>
                    ) : (
                      <span style={{ color: "var(--success)" }}>通過</span>
                    )}
                  </td>
                  <td style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                    {run.provider ? `${run.provider} / ${run.model ?? ""}` : "—"}
                  </td>
                  <td style={{ fontSize: "0.82rem", color: "var(--muted)", whiteSpace: "nowrap" }}>
                    {fmtTime(run.updated_at)}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        className="btn"
                        style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                        onClick={() =>
                          setPanel(panel?.type === "preview" && panel.run.id === run.id ? null : { type: "preview", run })
                        }
                      >
                        {panel?.type === "preview" && panel.run.id === run.id ? "收起" : "預覽"}
                      </button>
                      {run.status === "draft" && canReview && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem", background: "#7c3aed" }}
                          disabled={pipelineBusy === run.id}
                          onClick={() => runPipeline(run.id)}
                        >
                          {pipelineBusy === run.id ? "執行中…" : "🔬 Pipeline"}
                        </button>
                      )}
                      {canPublishDraft(run.status) && canPublish && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem", background: "#0f766e" }}
                          disabled={busy === run.id}
                          onClick={() => publishToSite(run.id, "draft")}
                        >
                          {busy === run.id ? "發布中…" : "發布至恆惠站（草稿）"}
                        </button>
                      )}
                      {canPublishLive(run.status) && canPublish && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem", background: "#b45309" }}
                          disabled={busy === run.id}
                          onClick={() => publishToSite(run.id, "published")}
                        >
                          {busy === run.id ? "上線中…" : "正式上線恆惠站"}
                        </button>
                      )}
                      {isReviewable(run.status) && canReview && (
                        <>
                          <button
                            type="button"
                            className="btn btn-primary"
                            style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                            disabled={busy === run.id}
                            onClick={() => approve(run.id)}
                          >
                            核准
                          </button>
                          <button
                            type="button"
                            className="btn"
                            style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                            onClick={() =>
                              setPanel(
                                panel?.type === "changes" && panel.run.id === run.id
                                  ? null
                                  : { type: "changes", run },
                              )
                            }
                          >
                            退件
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Inline preview panel */}
      {panel?.type === "preview" && (
        <div
          className="card"
          style={{ marginTop: "1.5rem", position: "relative" }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0, fontSize: "1rem" }}>
              內容預覽 —{" "}
              <span className={`badge ${STATUS_CLASS[panel.run.status] ?? ""}`}>
                {STATUS_LABEL[panel.run.status]}
              </span>
            </h2>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              {canPublishDraft(panel.run.status) && canPublish && (
                <button
                  type="button"
                  className="btn"
                  style={{ background: "#0f766e", color: "#fff" }}
                  disabled={busy === panel.run.id}
                  onClick={() => publishToSite(panel.run.id, "draft")}
                >
                  發布至恆惠站（草稿）
                </button>
              )}
              {canPublishLive(panel.run.status) && canPublish && (
                <button
                  type="button"
                  className="btn"
                  style={{ background: "#b45309", color: "#fff" }}
                  disabled={busy === panel.run.id}
                  onClick={() => publishToSite(panel.run.id, "published")}
                >
                  正式上線恆惠站
                </button>
              )}
              {isReviewable(panel.run.status) && canReview && (
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={busy === panel.run.id}
                  onClick={() => approve(panel.run.id)}
                >
                  核准此版本
                </button>
              )}
              <button
                type="button"
                className="btn"
                onClick={() => setPanel(null)}
              >
                關閉
              </button>
            </div>
          </div>
          {panel.run.output_markdown ? (
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontFamily: "var(--font)",
                lineHeight: 1.6,
                color: "var(--text)",
                maxHeight: 480,
                overflowY: "auto",
                fontSize: "0.9rem",
              }}
            >
              {panel.run.output_markdown}
            </pre>
          ) : (
            <p style={{ color: "var(--muted)" }}>此 run 尚無編譯好的內容（status: {panel.run.status}）</p>
          )}
          {panel.run.unsupported_claims_json.length > 0 && (
            <div
              style={{
                marginTop: "1rem",
                background: "rgba(239,68,68,0.1)",
                border: "1px solid var(--danger)",
                borderRadius: 8,
                padding: "0.75rem 1rem",
              }}
            >
              <strong style={{ color: "var(--danger)" }}>
                待處理 Claim 問題（{panel.run.unsupported_claims_json.length} 項）
              </strong>
              <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.25rem", fontSize: "0.85rem" }}>
                {(panel.run.unsupported_claims_json as Array<Record<string, unknown>>).map(
                  (c, i) => (
                    <li key={i}>
                      {String(c.claim_text ?? c.text ?? JSON.stringify(c))}
                    </li>
                  ),
                )}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Pipeline result panel */}
      {pipelineResult && (
        <div className="card" style={{ marginTop: "1.5rem", border: "1px solid rgba(124, 58, 237, 0.4)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <h2 style={{ fontSize: "1rem", margin: 0 }}>
              🔬 Pipeline 結果 — {seoScoreBadge(pipelineResult.seo_score)}
            </h2>
            <button type="button" className="btn btn-ghost" onClick={() => setPipelineResult(null)}>收起</button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "0.5rem", marginBottom: "1rem" }}>
            {[
              { label: "Pipeline 狀態", value: pipelineResult.pipeline_status },
              { label: "SEO 分數", value: `${pipelineResult.seo_score}/100` },
              { label: "Agent 決策數", value: pipelineResult.agent_decisions.length },
            ].map(item => (
              <div key={item.label} style={{ padding: "0.5rem", borderRadius: 8, background: "var(--surface-1)", border: "1px solid var(--border)", textAlign: "center" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{item.label}</div>
                <div style={{ fontSize: "1rem", fontWeight: 600 }}>{item.value}</div>
              </div>
            ))}
          </div>
          {pipelineResult.agent_decisions.length > 0 && (
            <details>
              <summary style={{ cursor: "pointer", fontSize: "0.85rem", color: "var(--muted)" }}>
                Agent 決策記錄（{pipelineResult.agent_decisions.length} 步）
              </summary>
              <div className="table-wrap" style={{ marginTop: "0.5rem", maxHeight: 300, overflowY: "auto" }}>
                <table style={{ fontSize: "0.8rem" }}>
                  <thead>
                    <tr><th>Agent</th><th>決策</th><th>原因</th><th>時間</th></tr>
                  </thead>
                  <tbody>
                    {pipelineResult.agent_decisions.map((d, i) => (
                      <tr key={i}>
                        <td><code>{String(d.agent ?? "")}</code></td>
                        <td>{String(d.decision ?? "")}</td>
                        <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis" }}>{String(d.reason ?? "")}</td>
                        <td style={{ whiteSpace: "nowrap" }}>{String(d.timestamp ?? "").slice(11, 19)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </div>
      )}
    </>
  );
}
