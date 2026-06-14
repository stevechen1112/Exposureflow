"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function SerpoPage() {
  const { siteId, client } = useSiteContext();
  const [records, setRecords] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listSerpoRecords(siteId).then(setRecords).catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="SERPO" subtitle="Search engine result page opinion 與情緒分布" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>關鍵字</th>
              <th>正面</th>
              <th>中性</th>
              <th>負面</th>
              <th>錯誤資訊</th>
              <th>擷取時間</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={String(r.id)}>
                <td>{String(r.keyword ?? "")}</td>
                <td>{String(r.first_page_positive_count ?? 0)}</td>
                <td>{String(r.first_page_neutral_count ?? 0)}</td>
                <td>{String(r.first_page_negative_count ?? 0)}</td>
                <td>{String(r.first_page_wrong_info_count ?? 0)}</td>
                <td>{String(r.captured_at ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
