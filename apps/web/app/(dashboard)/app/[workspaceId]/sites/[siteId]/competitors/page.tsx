"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type Competitor = {
  id: string;
  name: string;
  domain: string;
  active: boolean;
};

type CreateForm = {
  name: string;
  domain: string;
  aliases: string;
  notes: string;
};

export default function CompetitorsPage() {
  const { siteId, client } = useSiteContext();
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateForm>({
    name: "",
    domain: "",
    aliases: "",
    notes: "",
  });
  const [creating, setCreating] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await client.listCompetitors(siteId);
      setCompetitors(list as Competitor[]);
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

  async function handleCreate() {
    if (!form.name.trim() || !form.domain.trim()) {
      setError("請填寫競爭對手名稱與 domain");
      return;
    }
    setCreating(true);
    setSuccess(null);
    try {
      await client.createCompetitor({
        site_id: siteId,
        name: form.name.trim(),
        domain: form.domain.trim().toLowerCase(),
        aliases: form.aliases
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        notes: form.notes.trim() || null,
      });
      setSuccess("已新增競爭對手");
      setForm({ name: "", domain: "", aliases: "", notes: "" });
      setShowCreate(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增失敗");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(competitorId: string) {
    setBusyId(competitorId);
    setSuccess(null);
    try {
      await client.deleteCompetitor(competitorId);
      setSuccess("已移除競爭對手");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "移除失敗");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <PageHeader
        title="競爭對手管理"
        subtitle="登錄主要競爭對手 domain，用於 SERP 版位歸屬、AI 提及分類與曝光差距分析"
      />

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      {/* Stats */}
      {!loading && (
        <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          <div className="card">
            <div className="kpi-label">競爭對手</div>
            <div className="kpi-value">{competitors.length}</div>
          </div>
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
          {showCreate ? "取消新增" : "+ 新增競爭對手"}
        </button>
        <button type="button" className="btn" disabled={loading} onClick={load}>
          重新整理
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>新增競爭對手</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "1rem" }}>
            策略文件 §二 第 2 週：曝光版位矩陣與競品分析 — 建議登錄 3-5 個主要競爭對手
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                競爭對手名稱 *
              </label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="例：台中紗窗維修王"
                style={{ width: "100%" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
                Domain *
              </label>
              <input
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
                placeholder="例：taichung-screen.com"
                style={{ width: "100%" }}
              />
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
              別名（每行一個，選填）
            </label>
            <textarea
              value={form.aliases}
              onChange={(e) => setForm({ ...form, aliases: e.target.value })}
              rows={2}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="品牌別名、常用簡稱…"
            />
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>
              備註（選填）
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={2}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="競爭優勢、主要關鍵字、市場定位…"
            />
          </div>
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

      {/* Competitors table */}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>名稱</th>
              <th>Domain</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={3} style={{ color: "var(--muted)" }}>
                  載入中…
                </td>
              </tr>
            ) : competitors.length === 0 ? (
              <tr>
                <td colSpan={3} style={{ color: "var(--muted)" }}>
                  尚無競爭對手。請點「新增競爭對手」登錄 3-5 個主要競品 domain，用於 SERP 版位歸屬與 AI 提及分類。
                </td>
              </tr>
            ) : (
              competitors.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{c.name}</div>
                  </td>
                  <td>
                    <code style={{ fontSize: "0.85rem" }}>{c.domain}</code>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn"
                      style={{ fontSize: "0.78rem", padding: "0.25rem 0.55rem", color: "var(--danger)" }}
                      disabled={busyId === c.id}
                      onClick={() => handleDelete(c.id)}
                    >
                      {busyId === c.id ? "移除中…" : "移除"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* SEO context */}
      <div
        className="card"
        style={{
          marginTop: "1.5rem",
          fontSize: "0.82rem",
          color: "var(--muted)",
          lineHeight: 1.6,
        }}
      >
        <strong>📎 策略文件 §二 第 2 週：曝光版位矩陣與競品分析</strong>
        <p style={{ margin: "0.5rem 0 0" }}>
          競爭對手 domain 用於：SERP 版位歸屬判斷（哪些排名位置屬於競品）、AI
          提及分類（AI 回答中提及的是我方還是競品）、曝光差距分析（競品在哪些關鍵字有曝光而我方沒有）。
          建議登錄 3-5 個主要競爭對手後，回到「SERP 矩陣」與「AI 能見度」頁面查看競品分析結果。
        </p>
      </div>
    </>
  );
}
