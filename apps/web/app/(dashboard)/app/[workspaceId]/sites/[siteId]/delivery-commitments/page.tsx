"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type DeliveryCommitment = {
  id: string;
  period: string;
  new_content_target: number;
  refresh_target: number;
  faq_schema_target: number;
  technical_fix_target: number;
  report_target: number;
  effective_from: string;
  effective_to: string | null;
  notes: string | null;
  status?: string;
};

export default function DeliveryCommitmentsPage() {
  const { siteId, client } = useSiteContext();
  const [rows, setRows] = useState<DeliveryCommitment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function deactivate(id: string) {
    setBusyId(id);
    setSuccess(null);
    try {
      await client.deactivateDeliveryCommitment(id);
      setSuccess("已封存該交付承諾");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "封存失敗");
    } finally {
      setBusyId(null);
    }
  }
  const [form, setForm] = useState({
    period: "monthly",
    new_content_target: 2,
    refresh_target: 3,
    faq_schema_target: 2,
    technical_fix_target: 2,
    report_target: 1,
    effective_from: new Date().toISOString().slice(0, 10),
    effective_to: "",
    notes: "",
  });

  const load = useCallback(async () => {
    try {
      const data = await client.listDeliveryCommitments(siteId);
      setRows(data as DeliveryCommitment[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    }
  }, [client, siteId]);

  useEffect(() => {
    load();
  }, [load]);

  async function submit() {
    if (!form.effective_from) {
      setError("請填寫生效日期");
      return;
    }
    setSubmitting(true);
    setSuccess(null);
    try {
      await client.createDeliveryCommitment({
        site_id: siteId,
        period: form.period,
        new_content_target: form.new_content_target,
        refresh_target: form.refresh_target,
        faq_schema_target: form.faq_schema_target,
        technical_fix_target: form.technical_fix_target,
        report_target: form.report_target,
        effective_from: form.effective_from,
        effective_to: form.effective_to || null,
        notes: form.notes || null,
      });
      setSuccess("交付承諾已建立");
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立失敗");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader title="交付承諾" subtitle="產能邊界與每月交付上限" />
      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => { setShowForm(!showForm); setError(null); }}
        >
          {showForm ? "取消" : "+ 新增交付承諾"}
        </button>
        <button type="button" className="btn" onClick={load}>
          重新整理
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>新增交付承諾</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>期間</label>
              <select value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value })} style={{ width: "100%" }}>
                <option value="monthly">每月</option>
                <option value="quarterly">每季</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>文章上限</label>
              <input type="number" min={0} value={form.new_content_target} onChange={(e) => setForm({ ...form, new_content_target: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>Refresh 上限</label>
              <input type="number" min={0} value={form.refresh_target} onChange={(e) => setForm({ ...form, refresh_target: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>FAQ Schema 上限</label>
              <input type="number" min={0} value={form.faq_schema_target} onChange={(e) => setForm({ ...form, faq_schema_target: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>Technical Fix 上限</label>
              <input type="number" min={0} value={form.technical_fix_target} onChange={(e) => setForm({ ...form, technical_fix_target: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>月報上限</label>
              <input type="number" min={0} value={form.report_target} onChange={(e) => setForm({ ...form, report_target: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>生效日期 *</label>
              <input type="date" value={form.effective_from} onChange={(e) => setForm({ ...form, effective_from: e.target.value })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>結束日期</label>
              <input type="date" value={form.effective_to} onChange={(e) => setForm({ ...form, effective_to: e.target.value })} style={{ width: "100%" }} />
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>備註</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} style={{ width: "100%", resize: "vertical" }} placeholder="例：ezfix 每月產能上限…" />
          </div>
          <div style={{ marginTop: "1rem" }}>
            <button type="button" className="btn btn-primary" disabled={submitting} onClick={submit}>
              {submitting ? "建立中…" : "確認建立"}
            </button>
          </div>
        </div>
      )}

      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>期間</th>
              <th>文章上限</th>
              <th>Refresh 上限</th>
              <th>FAQ Schema</th>
              <th>Technical Fix</th>
              <th>月報</th>
              <th>生效日期</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ color: "var(--muted)" }}>尚無交付承諾，請點擊上方按鈕新增</td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={String(r.id)}>
                  <td>{r.period === "monthly" ? "每月" : r.period === "quarterly" ? "每季" : r.period}</td>
                  <td>{r.new_content_target}</td>
                  <td>{r.refresh_target}</td>
                  <td>{r.faq_schema_target ?? 0}</td>
                  <td>{r.technical_fix_target}</td>
                  <td>{r.report_target ?? 1}</td>
                  <td>{r.effective_from}{r.effective_to ? ` — ${r.effective_to}` : ""}</td>
                  <td>{r.status ?? "active"}</td>
                  <td>
                    {r.status !== "archived" && (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={{ fontSize: "0.78rem", padding: "0.25rem 0.5rem", color: "var(--muted)" }}
                        disabled={busyId === r.id}
                        onClick={() => deactivate(r.id)}
                      >
                        {busyId === r.id ? "封存中…" : "封存"}
                      </button>
                    )}
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
