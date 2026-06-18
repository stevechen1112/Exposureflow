/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function ProviderCostsPage() {
  const client = getInternalApiClient();
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    client
      .internalProviderCosts(days)
      .then(setRows)
      .catch((err: Error) => setError(err.message));
  }, [client, days]);

  return (
    <>
      <PageHeader title="Provider Costs" subtitle="外部 API 成本彙總" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div style={{ marginBottom: "1rem" }}>
        <label>
          Days{" "}
          <input
            type="number"
            min={7}
            max={90}
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          />
        </label>
      </div>
      <section className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Jobs</th>
              <th>Failed</th>
              <th>Cost (cents)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={String(r.provider)}>
                <td>{String(r.provider)}</td>
                <td>{String(r.job_count)}</td>
                <td>{String(r.failed_jobs)}</td>
                <td>{String(r.total_cost_cents)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
