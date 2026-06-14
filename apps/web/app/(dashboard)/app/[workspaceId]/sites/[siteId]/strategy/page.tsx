"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function StrategyPage() {
  const { client } = useSiteContext();
  const [intakes, setIntakes] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listStrategyIntakes().then(setIntakes).catch((err: Error) => setError(err.message));
  }, [client]);

  return (
    <>
      <PageHeader title="策略 Intake" subtitle="Business scope 與審批狀態" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>版本</th>
              <th>狀態</th>
              <th>North Star</th>
              <th>更新時間</th>
            </tr>
          </thead>
          <tbody>
            {intakes.map((row) => (
              <tr key={String(row.id)}>
                <td>{String(row.version ?? row.id)}</td>
                <td>
                  <span className="badge">{String(row.status ?? "")}</span>
                </td>
                <td style={{ maxWidth: 360 }}>{String(row.north_star_summary ?? row.business_summary ?? "")}</td>
                <td>{String(row.updated_at ?? row.created_at ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
