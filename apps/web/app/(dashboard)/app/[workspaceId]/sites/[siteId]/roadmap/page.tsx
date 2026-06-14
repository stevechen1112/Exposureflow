"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function RoadmapPage() {
  const { siteId, client } = useSiteContext();
  const [roadmaps, setRoadmaps] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .listRoadmaps(siteId)
      .then(setRoadmaps)
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="Roadmap" subtitle="4 / 8 / 16 週執行路線與項目狀態" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {roadmaps.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>尚無 roadmap，請從 Decision Plane 建立。</p>
      ) : (
        roadmaps.map((rm) => (
          <section key={String(rm.id)} style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem" }}>
              {String(rm.title ?? "Roadmap")} · {String(rm.horizon_weeks)} 週 · {String(rm.status)}
            </h2>
            <div className="table-wrap card" style={{ padding: 0 }}>
              <table>
                <thead>
                  <tr>
                    <th>週次</th>
                    <th>標題</th>
                    <th>狀態</th>
                    <th>負責</th>
                  </tr>
                </thead>
                <tbody>
                  {((rm.items as Array<Record<string, unknown>>) ?? []).map((item) => (
                    <tr key={String(item.id)}>
                      <td>W{String(item.week_number ?? "")}</td>
                      <td>{String(item.title ?? "")}</td>
                      <td>{String(item.status ?? "")}</td>
                      <td>{String(item.owner_user_id ?? "—")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))
      )}
    </>
  );
}
