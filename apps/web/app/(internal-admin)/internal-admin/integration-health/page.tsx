"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function IntegrationHealthPage() {
  const client = getInternalApiClient();
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .internalIntegrationHealth()
      .then(setRows)
      .catch((err: Error) => setError(err.message));
  }, [client]);

  return (
    <>
      <PageHeader title="Integration Health" subtitle="各 provider 同步健康度" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <section className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Total</th>
              <th>Healthy</th>
              <th>Failing</th>
              <th>Stale</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={String(r.provider)}>
                <td>{String(r.provider)}</td>
                <td>{String(r.total)}</td>
                <td style={{ color: "var(--success)" }}>{String(r.healthy)}</td>
                <td style={{ color: "var(--danger)" }}>{String(r.failing)}</td>
                <td style={{ color: "var(--warning)" }}>{String(r.stale)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
