"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { RequirePermission } from "@/components/WorkspaceGuard";
import { getApiClient } from "@/lib/api-client";
import { ROLE_LABELS, type WorkspaceRole } from "@/lib/permissions";
import { useWorkspaceAuth } from "@/lib/auth-context";

const ASSIGNABLE_ROLES: WorkspaceRole[] = [
  "admin",
  "strategist",
  "editor",
  "analyst",
  "client_viewer",
  "billing_admin",
];

type MemberRow = {
  user_id: string;
  email: string;
  name: string;
  role: string;
  status: string;
};

export default function MembersPage() {
  const params = useParams<{ workspaceId: string }>();
  const { can } = useWorkspaceAuth();
  const client = getApiClient(params.workspaceId);
  const [members, setMembers] = useState<MemberRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<WorkspaceRole>("editor");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const rows = await client.listMembers();
    setMembers(rows as MemberRow[]);
  }, [client]);

  useEffect(() => {
    load().catch((err: Error) => setError(parseApiError(err.message).friendly));
  }, [load]);

  async function sendInvite(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const inv = await client.createInvitation(inviteEmail.trim(), inviteRole);
      const token = inv.invite_token ? `（dev token: ${String(inv.invite_token).slice(0, 12)}…）` : "";
      setSuccess(`已邀請 ${inviteEmail} 為 ${ROLE_LABELS[inviteRole]} ${token}`);
      setInviteEmail("");
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "邀請失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  async function changeRole(userId: string, role: string) {
    setBusy(true);
    setError(null);
    try {
      await client.updateMemberRole(userId, role);
      setSuccess("角色已更新");
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "更新失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  return (
    <RequirePermission permission="member:read" workspaceId={params.workspaceId}>
      <PageHeader
        title="成員"
        subtitle="工作區 RBAC：檢視成員、調整角色或發送邀請"
      />

      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)" }}>{success}</p> : null}

      {can("invitation:write") ? (
        <form
          className="card"
          onSubmit={sendInvite}
          style={{ marginBottom: "1.5rem", display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "flex-end" }}
        >
          <label style={{ flex: "1 1 200px" }}>
            <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
              邀請 Email
            </span>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@example.com"
              style={{ width: "100%" }}
            />
          </label>
          <label>
            <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
              角色
            </span>
            <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value as WorkspaceRole)}>
              {ASSIGNABLE_ROLES.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            發送邀請
          </button>
        </form>
      ) : null}

      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>名稱</th>
              <th>角色</th>
              <th>狀態</th>
              {can("member:write") ? <th>調整角色</th> : null}
            </tr>
          </thead>
          <tbody>
            {members.length === 0 ? (
              <tr>
                <td colSpan={can("member:write") ? 5 : 4} style={{ color: "var(--muted)" }}>
                  尚無成員
                </td>
              </tr>
            ) : (
              members.map((m) => (
                <tr key={m.user_id}>
                  <td>{m.email}</td>
                  <td>{m.name}</td>
                  <td>{ROLE_LABELS[m.role as WorkspaceRole] ?? m.role}</td>
                  <td>{m.status ?? "active"}</td>
                  {can("member:write") ? (
                    <td>
                      {m.role === "owner" ? (
                        <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>擁有者</span>
                      ) : (
                        <select
                          value={m.role}
                          disabled={busy}
                          onChange={(e) => changeRole(m.user_id, e.target.value)}
                        >
                          {ASSIGNABLE_ROLES.map((r) => (
                            <option key={r} value={r}>
                              {ROLE_LABELS[r]}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                  ) : null}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </RequirePermission>
  );
}
