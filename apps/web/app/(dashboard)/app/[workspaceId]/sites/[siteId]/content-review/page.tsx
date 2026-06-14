"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { useSiteContext } from "@/lib/hooks";
import { useWorkspaceAuth } from "@/lib/auth-context";

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
  published: "已發布",
  queued: "排隊中",
};

function isReviewable(status: string) {
  return REVIEWABLE_STATUSES.has(status);
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
  const [runs, setRuns] = useState<GenerationRun[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [panel, setPanel] = useState<ActivePanel>(null);
  const [changesNote, setChangesNote] = useState("");

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

  const statusOptions = [
    "all",
    "needs_review",
    "needs_changes",
    "claim_verified",
    "claim_blocked",
    "approved",
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

      {/* Inline request-changes panel */}
      {panel?.type === "changes" && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2 style={{ margin: "0 0 1rem", fontSize: "1rem" }}>
            退件修改 — {fmtTime(panel.run.created_at)}
          </h2>
          <label
            style={{ display: "block", color: "var(--muted)", fontSize: "0.85rem", marginBottom: "0.5rem" }}
          >
            修改說明（必填）
          </label>
          <textarea
            value={changesNote}
            onChange={(e) => setChangesNote(e.target.value)}
            rows={4}
            style={{ width: "100%", resize: "vertical" }}
            placeholder="請說明需要修改的內容或原因…"
          />
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy === panel.run.id || !changesNote.trim()}
              onClick={() => requestChanges(panel.run.id)}
            >
              送出退件
            </button>
            <button type="button" className="btn" onClick={() => setPanel(null)}>
              取消
            </button>
          </div>
        </div>
      )}
    </>
  );
}
