"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type KnowledgeSource = {
  id: string;
  title: string | null;
  source_url: string | null;
  source_type: string;
  approval_status: string;
  status?: string;
  fact_count?: number;
  created_at?: string;
};

const APPROVAL_CLASS: Record<string, string> = {
  approved: "",
  pending_review: "badge-high",
  revoked: "badge-critical",
};

const APPROVAL_LABEL: Record<string, string> = {
  approved: "已核准",
  pending_review: "待審核",
  revoked: "已撤銷",
  draft: "草稿",
};

const SOURCE_TYPE_LABEL: Record<string, string> = {
  webpage: "網頁",
  document: "文件",
  manual: "手動輸入",
  api_feed: "API Feed",
  faq: "FAQ",
};

function fmtDate(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("zh-TW", { month: "2-digit", day: "2-digit" });
}

type CreateForm = {
  title: string;
  source_type: string;
  source_url: string;
  content_text: string;
};

export default function KnowledgePage() {
  const { siteId, client } = useSiteContext();
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateForm>({
    title: "",
    source_type: "webpage",
    source_url: "",
    content_text: "",
  });
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, s] = await Promise.all([
        client.getBrandProfile(siteId),
        client.listKnowledgeSources(siteId),
      ]);
      setProfile(p);
      setSources(s as KnowledgeSource[]);
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

  async function handleApprove(sourceId: string) {
    setBusyId(sourceId);
    setSuccess(null);
    try {
      await client.approveKnowledgeSource(sourceId);
      setSuccess("已核准知識來源");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "核准失敗");
    } finally {
      setBusyId(null);
    }
  }

  async function handleIngest(sourceId: string) {
    setBusyId(`ingest-${sourceId}`);
    setSuccess(null);
    try {
      const res = await client.triggerKnowledgeIngest(sourceId);
      setSuccess(`Ingest 已排程（job: ${res.job_run_id.slice(0, 8)}…）`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest 失敗");
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreate() {
    if (!form.title.trim()) {
      setError("請填寫來源名稱");
      return;
    }
    setCreating(true);
    setSuccess(null);
    try {
      await client.createKnowledgeSource({
        site_id: siteId,
        title: form.title,
        source_type: form.source_type,
        source_url: form.source_url || undefined,
        content_text: form.content_text || undefined,
      });
      setSuccess("已新增知識來源");
      setForm({ title: "", source_type: "webpage", source_url: "", content_text: "" });
      setShowCreate(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增失敗");
    } finally {
      setCreating(false);
    }
  }

  const approvedCount = sources.filter((s) => s.approval_status === "approved").length;
  const pendingCount = sources.filter((s) => s.approval_status === "pending_review").length;

  return (
    <>
      <PageHeader title="知識庫" subtitle="Brand profile、知識來源管理與核准" />

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      {/* Brand Profile */}
      {profile ? (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h2 style={{ fontSize: "1rem", marginTop: 0, marginBottom: "0.5rem" }}>
                Brand Profile
              </h2>
              <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.88rem", lineHeight: 1.6 }}>
                {String(
                  profile.brand_voice_summary ??
                    profile.summary ??
                    profile.canonical_brand_name ??
                    "—",
                )}
              </p>
            </div>
            {profile.canonical_brand_name != null && (
              <span
                style={{
                  fontSize: "0.82rem",
                  background: "var(--accent-soft)",
                  color: "var(--accent)",
                  padding: "0.2rem 0.6rem",
                  borderRadius: 6,
                  whiteSpace: "nowrap",
                }}
              >
                {String(profile.canonical_brand_name)}
              </span>
            )}
          </div>
        </div>
      ) : null}

      {/* Stats row */}
      {!loading && (
        <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          <div className="card">
            <div className="kpi-label">知識來源</div>
            <div className="kpi-value">{sources.length}</div>
          </div>
          <div className="card">
            <div className="kpi-label">已核准</div>
            <div className="kpi-value" style={{ color: "var(--success)" }}>
              {approvedCount}
            </div>
          </div>
          {pendingCount > 0 && (
            <div className="card" style={{ borderColor: "var(--warning)" }}>
              <div className="kpi-label">待審核</div>
              <div className="kpi-value" style={{ color: "var(--warning)" }}>
                {pendingCount}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action bar */}
      <div className="form-row" style={{ marginBottom: "1rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => {
            setShowCreate(!showCreate);
            setError(null);
          }}
        >
          {showCreate ? "取消新增" : "+ 新增知識來源"}
        </button>
        <button type="button" className="btn" disabled={loading} onClick={load}>
          重新整理
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>新增知識來源</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                來源名稱 *
              </label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="例：官網 FAQ、產品白皮書"
                style={{ width: "100%" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                來源類型
              </label>
              <select
                value={form.source_type}
                onChange={(e) => setForm({ ...form, source_type: e.target.value })}
                style={{ width: "100%" }}
              >
                <option value="webpage">網頁</option>
                <option value="document">文件</option>
                <option value="manual">手動輸入</option>
                <option value="faq">FAQ</option>
                <option value="api_feed">API Feed</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                來源 URL（選填）
              </label>
              <input
                value={form.source_url}
                onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                placeholder="https://example.com/faq"
                style={{ width: "100%" }}
              />
            </div>
          </div>
          {form.source_type === "manual" && (
            <div style={{ marginTop: "0.75rem" }}>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                內容文字
              </label>
              <textarea
                value={form.content_text}
                onChange={(e) => setForm({ ...form, content_text: e.target.value })}
                rows={5}
                style={{ width: "100%", resize: "vertical" }}
                placeholder="貼上要作為知識來源的文字內容…"
              />
            </div>
          )}
          <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={creating}
              onClick={handleCreate}
            >
              {creating ? "新增中…" : "確認新增"}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => {
                setShowCreate(false);
                setError(null);
              }}
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* Sources table */}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>來源名稱</th>
              <th>類型</th>
              <th>核准狀態</th>
              <th style={{ width: 64 }}>Facts</th>
              <th>新增日期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ color: "var(--muted)" }}>
                  載入中…
                </td>
              </tr>
            ) : sources.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ color: "var(--muted)" }}>
                  尚無知識來源，請點「新增知識來源」
                </td>
              </tr>
            ) : (
              sources.map((s) => (
                <tr key={s.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{s.title ?? "—"}</div>
                    {s.source_url && (
                      <a
                        href={s.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: "0.78rem",
                          color: "var(--accent)",
                          wordBreak: "break-all",
                        }}
                      >
                        {s.source_url.slice(0, 60)}
                        {s.source_url.length > 60 ? "…" : ""}
                      </a>
                    )}
                  </td>
                  <td>{SOURCE_TYPE_LABEL[s.source_type] ?? s.source_type}</td>
                  <td>
                    <span className={`badge ${APPROVAL_CLASS[s.approval_status] ?? ""}`}>
                      {APPROVAL_LABEL[s.approval_status] ?? s.approval_status}
                    </span>
                  </td>
                  <td>{s.fact_count ?? "—"}</td>
                  <td style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {fmtDate(s.created_at)}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                      {s.approval_status === "pending_review" && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: "0.78rem", padding: "0.25rem 0.55rem" }}
                          disabled={busyId === s.id}
                          onClick={() => handleApprove(s.id)}
                        >
                          核准
                        </button>
                      )}
                      {s.approval_status === "approved" && (
                        <button
                          type="button"
                          className="btn"
                          style={{ fontSize: "0.78rem", padding: "0.25rem 0.55rem" }}
                          disabled={busyId === `ingest-${s.id}`}
                          onClick={() => handleIngest(s.id)}
                        >
                          {busyId === `ingest-${s.id}` ? "排程中…" : "觸發 Ingest"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
