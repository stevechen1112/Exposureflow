/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function InternalSupportPage() {
  const client = getInternalApiClient();
  const [tickets, setTickets] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .internalListSupportTickets()
      .then(setTickets)
      .catch((err: Error) => setError(err.message));
  }, [client]);

  return (
    <>
      <PageHeader title="Support Tickets" subtitle="跨 workspace 工單檢視" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <section className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Subject</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Workspace</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={String(t.id)}>
                <td>{String(t.subject)}</td>
                <td>{String(t.status)}</td>
                <td>{String(t.priority)}</td>
                <td>{String(t.workspace_id)}</td>
                <td>{String(t.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
