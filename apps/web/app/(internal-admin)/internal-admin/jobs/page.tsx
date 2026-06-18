/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function InternalJobsPage() {
  const client = getInternalApiClient();
  const [jobs, setJobs] = useState<Array<Record<string, unknown>>>([]);
  const [syncs, setSyncs] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [failingOnly, setFailingOnly] = useState(true);

  useEffect(() => {
    Promise.all([
      client.internalListJobs({ status: undefined }),
      client.internalListSyncStates({ failing_only: failingOnly }),
    ])
      .then(([j, s]) => {
        setJobs(j);
        setSyncs(s);
      })
      .catch((err: Error) => setError(err.message));
  }, [client, failingOnly]);

  return (
    <>
      <PageHeader title="Jobs & Sync" subtitle="Job runs 與 integration sync 狀態" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>Recent job runs</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Status</th>
              <th>Provider</th>
              <th>Cost</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {jobs.slice(0, 50).map((j) => (
              <tr key={String(j.id)}>
                <td>{String(j.job_type)}</td>
                <td>{String(j.status)}</td>
                <td>{String(j.provider ?? "—")}</td>
                <td>{String(j.provider_cost_cents)}</td>
                <td>{String(j.error_message ?? "—").slice(0, 80)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3>Sync states</h3>
          <label>
            <input type="checkbox" checked={failingOnly} onChange={(e) => setFailingOnly(e.target.checked)} />{" "}
            Failing only
          </label>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Last success</th>
              <th>Last error</th>
            </tr>
          </thead>
          <tbody>
            {syncs.map((s) => (
              <tr key={String(s.id)}>
                <td>{String(s.provider)}</td>
                <td>{String(s.last_success_at ?? "—")}</td>
                <td style={{ color: s.last_error ? "var(--danger)" : undefined }}>
                  {String(s.last_error ?? "—").slice(0, 100)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
