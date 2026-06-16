"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type SerpoRecord = {
  id: string;
  brand_query: string;
  keyword: string;
  first_page_positive_count: number;
  first_page_neutral_count: number;
  first_page_negative_count: number;
  first_page_wrong_info_count: number;
  captured_at: string;
};

export default function SerpoPage() {
  const { siteId, client } = useSiteContext();
  const [records, setRecords] = useState<SerpoRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    brand_query: "",
    keyword: "",
    first_page_positive_count: 0,
    first_page_neutral_count: 0,
    first_page_negative_count: 0,
    first_page_wrong_info_count: 0,
  });

  const load = useCallback(async () => {
    try {
      const data = await client.listSerpoRecords(siteId);
      setRecords(data as SerpoRecord[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    }
  }, [client, siteId]);

  useEffect(() => { load(); }, [load]);

  async function submit() {
    if (!form.brand_query.trim()) { setError("請填寫品牌查詢詞"); return; }
    setSubmitting(true);
    try {
      await client.createSerpoRecord({
        site_id: siteId,
        brand_query: form.brand_query.trim(),
        keyword: form.keyword.trim() || undefined,
        first_page_positive_count: form.first_page_positive_count,
        first_page_neutral_count: form.first_page_neutral_count,
        first_page_negative_count: form.first_page_negative_count,
        first_page_wrong_info_count: form.first_page_wrong_info_count,
      });
      setSuccess("SERPO 紀錄已建立");
      setShowForm(false);
      setForm({ brand_query: "", keyword: "", first_page_positive_count: 0, first_page_neutral_count: 0, first_page_negative_count: 0, first_page_wrong_info_count: 0 });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立失敗");
    } finally { setSubmitting(false); }
  }

  return (
    <>
      <PageHeader title="SERPO" subtitle="Search engine result page opinion 與情緒分布" />
      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button type="button" className="btn btn-primary" onClick={() => { setShowForm(!showForm); setError(null); }}>
          {showForm ? "取消" : "+ 錄入 SERPO 紀錄"}
        </button>
        <button type="button" className="btn" onClick={load}>重新整理</button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>手動錄入 SERPO 紀錄</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 0 }}>
            針對品牌關鍵字，手動檢查 Google 搜尋結果第一頁的內容情緒分布
          </p>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>品牌查詢詞 *</label>
            <input value={form.brand_query} onChange={(e) => setForm({ ...form, brand_query: e.target.value })} style={{ width: "100%" }} placeholder="例：恆惠修理紗窗" />
          </div>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>關鍵字（選填）</label>
            <input value={form.keyword} onChange={(e) => setForm({ ...form, keyword: e.target.value })} style={{ width: "100%" }} placeholder="例：恆惠修理紗窗 評價" />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>正面結果數</label>
              <input type="number" min={0} value={form.first_page_positive_count} onChange={(e) => setForm({ ...form, first_page_positive_count: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>中性結果數</label>
              <input type="number" min={0} value={form.first_page_neutral_count} onChange={(e) => setForm({ ...form, first_page_neutral_count: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>負面結果數</label>
              <input type="number" min={0} value={form.first_page_negative_count} onChange={(e) => setForm({ ...form, first_page_negative_count: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>錯誤資訊數</label>
              <input type="number" min={0} value={form.first_page_wrong_info_count} onChange={(e) => setForm({ ...form, first_page_wrong_info_count: Number(e.target.value) })} style={{ width: "100%" }} />
            </div>
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
              <th>品牌查詢</th>
              <th>關鍵字</th>
              <th>正面</th>
              <th>中性</th>
              <th>負面</th>
              <th>錯誤資訊</th>
              <th>擷取時間</th>
            </tr>
          </thead>
          <tbody>
            {records.length === 0 ? (
              <tr><td colSpan={7} style={{ color: "var(--muted)" }}>尚無 SERPO 紀錄，請點擊上方按鈕手動錄入</td></tr>
            ) : (
              records.map((r) => (
                <tr key={String(r.id)}>
                  <td>{r.brand_query}</td>
                  <td>{r.keyword}</td>
                  <td>{r.first_page_positive_count}</td>
                  <td>{r.first_page_neutral_count}</td>
                  <td>{r.first_page_negative_count}</td>
                  <td>{r.first_page_wrong_info_count}</td>
                  <td>{r.captured_at ? new Date(r.captured_at).toLocaleString("zh-TW") : ""}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
