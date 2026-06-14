"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function OutcomesPage() {
  const { siteId, client } = useSiteContext();
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .listActionOutcomes(siteId)
      .then(setRows)
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="行動成果" subtitle="已 approve 決策的曝光成效追蹤" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>行動類型</th>
              <th>關鍵字</th>
              <th>預期影響</th>
              <th>Roadmap</th>
              <th>Δ 曝光 7d</th>
              <th>Δ 曝光 28d</th>
              <th>SERP Δ</th>
              <th>AI Citation Δ</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ color: "var(--muted)" }}>
                  尚無已追蹤成果
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={String(r.decision_id)}>
                  <td>{String(r.action_type ?? "")}</td>
                  <td>{String(r.keyword ?? "—")}</td>
                  <td>{Number(r.expected_exposure_impact ?? 0).toFixed(1)}</td>
                  <td>
                    {String(r.roadmap_status ?? "")}
                    {r.week_number != null ? ` · W${String(r.week_number)}` : ""}
                  </td>
                  <td>{String(r.impressions_delta_7d ?? "—")}</td>
                  <td>{String(r.impressions_delta_28d ?? "—")}</td>
                  <td>{String(r.serp_slot_delta ?? "—")}</td>
                  <td>{String(r.ai_citation_delta ?? "—")}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
