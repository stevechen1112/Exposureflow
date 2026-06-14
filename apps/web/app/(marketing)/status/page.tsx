"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { API_BASE_URL } from "@/lib/config";

type Incident = {
  id: string;
  title: string;
  summary: string;
  status: string;
  severity: string;
  started_at: string;
};

export default function PublicStatusPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [readiness, setReadiness] = useState<{ overall: string; passed: number; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/v1/status`).then((r) => r.json()),
      fetch(`${API_BASE_URL}/api/v1/launch/readiness`).then((r) => r.json()),
    ])
      .then(([status, launch]) => {
        setIncidents(status as Incident[]);
        setReadiness({ overall: launch.overall, passed: launch.passed, total: launch.total });
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <>
      <PageHeader title="System Status" subtitle="服務健康與公開 incident" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {readiness ? (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Platform readiness</h3>
          <p>
            {readiness.overall === "ready" ? (
              <span style={{ color: "var(--success)" }}>● All systems operational</span>
            ) : (
              <span style={{ color: "var(--warning)" }}>● Some checks pending</span>
            )}{" "}
            — {readiness.passed}/{readiness.total} checks passed
          </p>
        </div>
      ) : null}

      <section className="card">
        <h3>Incidents</h3>
        {incidents.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>No public incidents.</p>
        ) : (
          incidents.map((i) => (
            <div key={i.id} style={{ marginBottom: "1rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border)" }}>
              <strong>{i.title}</strong> · {i.status} · {i.severity}
              <p style={{ color: "var(--muted)", margin: "0.35rem 0 0" }}>{i.summary}</p>
            </div>
          ))
        )}
      </section>
    </>
  );
}
