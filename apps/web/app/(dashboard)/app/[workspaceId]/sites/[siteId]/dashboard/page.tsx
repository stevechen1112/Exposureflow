"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { ExposureDashboardMetrics } from "@exposureflow/shared-types";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { useSiteContext } from "@/lib/hooks";

const RANGE_OPTIONS = [
  { label: "7 天", days: 7 },
  { label: "28 天", days: 28 },
  { label: "90 天", days: 90 },
];

type TopicRow = {
  id: string;
  name: string;
  total_impressions: number;
  coverage_score: number;
  ai_visibility_score: number;
  status: string;
};

type AttentionItem = {
  id: string;
  label: string;
  detail: string;
  href: string;
  severity: "critical" | "warning" | "info";
};

function HealthBadge({ value, label }: { value: number; label: string }) {
  const color = value === 0 ? "var(--success)" : value <= 2 ? "var(--warning)" : "var(--danger)";
  return (
    <div className="card" style={{ borderColor: value > 0 ? color : "var(--border)" }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ color: value > 0 ? color : undefined }}>{value}</div>
    </div>
  );
}

/** Pure-SVG sparkline chart — no chart library dependency */
function TrendChart({
  data,
  width = 600,
  height = 180,
  lineColor = "var(--accent)",
  fillColor = "var(--accent-soft)",
  label,
}: {
  data: Array<{ date: string; impressions: number; clicks: number; position: number }>;
  width?: number;
  height?: number;
  lineColor?: string;
  fillColor?: string;
  label?: string;
}) {
  if (data.length < 2) return null;
  const pad = { top: 20, right: 20, bottom: 30, left: 50 };
  const w = width - pad.left - pad.right;
  const h = height - pad.top - pad.bottom;
  const maxVal = Math.max(...data.map(d => d.impressions), 1);
  const minVal = Math.min(...data.map(d => d.impressions), 0);
  const range = maxVal - minVal || 1;

  const points = data.map((d, i) => {
    const x = pad.left + (i / Math.max(data.length - 1, 1)) * w;
    const y = pad.top + h - ((d.impressions - minVal) / range) * h;
    return `${x},${y}`;
  });

  const areaPath = `M${pad.left},${pad.top + h} L${points.join(" L")} L${pad.left + w},${pad.top + h} Z`;
  const linePath = `M${points.join(" L")}`;

  // Y-axis labels
  const yTicks = 4;
  const yLabels = Array.from({ length: yTicks }, (_, i) => {
    const val = minVal + (range / (yTicks - 1)) * i;
    const y = pad.top + h - ((val - minVal) / range) * h;
    return { val, y };
  });

  // X-axis labels (show ~4 dates)
  const xStep = Math.max(1, Math.floor(data.length / 4));
  const xLabels = data.filter((_, i) => i % xStep === 0 || i === data.length - 1);

  return (
    <div className="card" style={{ marginBottom: "1.5rem", padding: "0.75rem 1rem" }}>
      {label && <h2 style={{ fontSize: "1rem", margin: "0 0 0.5rem" }}>{label}</h2>}
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", maxHeight: height }}>
        {/* Grid lines */}
        {yLabels.map(({ val, y }) => (
          <g key={val}>
            <line x1={pad.left} y1={y} x2={pad.left + w} y2={y} stroke="var(--border)" strokeWidth={0.5} />
            <text x={pad.left - 6} y={y + 4} textAnchor="end" fill="var(--muted)" fontSize={10}>
              {val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val.toFixed(0)}
            </text>
          </g>
        ))}
        {/* Area fill */}
        <path d={areaPath} fill={fillColor} opacity={0.5} />
        {/* Line */}
        <path d={linePath} fill="none" stroke={lineColor} strokeWidth={2} strokeLinejoin="round" />
        {/* Dots */}
        {data.map((d, i) => {
          const x = pad.left + (i / Math.max(data.length - 1, 1)) * w;
          const y = pad.top + h - ((d.impressions - minVal) / range) * h;
          return <circle key={i} cx={x} cy={y} r={2.5} fill={lineColor} />;
        })}
        {/* X-axis labels */}
        {xLabels.map((d) => {
          const i = data.indexOf(d);
          const x = pad.left + (i / Math.max(data.length - 1, 1)) * w;
          return (
            <text key={d.date} x={x} y={height - 6} textAnchor="middle" fill="var(--muted)" fontSize={9}>
              {d.date.slice(5)}
            </text>
          );
        })}
      </svg>
      <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem", fontSize: "0.82rem", color: "var(--muted)" }}>
        <span>▲ 最高 {maxVal.toLocaleString()}</span>
        <span>▼ 最低 {minVal.toLocaleString()}</span>
        <span>日均 {Math.round(data.reduce((s, d) => s + d.impressions, 0) / data.length).toLocaleString()}</span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { workspaceId, siteId, client } = useSiteContext();
  const [data, setData] = useState<ExposureDashboardMetrics | null>(null);
  const [range, setRange] = useState(28);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [attentionItems, setAttentionItems] = useState<AttentionItem[]>([]);
  const [gscTrend, setGscTrend] = useState<Array<{ date: string; impressions: number; clicks: number; position: number }>>([]);
  const [trendLoading, setTrendLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    client.getDashboard(siteId, range)
      .then((d) => { setData(d); setError(null); })
      .catch((err: Error) => setError(parseApiError(err.message).friendly))
      .finally(() => setLoading(false));
  }, [client, siteId, range]);

  useEffect(() => {
    async function loadAttention() {
      const items: AttentionItem[] = [];
      const base = `/app/${workspaceId}/sites/${siteId}`;
      try {
        const runs = await client.listGenerationRuns(siteId);
        const pending = (runs as Array<{ id: string; status: string }>).filter(r => r.status === "needs_review");
        if (pending.length > 0) items.push({ id: "review", label: `${pending.length} 篇內容待審核`, detail: "內容審核有待處理項目", href: `${base}/content-review`, severity: "warning" });
      } catch {}
      try {
        const nodes = await client.listTopicNodes(siteId);
        const gaps = (nodes as Array<{ id: string; status: string }>).filter(n => n.status === "gap");
        if (gaps.length > 0) items.push({ id: "gaps", label: `${gaps.length} 個 Topic 覆蓋缺口`, detail: "曝光地圖有未覆蓋節點", href: `${base}/exposure-map`, severity: "critical" });
      } catch {}
      try {
        const opps = await client.listOpportunities(siteId);
        const openCount = (opps as Array<{ id: string; status?: string }>).filter(o => !o.status || o.status === "open").length;
        if (openCount > 0) items.push({ id: "opps", label: `${openCount} 個開放機會`, detail: "機會佇列有待審核項目", href: `${base}/opportunities`, severity: "info" });
      } catch {}
      try {
        const issues = await client.listTechnicalIssues(siteId);
        const critical = (issues as Array<{ id: string; severity: string }>).filter(i => i.severity === "critical");
        if (critical.length > 0) items.push({ id: "tech", label: `${critical.length} 個 Critical 技術問題`, detail: "需立即處理的 SEO 技術阻擋", href: `${base}/technical-issues`, severity: "critical" });
      } catch {}
      setAttentionItems(items);
    }
    loadAttention();
  }, [client, siteId, workspaceId]);

  // Fetch GSC daily trend
  useEffect(() => {
    async function loadTrend() {
      setTrendLoading(true);
      try {
        const rows = await client.listGscPerformance(siteId, { limit: range });
        const daily = new Map<string, { impressions: number; clicks: number; position: number; count: number }>();
        for (const r of rows as Array<{ date: string; impressions: number; clicks: number; position: number }>) {
          const d = r.date?.slice(0, 10) ?? "";
          if (!d) continue;
          const cur = daily.get(d) ?? { impressions: 0, clicks: 0, position: 0, count: 0 };
          cur.impressions += r.impressions ?? 0;
          cur.clicks += r.clicks ?? 0;
          cur.position += (r.position ?? 0);
          cur.count += 1;
          daily.set(d, cur);
        }
        const trend = Array.from(daily.entries())
          .map(([date, v]) => ({ date, impressions: v.impressions, clicks: v.clicks, position: v.count > 0 ? v.position / v.count : 0 }))
          .sort((a, b) => a.date.localeCompare(b.date));
        setGscTrend(trend);
      } catch {} finally { setTrendLoading(false); }
    }
    loadTrend();
  }, [client, siteId, range]);

  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!data && loading) return <p style={{ color: "var(--muted)" }}>載入儀表板…</p>;
  if (!data) return null;

  const delta = data.impressions_delta_pct;
  const base = `/app/${workspaceId}/sites/${siteId}`;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
        <PageHeader title="曝光儀表板" subtitle="行動導向：需要你的注意力、核心 KPI、Topic Cluster 表現" />
        <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", marginTop: "0.5rem" }}>
          <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>時間範圍</span>
          {RANGE_OPTIONS.map((opt) => (
            <button key={opt.days} type="button" onClick={() => setRange(opt.days)}
              style={{ padding: "0.3rem 0.7rem", borderRadius: 999, border: "1px solid var(--border)", background: range === opt.days ? "var(--accent)" : "var(--surface-2)", color: range === opt.days ? "#ffffff" : "var(--text)", cursor: "pointer", font: "inherit", fontSize: "0.82rem" }}>
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Needs Your Attention */}
      {attentionItems.length > 0 && (
        <div className="card card-warning" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", margin: "0 0 0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            ⚡ 需要你的注意力
            <span style={{ fontSize: "0.82rem", color: "var(--muted)", fontWeight: 400 }}>（點擊直達對應頁面）</span>
          </h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {attentionItems.map(item => {
              const colors: Record<string, { bg: string; border: string; text: string }> = {
                critical: { bg: "var(--danger-soft)", border: "var(--danger)", text: "var(--danger)" },
                warning: { bg: "var(--warning-soft)", border: "var(--warning)", text: "var(--warning)" },
                info: { bg: "var(--accent-soft)", border: "var(--accent)", text: "var(--accent-text)" },
              };
              const c = colors[item.severity];
              return (
                <Link key={item.id} href={item.href}
                  style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.85rem", borderRadius: 8, border: `1px solid ${c.border}`, background: c.bg, color: c.text, fontWeight: 500, fontSize: "0.88rem", textDecoration: "none" }}>
                  {item.label} <span style={{ fontSize: "0.75rem", opacity: 0.7 }}>→</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Core KPIs */}
      <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="card card-primary">
          <div className="kpi-label">{range} 天自然曝光</div>
          <div className="kpi-value">{data.total_impressions.toLocaleString()}</div>
          <div className={delta >= 0 ? "delta-up" : "delta-down"} style={{ fontSize: "0.9rem", marginTop: "0.25rem" }}>{delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}% MoM</div>
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.3rem" }}>來源：Google Search Console</div>
        </div>
        <KpiCard label="查詢覆蓋" value={data.query_coverage_count} note={`本站出現在 ${data.query_coverage_count.toLocaleString()} 個不同搜尋詞`} />
        <KpiCard label="已索引資產" value={data.indexed_asset_count} note="Google 已索引的頁面數" />
      </div>

      {/* GSC Trend Chart */}
      {!trendLoading && gscTrend.length >= 2 && (
        <TrendChart data={gscTrend} label={`${range} 天曝光趨勢（GSC 每日彙總）`} />
      )}

      {/* Quick Actions */}
      <div className="card card-secondary" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", margin: "0 0 0.5rem" }}>快速操作</h2>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <Link href={`${base}/keyword-pyramid`} className="btn btn-primary">關鍵字研究</Link>
          <Link href={`${base}/opportunities`} className="btn">機會佇列</Link>
          <Link href={`${base}/content-review`} className="btn">內容審核</Link>
          <Link href={`${base}/exposure-map`} className="btn">曝光地圖</Link>
          <Link href={`${base}/today`} className="btn">今日工作</Link>
        </div>
      </div>

      {/* Ranking Breakdown */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem", color: "var(--muted)" }}>排名分佈</h2>
        <div className="kpi-grid">
          <div className="card"><div className="kpi-label">Top 3 查詢</div><div className="kpi-value" style={{ color: "var(--success)" }}>{data.top_3_count.toLocaleString()}</div><div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>排名 1–3（高點擊率）</div></div>
          <div className="card"><div className="kpi-label">Top 10 查詢</div><div className="kpi-value">{data.top_10_count.toLocaleString()}</div><div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>排名 4–10（首頁）</div></div>
          <div className="card"><div className="kpi-label">Top 20 查詢</div><div className="kpi-value" style={{ color: "var(--muted)" }}>{data.top_20_count.toLocaleString()}</div><div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>排名 11–20（第二頁）</div></div>
          <div className="card"><div className="kpi-label">SERP 版位達成</div><div className="kpi-value" style={{ color: "var(--accent)" }}>{data.serp_slot_count.toLocaleString()}</div><div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>已確認取得的特殊版位</div></div>
          <div className="card"><div className="kpi-label">AI 引用</div><div className="kpi-value" style={{ color: "var(--accent)" }}>{data.ai_citation_count.toLocaleString()}</div><div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>AI 平台上提及本站 URL</div></div>
        </div>
      </div>

      {/* Action Items */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem", color: "var(--muted)" }}>待處理事項</h2>
        <div className="kpi-grid">
          <Link href={`${base}/opportunities`} style={{ textDecoration: "none" }}><HealthBadge value={data.open_opportunity_count} label="Open 機會" /></Link>
          <Link href={`${base}/technical-issues`} style={{ textDecoration: "none" }}><HealthBadge value={data.critical_blocker_count} label="Critical 技術阻擋" /></Link>
        </div>
      </div>

      {/* Topic Cluster Performance */}
      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
          Topic Cluster 表現
          <span style={{ fontSize: "0.82rem", color: "var(--muted)", marginLeft: "0.5rem" }}>（點擊列可跳轉曝光地圖）</span>
        </h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead><tr><th>主題群</th><th>曝光</th><th>覆蓋分數</th><th>AI 能見度</th><th>狀態</th></tr></thead>
            <tbody>
              {data.topic_cluster_performance.length === 0 ? (
                <tr><td colSpan={5} style={{ color: "var(--muted)" }}>尚無 topic cluster 資料，請完成 GSC sync 後刷新</td></tr>
              ) : (
                (data.topic_cluster_performance as TopicRow[]).sort((a, b) => b.total_impressions - a.total_impressions).map((row) => (
                  <tr key={row.id} style={{ cursor: "pointer" }} onClick={() => window.location.href = `${base}/exposure-map`}>
                    <td style={{ fontWeight: 500, color: "var(--accent-text)" }}>{row.name} →</td>
                    <td>{row.total_impressions.toLocaleString()}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div style={{ width: 60, height: 6, background: "var(--surface-2)", borderRadius: 999, overflow: "hidden" }}>
                          <div style={{ width: `${Math.min(100, row.coverage_score)}%`, height: "100%", background: row.coverage_score > 60 ? "var(--success)" : row.coverage_score > 30 ? "var(--warning)" : "var(--danger)", borderRadius: 999 }} />
                        </div>
                        <span style={{ fontSize: "0.82rem" }}>{row.coverage_score.toFixed(1)}</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div style={{ width: 60, height: 6, background: "var(--surface-2)", borderRadius: 999, overflow: "hidden" }}>
                          <div style={{ width: `${Math.min(100, row.ai_visibility_score)}%`, height: "100%", background: row.ai_visibility_score > 60 ? "var(--success)" : row.ai_visibility_score > 30 ? "var(--warning)" : "var(--danger)", borderRadius: 999 }} />
                        </div>
                        <span style={{ fontSize: "0.82rem" }}>{row.ai_visibility_score.toFixed(1)}</span>
                      </div>
                    </td>
                    <td><span className={`badge ${row.status === "gap" ? "badge-high" : row.status === "cannibalized" ? "badge-critical" : ""}`}>{row.status}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
