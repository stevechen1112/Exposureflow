"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";

export default function MembersPage() {
  const params = useParams<{ workspaceId: string }>();
  const client = getApiClient(params.workspaceId);
  const [members, setMembers] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listMembers().then(setMembers).catch((err: Error) => setError(err.message));
  }, [client]);

  return (
    <>
      <PageHeader title="成員" subtitle="Workspace RBAC 成員列表" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>名稱</th>
              <th>角色</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={String(m.user_id ?? m.id)}>
                <td>{String(m.email ?? "")}</td>
                <td>{String(m.name ?? "")}</td>
                <td>{String(m.role ?? "")}</td>
                <td>{String(m.status ?? "active")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
