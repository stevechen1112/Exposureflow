"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import type { AiVisibilityDashboard } from "@exposureflow/shared-types";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

/* ── Types ── */
type ProbeSet = { id: string; name: string; status: string; probe_count?: number; schedule?: string; active?: boolean };
type ProbeRun = { id: string; probe_set_id?: string; surface?: string; prompt?: string; answer_text?: string; sentiment?: string; is_brand_mentioned?: boolean; is_url_cited?: boolean; run_at?: string };
type Citation = { id?: string; surface?: string; cited_url?: string; is_own_site?: boolean; is_competitor?: boolean; captured_at?: string };
type SerpoRecord = { id: string; brand_query: string; keyword: string; first_page_positive_count: number; first_page_neutral_count: number; first_page_negative_count: number; first_page_wrong_info_count: number; captured_at: string };
type BrandEntity = { id: string; canonical_name: string; entity_type: string; aliases: string[]; status: string };

/* ── Labels ── */
const SURFACE_LABEL: Record<string, string> = { chatgpt: "ChatGPT", perplexity: "Perplexity", gemini: "Gemini", claude: "Claude", copilot: "Copilot", google_ai: "Google AI" };
const SENTIMENT_LABEL: Record<string, string> = { positive: "正面", neutral: "中立", negative: "負面" };
const SENTIMENT_CLASS: Record<string, string> = { positive: "badge", neutral: "badge", negative: "badge-critical" };

