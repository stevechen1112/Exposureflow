"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function KnowledgePage() {
  const { siteId, client } = useSiteContext();
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [sources, setSources] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([client.getBrandProfile(siteId), client.listKnowledgeSources(siteId)])
      .then(([p, s]) => {
        setProfile(p);
        setSources(s);
      })
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="知識庫" subtitle="Brand profile 與 knowledge sources" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {profile ? (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>Brand Profile</h2>
          <p>{String(profile.brand_voice_summary ?? profile.summary ?? "—")}</p>
        </div>
      ) : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>來源</th>
              <th>類型</th>
              <th>狀態</th>
              <th>Facts</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={String(s.id)}>
                <td>{String(s.title ?? s.source_url ?? "")}</td>
                <td>{String(s.source_type ?? "")}</td>
                <td>{String(s.approval_status ?? s.status ?? "")}</td>
                <td>{String(s.fact_count ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
