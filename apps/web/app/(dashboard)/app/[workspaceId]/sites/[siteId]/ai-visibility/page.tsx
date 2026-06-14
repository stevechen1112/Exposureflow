"use client";

import { Fragment, useEffect, useState } from "react";
import type { AiVisibilityDashboard } from "@exposureflow/shared-types";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function AiVisibilityPage() {
  const { siteId, client } = useSiteContext();
  const [dash, setDash] = useState<AiVisibilityDashboard | null>(null);
  const [probeSets, setProbeSets] = useState<Array<Record<string, unknown>>>([]);
  const [citations, setCitations] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      client.getAiDashboard(siteId),
      client.listProbeSets(siteId),
      client.listCitations(siteId),
    ])
      .then(([d, ps, c]) => {
        setDash(d);
        setProbeSets(ps);
        setCitations(c);
      })
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!dash) return <p style={{ color: "var(--muted)" }}>載入 AI 能見度…</p>;

  const serpo = dash.serpo_summary ?? {};

  return (
    <>
      <PageHeader title="AI 能見度" subtitle="Probe、citation、品牌提及與 SERPO 情緒摘要" />
      <div className="kpi-grid">
        <KpiCard label="Probe Sets" value={dash.probe_set_count} />
        <KpiCard label="Probe Runs" value={dash.probe_run_count} />
        <KpiCard label="Citations" value={dash.citation_count} />
        <KpiCard label="品牌提及" value={dash.brand_mention_count} />
        <KpiCard label="競品提及" value={dash.competitor_mention_count} />
        <KpiCard label="SERPO 正面" value={Number(serpo.positive ?? 0)} />
        <KpiCard label="SERPO 負面" value={Number(serpo.negative ?? 0)} />
      </div>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontSize: "1.1rem" }}>Prompt Sets</h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>名稱</th>
                <th>狀態</th>
                <th>Probe 數</th>
              </tr>
            </thead>
            <tbody>
              {probeSets.length === 0 ? (
                <tr>
                  <td colSpan={3} style={{ color: "var(--muted)" }}>
                    尚無 probe set
                  </td>
                </tr>
              ) : (
                probeSets.map((p) => (
                  <tr key={String(p.id)}>
                    <td>{String(p.name ?? "")}</td>
                    <td>{String(p.status ?? "")}</td>
                    <td>{String(p.probe_count ?? 0)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontSize: "1.1rem" }}>Citation 歷史</h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Surface</th>
                <th>URL</th>
                <th>自有站</th>
                <th>競品</th>
                <th>時間</th>
              </tr>
            </thead>
            <tbody>
              {(citations.length ? citations : dash.recent_citations).map((c, i) => (
                <tr key={String(c.id ?? i)}>
                  <td>{String(c.surface ?? "")}</td>
                  <td style={{ maxWidth: 240, wordBreak: "break-all" }}>{String(c.cited_url ?? "")}</td>
                  <td>{c.is_own_site ? "✓" : "—"}</td>
                  <td>{c.is_competitor ? "✓" : "—"}</td>
                  <td>{String(c.captured_at ?? "")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
