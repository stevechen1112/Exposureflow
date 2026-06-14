"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import type { AiVisibilityDashboard } from "@exposureflow/shared-types";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type ProbeSet = {
  id: string;
  name: string;
  status: string;
  probe_count?: number;
  schedule?: string;
  active?: boolean;
};

type ProbeRun = {
  id: string;
  probe_set_id?: string;
  surface?: string;
  prompt?: string;
  answer_text?: string;
  sentiment?: string;
  is_brand_mentioned?: boolean;
  is_url_cited?: boolean;
  run_at?: string;
};

type Citation = {
  id?: string;
  surface?: string;
  cited_url?: string;
  is_own_site?: boolean;
  is_competitor?: boolean;
  captured_at?: string;
};

function fmtTime(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const SURFACE_LABEL: Record<string, string> = {
  chatgpt: "ChatGPT",
  perplexity: "Perplexity",
  gemini: "Gemini",
  claude: "Claude",
  copilot: "Copilot",
  google_ai: "Google AI",
};

const SENTIMENT_CLASS: Record<string, string> = {
  positive: "badge",
  neutral: "badge",
  negative: "badge-critical",
};

const SENTIMENT_LABEL: Record<string, string> = {
  positive: "正面",
  neutral: "中立",
  negative: "負面",
};

type ProbeRunForm = {
  probe_set_id: string;
  surface: string;
  prompt: string;
  answer_text: string;
  sentiment: string;
};

export default function AiVisibilityPage() {
  const { siteId, client } = useSiteContext();
  const [dash, setDash] = useState<AiVisibilityDashboard | null>(null);
  const [probeSets, setProbeSets] = useState<ProbeSet[]>([]);
  const [probeRuns, setProbeRuns] = useState<ProbeRun[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showProbeForm, setShowProbeForm] = useState(false);
  const [probeForm, setProbeForm] = useState<ProbeRunForm>({
    probe_set_id: "",
    surface: "chatgpt",
    prompt: "",
    answer_text: "",
    sentiment: "neutral",
  });
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<"probeSets" | "runs" | "citations">("probeSets");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [d, ps, runsData, c] = await Promise.all([
        client.getAiDashboard(siteId),
        client.listProbeSets(siteId),
        client.listAiProbeRuns(siteId),
        client.listCitations(siteId),
      ]);
      setDash(d);
      setProbeSets(ps as ProbeSet[]);
      setProbeRuns(runsData as ProbeRun[]);
      setCitations(c as Citation[]);
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

  async function submitProbeRun() {
    if (!probeForm.probe_set_id || !probeForm.prompt.trim() || !probeForm.answer_text.trim()) {
      setError("請填寫必要欄位：Probe Set、Prompt、AI 回答");
      return;
    }
    setSubmitting(true);
    setSuccess(null);
    try {
      await client.submitProbeRun({
        site_id: siteId,
        probe_set_id: probeForm.probe_set_id,
        surface: probeForm.surface,
        prompt: probeForm.prompt,
        answer_text: probeForm.answer_text,
        sentiment: probeForm.sentiment,
      });
      setSuccess("Probe run 已記錄");
      setProbeForm({ probe_set_id: "", surface: "chatgpt", prompt: "", answer_text: "", sentiment: "neutral" });
      setShowProbeForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失敗");
    } finally {
      setSubmitting(false);
    }
  }

  if (!dash && !loading) return <p style={{ color: "var(--danger)" }}>{error ?? "無法載入"}</p>;
  if (!dash) return <p style={{ color: "var(--muted)" }}>載入 AI 能見度…</p>;

  const serpo = dash.serpo_summary ?? {};

  return (
    <>
      <PageHeader title="AI 能見度" subtitle="Probe、Citation、品牌提及與 SERPO 情緒摘要" />

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      <div className="kpi-grid" style={{ marginBottom: "2rem" }}>
        <KpiCard label="Probe Sets" value={dash.probe_set_count} />
        <KpiCard label="Probe Runs" value={dash.probe_run_count} />
        <KpiCard label="Citations" value={dash.citation_count} />
        <KpiCard label="品牌提及" value={dash.brand_mention_count} />
        <KpiCard label="競品提及" value={dash.competitor_mention_count} />
        <KpiCard label="SERPO 正面" value={Number(serpo.positive ?? 0)} />
        <KpiCard label="SERPO 負面" value={Number(serpo.negative ?? 0)} />
      </div>

      {/* Tab navigation */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem", borderBottom: "1px solid var(--border)", paddingBottom: "0.75rem" }}>
        {(["probeSets", "runs", "citations"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "0.4rem 1rem",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: activeTab === tab ? "var(--accent)" : "var(--surface-2)",
              color: activeTab === tab ? "#ffffff" : "var(--text)",
              cursor: "pointer",
              font: "inherit",
              fontSize: "0.88rem",
            }}
          >
            {tab === "probeSets" ? `Probe Sets (${probeSets.length})` : tab === "runs" ? `Probe Runs (${probeRuns.length})` : `Citations (${citations.length})`}
          </button>
        ))}
        <button
          type="button"
          className="btn btn-primary"
          style={{ marginLeft: "auto" }}
          onClick={() => {
            setShowProbeForm(!showProbeForm);
            setError(null);
          }}
        >
          {showProbeForm ? "取消" : "+ 錄入 Probe Run"}
        </button>
      </div>

      {/* Probe run input form */}
      {showProbeForm && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>手動錄入 AI Probe Run</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 0 }}>
            向 AI 提問後，將完整對話錄入系統進行品牌可見性分析
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                Probe Set *
              </label>
              <select
                value={probeForm.probe_set_id}
                onChange={(e) => setProbeForm({ ...probeForm, probe_set_id: e.target.value })}
                style={{ width: "100%" }}
              >
                <option value="">— 選擇 Probe Set —</option>
                {probeSets.map((ps) => (
                  <option key={ps.id} value={ps.id}>
                    {ps.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                AI 平台
              </label>
              <select
                value={probeForm.surface}
                onChange={(e) => setProbeForm({ ...probeForm, surface: e.target.value })}
                style={{ width: "100%" }}
              >
                {Object.entries(SURFACE_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                情緒評估
              </label>
              <select
                value={probeForm.sentiment}
                onChange={(e) => setProbeForm({ ...probeForm, sentiment: e.target.value })}
                style={{ width: "100%" }}
              >
                <option value="positive">正面</option>
                <option value="neutral">中立</option>
                <option value="negative">負面</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
              Prompt（詢問 AI 的問題）*
            </label>
            <textarea
              value={probeForm.prompt}
              onChange={(e) => setProbeForm({ ...probeForm, prompt: e.target.value })}
              rows={2}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="例：推薦幾個適合中小企業的 SEO 工具"
            />
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
              AI 完整回答 *
            </label>
            <textarea
              value={probeForm.answer_text}
              onChange={(e) => setProbeForm({ ...probeForm, answer_text: e.target.value })}
              rows={5}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="貼上 AI 的完整回答內容…"
            />
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={submitting}
              onClick={submitProbeRun}
            >
              {submitting ? "提交中…" : "確認提交"}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => {
                setShowProbeForm(false);
                setError(null);
              }}
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* Probe Sets tab */}
      {activeTab === "probeSets" && (
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>名稱</th>
                <th>Probe 數</th>
                <th>排程</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              {probeSets.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ color: "var(--muted)" }}>
                    尚無 probe set，請先建立
                  </td>
                </tr>
              ) : (
                probeSets.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td>{p.probe_count ?? 0}</td>
                    <td style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                      {p.schedule ?? "手動"}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{ color: p.active ? "var(--success)" : undefined }}
                      >
                        {p.active ? "啟用" : "停用"}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Probe Runs tab */}
      {activeTab === "runs" && (
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>平台</th>
                <th>Prompt</th>
                <th>情緒</th>
                <th>品牌提及</th>
                <th>URL 引用</th>
                <th>時間</th>
              </tr>
            </thead>
            <tbody>
              {probeRuns.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ color: "var(--muted)" }}>
                    尚無 probe run 紀錄
                  </td>
                </tr>
              ) : (
                probeRuns.map((r, i) => (
                  <tr key={r.id ?? i}>
                    <td>{SURFACE_LABEL[r.surface ?? ""] ?? r.surface ?? "—"}</td>
                    <td style={{ maxWidth: 280, fontSize: "0.85rem" }}>
                      {(r.prompt ?? "—").slice(0, 80)}
                      {(r.prompt?.length ?? 0) > 80 ? "…" : ""}
                    </td>
                    <td>
                      {r.sentiment ? (
                        <span className={`badge ${SENTIMENT_CLASS[r.sentiment] ?? ""}`}>
                          {SENTIMENT_LABEL[r.sentiment] ?? r.sentiment}
                        </span>
                      ) : "—"}
                    </td>
                    <td>{r.is_brand_mentioned ? <span style={{ color: "var(--success)" }}>✓</span> : <span style={{ color: "var(--muted)" }}>—</span>}</td>
                    <td>{r.is_url_cited ? <span style={{ color: "var(--success)" }}>✓</span> : <span style={{ color: "var(--muted)" }}>—</span>}</td>
                    <td style={{ fontSize: "0.8rem", color: "var(--muted)", whiteSpace: "nowrap" }}>
                      {fmtTime(r.run_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Citations tab */}
      {activeTab === "citations" && (
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>AI 平台</th>
                <th>引用 URL</th>
                <th>自有站</th>
                <th>競品</th>
                <th>擷取時間</th>
              </tr>
            </thead>
            <tbody>
              {(citations.length ? citations : (dash.recent_citations as Citation[])).map(
                (c, i) => (
                  <tr key={String(c.id ?? i)}>
                    <td>{SURFACE_LABEL[c.surface ?? ""] ?? c.surface ?? "—"}</td>
                    <td
                      style={{
                        maxWidth: 300,
                        wordBreak: "break-all",
                        fontSize: "0.82rem",
                      }}
                    >
                      {c.cited_url ? (
                        <a
                          href={c.cited_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: "var(--accent)" }}
                        >
                          {c.cited_url.slice(0, 60)}
                          {c.cited_url.length > 60 ? "…" : ""}
                        </a>
                      ) : "—"}
                    </td>
                    <td>
                      {c.is_own_site ? (
                        <span style={{ color: "var(--success)" }}>✓ 自有</span>
                      ) : (
                        <span style={{ color: "var(--muted)" }}>—</span>
                      )}
                    </td>
                    <td>
                      {c.is_competitor ? (
                        <span style={{ color: "var(--danger)" }}>✓ 競品</span>
                      ) : (
                        <span style={{ color: "var(--muted)" }}>—</span>
                      )}
                    </td>
                    <td style={{ fontSize: "0.8rem", color: "var(--muted)", whiteSpace: "nowrap" }}>
                      {fmtTime(c.captured_at)}
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
