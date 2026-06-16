"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type BrandEntity = {
  id: string;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  status: string;
};

export default function BrandPage() {
  const { siteId, client } = useSiteContext();
  const [entities, setEntities] = useState<BrandEntity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    canonical_name: "",
    entity_type: "brand",
    aliases: "",
    description: "",
  });

  const load = useCallback(async () => {
    try {
      const data = await client.listBrandEntities(siteId);
      setEntities(data as BrandEntity[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    }
  }, [client, siteId]);

  useEffect(() => { load(); }, [load]);

  async function submit() {
    if (!form.canonical_name.trim()) { setError("請填寫品牌名稱"); return; }
    setSubmitting(true);
    try {
      await client.createBrandEntity({
        site_id: siteId,
        canonical_name: form.canonical_name.trim(),
        entity_type: form.entity_type,
        aliases_json: form.aliases.split("\n").filter(Boolean),
        description: form.description || null,
      });
      setSuccess("品牌實體已建立");
      setShowForm(false);
      setForm({ canonical_name: "", entity_type: "brand", aliases: "", description: "" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立失敗");
    } finally { setSubmitting(false); }
  }

  return (
    <>
      <PageHeader title="品牌實體" subtitle="Brand entities 與一致性檢查基礎" />
      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button type="button" className="btn btn-primary" onClick={() => { setShowForm(!showForm); setError(null); }}>
          {showForm ? "取消" : "+ 新增品牌實體"}
        </button>
        <button type="button" className="btn" onClick={load}>重新整理</button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>新增品牌實體</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>品牌正式名稱 *</label>
              <input value={form.canonical_name} onChange={(e) => setForm({ ...form, canonical_name: e.target.value })} style={{ width: "100%" }} placeholder="例：恆惠修理紗窗" />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>類型</label>
              <select value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })} style={{ width: "100%" }}>
                <option value="brand">品牌</option>
                <option value="product">產品</option>
                <option value="service">服務</option>
                <option value="person">人物</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>別名（每行一個）</label>
            <textarea value={form.aliases} onChange={(e) => setForm({ ...form, aliases: e.target.value })} rows={3} style={{ width: "100%", resize: "vertical" }} placeholder="例：ezfix&#10;恆惠" />
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>描述</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} style={{ width: "100%", resize: "vertical" }} placeholder="品牌簡介…" />
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
              <th>名稱</th>
              <th>類型</th>
              <th>別名</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            {entities.length === 0 ? (
              <tr><td colSpan={4} style={{ color: "var(--muted)" }}>尚無品牌實體，請點擊上方按鈕新增</td></tr>
            ) : (
              entities.map((e) => (
                <tr key={String(e.id)}>
                  <td>{e.canonical_name}</td>
                  <td>{e.entity_type}</td>
                  <td>{Array.isArray(e.aliases) ? e.aliases.join(", ") : String(e.aliases ?? "")}</td>
                  <td>{e.status ?? "active"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
