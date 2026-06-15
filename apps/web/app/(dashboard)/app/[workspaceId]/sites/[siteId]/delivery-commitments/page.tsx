"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function DeliveryCommitmentsPage() {
  const { siteId, client } = useSiteContext();
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listDeliveryCommitments(siteId).then(setRows).catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="交付承諾" subtitle="產能邊界與每月交付上限" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>期間</th>
              <th>文章上限</th>
              <th>Refresh 上限</th>
              <th>Technical Fix</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={String(r.id)}>
                <td>
                  {String(r.period_start ?? "")} — {String(r.period_end ?? "")}
                </td>
                <td>{String(r.new_content_target ?? r.article_target ?? 0)}</td>
                <td>{String(r.refresh_target ?? 0)}</td>
                <td>{String(r.technical_fix_target ?? 0)}</td>
                <td>{String(r.status ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