function fmtTime(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-TW", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

type TabId = "overview" | "ai-citations" | "brand-sentiment" | "brand-entities";

export default function AiBrandPage() {
  const { siteId, client } = useSiteContext();
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  /* ── AI Visibility state ── */
  const [dash, setDash] = useState<AiVisibilityDashboard | null>(null);
  const [probeSets, setProbeSets] = useState<ProbeSet[]>([]);
  const [probeRuns, setProbeRuns] = useState<ProbeRun[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [showProbeForm, setShowProbeForm] = useState(false);
  const [showProbeSetForm, setShowProbeSetForm] = useState(false);
  const [probeSetForm, setProbeSetForm] = useState({ name: "", prompts: "", surfaces: "chatgpt,perplexity,copilot,google_ai", schedule: "", active: true });
  const [probeForm, setProbeForm] = useState({ probe_set_id: "", surface: "chatgpt", prompt: "", answer_text: "", sentiment: "neutral" });

  /* ── SERPO state ── */
  const [serpoRecords, setSerpoRecords] = useState<SerpoRecord[]>([]);
  const [showSerpoForm, setShowSerpoForm] = useState(false);
  const [serpoForm, setSerpoForm] = useState({ brand_query: "", keyword: "", first_page_positive_count: 0, first_page_neutral_count: 0, first_page_negative_count: 0, first_page_wrong_info_count: 0 });

  /* ── Brand entities state ── */
  const [brandEntities, setBrandEntities] = useState<BrandEntity[]>([]);
  const [showBrandForm, setShowBrandForm] = useState(false);
  const [brandForm, setBrandForm] = useState({ canonical_name: "", entity_type: "brand", aliases: "", description: "" });

  /* ── Shared ── */
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  /* ── Loaders ── */
  const loadAi = useCallback(async () => {
    if (!siteId) return;
    try {
      const d = await client.getAiDashboard(siteId);
      setDash(d);
      const ps = await client.listProbeSets(siteId);
      setProbeSets(ps as ProbeSet[]);
      const pr = await client.listAiProbeRuns(siteId);
      setProbeRuns(pr as ProbeRun[]);
      const ct = await client.listCitations(siteId);
      setCitations(ct as Citation[]);
    } catch (err) { setError(err instanceof Error ? err.message : "載入 AI 資料失敗"); }
  }, [client, siteId]);

  const loadSerpo = useCallback(async () => {
    if (!siteId) return;
    try { const data = await client.listSerpoRecords(siteId); setSerpoRecords(data as SerpoRecord[]); } catch {}
  }, [client, siteId]);

  const loadBrand = useCallback(async () => {
    if (!siteId) return;
    try { const data = await client.listBrandEntities(siteId); setBrandEntities(data as BrandEntity[]); } catch {}
  }, [client, siteId]);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadAi(), loadSerpo(), loadBrand()]).finally(() => setLoading(false));
  }, [loadAi, loadSerpo, loadBrand]);

  /* ── Submit handlers ── */
  async function submitProbeSet(e: React.FormEvent) {
    e.preventDefault();
    if (!siteId) return;
    setSubmitting(true);
    try {
      await client.createProbeSet({ site_id: siteId, name: probeSetForm.name, prompts_json: probeSetForm.prompts.split("\n").filter(Boolean), surfaces_json: probeSetForm.surfaces.split(",").map(s => s.trim()).filter(Boolean), schedule: probeSetForm.schedule || undefined, active: probeSetForm.active });
      setSuccess("Probe Set 已建立");
      setShowProbeSetForm(false);
      setProbeSetForm({ name: "", prompts: "", surfaces: "chatgpt,perplexity,copilot,google_ai", schedule: "", active: true });
      await loadAi();
    } catch (err) { setError(err instanceof Error ? err.message : "建立失敗"); }
    finally { setSubmitting(false); }
  }

  async function submitProbeRun(e: React.FormEvent) {
    e.preventDefault();
    if (!siteId) return;
    setSubmitting(true);
    try {
      await client.submitProbeRun({ site_id: siteId, probe_set_id: probeForm.probe_set_id || probeSets[0]?.id || "", surface: probeForm.surface, prompt: probeForm.prompt, answer_text: probeForm.answer_text, sentiment: probeForm.sentiment });
      setSuccess("Probe Run 已錄入");
      setShowProbeForm(false);
      setProbeForm({ probe_set_id: "", surface: "chatgpt", prompt: "", answer_text: "", sentiment: "neutral" });
      await loadAi();
    } catch (err) { setError(err instanceof Error ? err.message : "錄入失敗"); }
    finally { setSubmitting(false); }
  }

  async function submitSerpo() {
    if (!siteId) return;
    if (!serpoForm.brand_query.trim()) { setError("請填寫品牌查詢詞"); return; }
    setSubmitting(true);
    try {
      await client.createSerpoRecord({ site_id: siteId, brand_query: serpoForm.brand_query.trim(), keyword: serpoForm.keyword.trim() || undefined, first_page_positive_count: serpoForm.first_page_positive_count, first_page_neutral_count: serpoForm.first_page_neutral_count, first_page_negative_count: serpoForm.first_page_negative_count, first_page_wrong_info_count: serpoForm.first_page_wrong_info_count });
      setSuccess("SERPO 紀錄已建立");
      setShowSerpoForm(false);
      setSerpoForm({ brand_query: "", keyword: "", first_page_positive_count: 0, first_page_neutral_count: 0, first_page_negative_count: 0, first_page_wrong_info_count: 0 });
      await loadSerpo();
    } catch (err) { setError(err instanceof Error ? err.message : "建立失敗"); }
    finally { setSubmitting(false); }
  }

  async function submitBrand() {
    if (!siteId) return;
    if (!brandForm.canonical_name.trim()) { setError("請填寫品牌名稱"); return; }
    setSubmitting(true);
    try {
      await client.createBrandEntity({ site_id: siteId, canonical_name: brandForm.canonical_name.trim(), entity_type: brandForm.entity_type, aliases_json: brandForm.aliases.split("\n").filter(Boolean), description: brandForm.description || null });
      setSuccess("品牌實體已建立");
      setShowBrandForm(false);
      setBrandForm({ canonical_name: "", entity_type: "brand", aliases: "", description: "" });
      await loadBrand();
    } catch (err) { setError(err instanceof Error ? err.message : "建立失敗"); }
    finally { setSubmitting(false); }
  }

  /* ── Derived ── */
  const ownCitations = citations.filter(c => c.is_own_site);
  const competitorCitations = citations.filter(c => c.is_competitor);
  const totalProbes = probeRuns.length;
  const brandMentioned = probeRuns.filter(r => r.is_brand_mentioned).length;

  const TABS: { id: TabId; label: string; count?: number }[] = [
    { id: "overview", label: "總覽" },
    { id: "ai-citations", label: "AI 引用", count: citations.length },
    { id: "brand-sentiment", label: "品牌情緒", count: serpoRecords.length },
    { id: "brand-entities", label: "品牌實體", count: brandEntities.length },
  ];

  if (!siteId) return <p style={{ color: "var(--muted)" }}>請先選擇有效站點。</p>;
  if (loading) return <p style={{ color: "var(--muted)" }}>載入中…</p>;

  return (
    <>
      <PageHeader title="AI 與品牌能見度" subtitle="AI 引用監控、品牌搜尋情緒、品牌實體管理" />
      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      {/* Tab bar */}
      <div className="tab-bar">
        {TABS.map(t => (
          <button key={t.id} className={activeTab === t.id ? "active" : ""} onClick={() => setActiveTab(t.id)}>
            {t.label}{t.count !== undefined ? ` (${t.count})` : ""}
          </button>
        ))}
      </div>

      {/* ── Tab: Overview ── */}
      {activeTab === "overview" && (
        <>
          <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
            <KpiCard label="AI 引用（自有）" value={ownCitations.length} note="AI 平台提及本站 URL" />
            <KpiCard label="競爭者引用" value={competitorCitations.length} note="AI 平台提及競爭者 URL" />
            <KpiCard label="品牌提及次數" value={brandMentioned} note="Probe 中品牌被提及" />
            <KpiCard label="總 Probe 數" value={totalProbes} note="已執行 AI 查詢次數" />
            <KpiCard label="SERPO 紀錄" value={serpoRecords.length} note="品牌搜尋情緒監控" />
            <KpiCard label="品牌實體" value={brandEntities.length} note="已登錄品牌/產品/服務" />
          </div>

          {/* Quick actions */}
          <div className="card card-primary" style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ fontSize: "1rem", margin: "0 0 0.5rem" }}>快速操作</h2>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <button type="button" className="btn btn-primary" onClick={() => { setActiveTab("ai-citations"); setShowProbeSetForm(true); }}>+ 建立 Probe Set</button>
              <button type="button" className="btn" onClick={() => { setActiveTab("ai-citations"); setShowProbeForm(true); }}>+ 錄入 Probe Run</button>
              <button type="button" className="btn" onClick={() => { setActiveTab("brand-sentiment"); setShowSerpoForm(true); }}>+ 錄入 SERPO</button>
              <button type="button" className="btn" onClick={() => { setActiveTab("brand-entities"); setShowBrandForm(true); }}>+ 新增品牌實體</button>
            </div>
          </div>

          {/* Recent activity summary */}
          {dash && (
            <div className="card card-secondary">
              <h2 style={{ fontSize: "1rem", margin: "0 0 0.5rem" }}>近期活動摘要</h2>
              <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: 0 }}>
                最近 Probe Run：{probeRuns.length > 0 ? fmtTime(probeRuns[0].run_at) : "無"} ·
                最近 SERPO：{serpoRecords.length > 0 ? fmtTime(serpoRecords[0].captured_at) : "無"} ·
                活躍 Probe Set：{probeSets.filter(p => p.active).length} 個
              </p>
            </div>
          )}
        </>
      )}

      {/* ── Tab: AI Citations ── */}
      {activeTab === "ai-citations" && (
        <>
          {/* Probe Sets */}
          <div style={{ marginBottom: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <h2 style={{ fontSize: "1rem", margin: 0 }}>Probe Sets</h2>
              <button type="button" className="btn btn-primary" onClick={() => setShowProbeSetForm(!showProbeSetForm)}>
                {showProbeSetForm ? "取消" : "+ 建立 Probe Set"}
              </button>
            </div>
            {showProbeSetForm && (
              <form className="card" onSubmit={submitProbeSet} style={{ marginBottom: "1rem" }}>
                <h3 style={{ fontSize: "0.95rem", marginTop: 0 }}>建立 Probe Set</h3>
                <div style={{ display: "grid", gap: "0.75rem" }}>
                  <label><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>名稱 *</span>
                    <input value={probeSetForm.name} onChange={e => setProbeSetForm({ ...probeSetForm, name: e.target.value })} style={{ width: "100%" }} required />
                  </label>
                  <label><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>Prompts（每行一個）</span>
                    <textarea value={probeSetForm.prompts} onChange={e => setProbeSetForm({ ...probeSetForm, prompts: e.target.value })} rows={3} style={{ width: "100%" }} />
                  </label>
                  <label><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>AI 平台（逗號分隔）</span>
                    <input value={probeSetForm.surfaces} onChange={e => setProbeSetForm({ ...probeSetForm, surfaces: e.target.value })} style={{ width: "100%" }} />
                  </label>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "建立中…" : "確認建立"}</button>
                </div>
              </form>
            )}
            <div className="table-wrap card" style={{ padding: 0 }}>
              <table>
                <thead><tr><th>名稱</th><th>Probe 數</th><th>排程</th><th>狀態</th></tr></thead>
                <tbody>
                  {probeSets.length === 0 ? <tr><td colSpan={4} style={{ color: "var(--muted)" }}>尚無 Probe Set</td></tr> :
                    probeSets.map(ps => (
                      <tr key={ps.id}><td>{ps.name}</td><td>{ps.probe_count ?? 0}</td><td>{ps.schedule || "手動"}</td><td>{ps.active ? "🟢 啟用" : "⏸ 暫停"}</td></tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Probe Runs */}
          <div style={{ marginBottom: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <h2 style={{ fontSize: "1rem", margin: 0 }}>Probe Runs</h2>
              <button type="button" className="btn" onClick={() => setShowProbeForm(!showProbeForm)}>
                {showProbeForm ? "取消" : "+ 錄入 Probe Run"}
              </button>
            </div>
            {showProbeForm && (
              <form className="card" onSubmit={submitProbeRun} style={{ marginBottom: "1rem" }}>
                <h3 style={{ fontSize: "0.95rem", marginTop: 0 }}>手動錄入 Probe Run</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  <label><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>AI 平台</span>
                    <select value={probeForm.surface} onChange={e => setProbeForm({ ...probeForm, surface: e.target.value })} style={{ width: "100%" }}>
                      {Object.entries(SURFACE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </label>
                  <label><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>情緒</span>
                    <select value={probeForm.sentiment} onChange={e => setProbeForm({ ...probeForm, sentiment: e.target.value })} style={{ width: "100%" }}>
                      {Object.entries(SENTIMENT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </label>
                  <label style={{ gridColumn: "1 / -1" }}><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>Prompt</span>
                    <textarea value={probeForm.prompt} onChange={e => setProbeForm({ ...probeForm, prompt: e.target.value })} rows={2} style={{ width: "100%" }} />
                  </label>
                  <label style={{ gridColumn: "1 / -1" }}><span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>AI 回答</span>
                    <textarea value={probeForm.answer_text} onChange={e => setProbeForm({ ...probeForm, answer_text: e.target.value })} rows={3} style={{ width: "100%" }} />
                  </label>
                  <button type="submit" className="btn btn-primary" disabled={submitting} style={{ gridColumn: "1 / -1" }}>{submitting ? "錄入中…" : "確認錄入"}</button>
                </div>
              </form>
            )}
            <div className="table-wrap card" style={{ padding: 0 }}>
              <table>
                <thead><tr><th>平台</th><th>Prompt</th><th>情緒</th><th>品牌提及</th><th>URL 引用</th><th>時間</th></tr></thead>
                <tbody>
                  {probeRuns.length === 0 ? <tr><td colSpan={6} style={{ color: "var(--muted)" }}>尚無 Probe Run</td></tr> :
                    probeRuns.map(r => (
                      <tr key={r.id}><td>{SURFACE_LABEL[r.surface ?? ""] ?? r.surface}</td><td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{r.prompt}</td><td><span className={SENTIMENT_CLASS[r.sentiment ?? ""] ?? "badge"}>{SENTIMENT_LABEL[r.sentiment ?? ""] ?? r.sentiment}</span></td><td>{r.is_brand_mentioned ? "✅" : "—"}</td><td>{r.is_url_cited ? "✅" : "—"}</td><td>{fmtTime(r.run_at)}</td></tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Citations */}
          <div>
            <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>Citations</h2>
            <div className="table-wrap card" style={{ padding: 0 }}>
              <table>
                <thead><tr><th>平台</th><th>引用 URL</th><th>自有/競爭</th><th>擷取時間</th></tr></thead>
                <tbody>
                  {citations.length === 0 ? <tr><td colSpan={4} style={{ color: "var(--muted)" }}>尚無 Citation 資料</td></tr> :
                    citations.map(c => (
                      <tr key={c.id ?? c.cited_url}><td>{SURFACE_LABEL[c.surface ?? ""] ?? c.surface}</td><td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis" }}>{c.cited_url}</td><td>{c.is_own_site ? <span style={{ color: "var(--success)" }}>自有</span> : c.is_competitor ? <span style={{ color: "var(--danger)" }}>競爭</span> : "—"}</td><td>{fmtTime(c.captured_at)}</td></tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* ── Tab: Brand Sentiment (SERPO) ── */}
      {activeTab === "brand-sentiment" && (
        <>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button type="button" className="btn btn-primary" onClick={() => setShowSerpoForm(!showSerpoForm)}>
              {showSerpoForm ? "取消" : "+ 錄入 SERPO 紀錄"}
            </button>
            <button type="button" className="btn" onClick={loadSerpo}>重新整理</button>
          </div>
          {showSerpoForm && (
            <div className="card" style={{ marginBottom: "1.5rem" }}>
              <h2 style={{ fontSize: "1rem", marginTop: 0 }}>手動錄入 SERPO 紀錄</h2>
              <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 0 }}>針對品牌關鍵字，手動檢查 Google 搜尋結果第一頁的內容情緒分布</p>
              <div style={{ marginBottom: "0.75rem" }}>
                <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>品牌查詢詞 *</label>
                <input value={serpoForm.brand_query} onChange={e => setSerpoForm({ ...serpoForm, brand_query: e.target.value })} style={{ width: "100%" }} placeholder="例：恆惠修理紗窗" />
              </div>
              <div style={{ marginBottom: "0.75rem" }}>
                <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>關鍵字（選填）</label>
                <input value={serpoForm.keyword} onChange={e => setSerpoForm({ ...serpoForm, keyword: e.target.value })} style={{ width: "100%" }} placeholder="例：恆惠修理紗窗 評價" />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "0.75rem" }}>
                {(["first_page_positive_count", "first_page_neutral_count", "first_page_negative_count", "first_page_wrong_info_count"] as const).map((field, i) => {
                  const labels = ["正面結果數", "中性結果數", "負面結果數", "錯誤資訊數"];
                  return (
                    <div key={field}>
                      <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>{labels[i]}</label>
                      <input type="number" min={0} value={serpoForm[field]} onChange={e => setSerpoForm({ ...serpoForm, [field]: Number(e.target.value) })} style={{ width: "100%" }} />
                    </div>
                  );
                })}
              </div>
              <div style={{ marginTop: "1rem" }}>
                <button type="button" className="btn btn-primary" disabled={submitting} onClick={submitSerpo}>{submitting ? "建立中…" : "確認建立"}</button>
              </div>
            </div>
          )}
          <div className="table-wrap card" style={{ padding: 0 }}>
            <table>
              <thead><tr><th>品牌查詢</th><th>關鍵字</th><th>正面</th><th>中性</th><th>負面</th><th>錯誤資訊</th><th>擷取時間</th></tr></thead>
              <tbody>
                {serpoRecords.length === 0 ? <tr><td colSpan={7} style={{ color: "var(--muted)" }}>尚無 SERPO 紀錄</td></tr> :
                  serpoRecords.map(r => (
                    <tr key={String(r.id)}><td>{r.brand_query}</td><td>{r.keyword}</td><td>{r.first_page_positive_count}</td><td>{r.first_page_neutral_count}</td><td>{r.first_page_negative_count}</td><td>{r.first_page_wrong_info_count}</td><td>{r.captured_at ? new Date(r.captured_at).toLocaleString("zh-TW") : ""}</td></tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* ── Tab: Brand Entities ── */}
      {activeTab === "brand-entities" && (
        <>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button type="button" className="btn btn-primary" onClick={() => setShowBrandForm(!showBrandForm)}>
              {showBrandForm ? "取消" : "+ 新增品牌實體"}
            </button>
            <button type="button" className="btn" onClick={loadBrand}>重新整理</button>
          </div>
          {showBrandForm && (
            <div className="card" style={{ marginBottom: "1.5rem" }}>
              <h2 style={{ fontSize: "1rem", marginTop: 0 }}>新增品牌實體</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>品牌正式名稱 *</label>
                  <input value={brandForm.canonical_name} onChange={e => setBrandForm({ ...brandForm, canonical_name: e.target.value })} style={{ width: "100%" }} placeholder="例：恆惠修理紗窗" />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>類型</label>
                  <select value={brandForm.entity_type} onChange={e => setBrandForm({ ...brandForm, entity_type: e.target.value })} style={{ width: "100%" }}>
                    <option value="brand">品牌</option><option value="product">產品</option><option value="service">服務</option><option value="person">人物</option>
                  </select>
                </div>
              </div>
              <div style={{ marginTop: "0.75rem" }}>
                <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>別名（每行一個）</label>
                <textarea value={brandForm.aliases} onChange={e => setBrandForm({ ...brandForm, aliases: e.target.value })} rows={3} style={{ width: "100%", resize: "vertical" }} />
              </div>
              <div style={{ marginTop: "0.75rem" }}>
                <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.3rem" }}>描述</label>
                <textarea value={brandForm.description} onChange={e => setBrandForm({ ...brandForm, description: e.target.value })} rows={2} style={{ width: "100%", resize: "vertical" }} />
              </div>
              <div style={{ marginTop: "1rem" }}>
                <button type="button" className="btn btn-primary" disabled={submitting} onClick={submitBrand}>{submitting ? "建立中…" : "確認建立"}</button>
              </div>
            </div>
          )}
          <div className="table-wrap card" style={{ padding: 0 }}>
            <table>
              <thead><tr><th>名稱</th><th>類型</th><th>別名</th><th>狀態</th></tr></thead>
              <tbody>
                {brandEntities.length === 0 ? <tr><td colSpan={4} style={{ color: "var(--muted)" }}>尚無品牌實體</td></tr> :
                  brandEntities.map(e => (
                    <tr key={String(e.id)}><td>{e.canonical_name}</td><td>{e.entity_type}</td><td>{Array.isArray(e.aliases) ? e.aliases.join(", ") : String(e.aliases ?? "")}</td><td>{e.status ?? "active"}</td></tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
