"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function ContentReviewPage() {
  const { siteId, client } = useSiteContext();
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listExecutionJobs(siteId).then(setRuns).catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="內容審核" subtitle="Generation runs 與 publish gate 狀態" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Job 類型</th>
              <th>狀態</th>
              <th>Action</th>
              <th>建立時間</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={String(r.id)}>
                <td>{String(r.job_type ?? "")}</td>
                <td>{String(r.status ?? "")}</td>
                <td>{String(r.action_type ?? "—")}</td>
                <td>{String(r.created_at ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
