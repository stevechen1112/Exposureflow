"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function KeywordPyramidPage() {
  const { siteId, client } = useSiteContext();
  const [nodes, setNodes] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listKeywordPyramid(siteId).then(setNodes).catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="關鍵字金字塔" subtitle="Pillar / cluster / long-tail 層級" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>層級</th>
              <th>關鍵字</th>
              <th>意圖</th>
              <th>狀態</th>
              <th>Business Fit</th>
            </tr>
          </thead>
          <tbody>
            {nodes.map((n) => (
              <tr key={String(n.id)}>
                <td>{String(n.tier ?? n.level ?? "")}</td>
                <td>{String(n.keyword ?? n.label ?? "")}</td>
                <td>{String(n.search_intent ?? "")}</td>
                <td>{String(n.approval_status ?? n.status ?? "")}</td>
                <td>{String(n.business_fit_score ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
