"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ensureDevSession } from "@/lib/api-client";
import { DEV_AUTH_ENABLED } from "@/lib/config";
import { ROLE_LABELS, type WorkspaceRole, resolveEntryPath } from "@/lib/permissions";

const DEV_PERSONAS: Array<{
  role: WorkspaceRole;
  email: string;
  name: string;
  blurb: string;
}> = [
  { role: "owner", email: "owner@example.com", name: "Owner", blurb: "完整權限，工作區擁有者" },
  { role: "admin", email: "admin@example.com", name: "Admin", blurb: "管理成員、整合與站點" },
  { role: "strategist", email: "strategist@example.com", name: "Strategist", blurb: "策略規劃、機會核准、內容審核" },
  { role: "editor", email: "editor@example.com", name: "Editor", blurb: "內容編輯與審核，無整合管理" },
  { role: "analyst", email: "analyst@example.com", name: "Analyst", blurb: "唯讀分析，無核准操作" },
  { role: "client_viewer", email: "client@example.com", name: "Client", blurb: "客戶入口：月報、Roadmap 核准" },
  { role: "billing_admin", email: "billing@example.com", name: "Billing", blurb: "僅計費與方案管理" },
  { role: "support_admin", email: "support@example.com", name: "Support", blurb: "平台營運後台" },
];

export default function AppEntryPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  if (!DEV_AUTH_ENABLED) {
    return (
      <div className="card" style={{ margin: "2rem auto", maxWidth: 480 }}>
        <p style={{ color: "var(--danger)" }}>正式環境請使用 Clerk 登入（尚未在此頁嵌入）。</p>
      </div>
    );
  }

  async function enter(persona: (typeof DEV_PERSONAS)[number]) {
    setBusy(persona.role);
    setError(null);
    try {
      const { workspaceId, siteId, role } = await ensureDevSession(
        persona.email,
        persona.name,
        persona.role,
      );
      if (!workspaceId) {
        setError("dev session 未建立 workspace，請確認 API 已啟動");
        return;
      }
      router.replace(resolveEntryPath(workspaceId, role ?? persona.role, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "登入失敗");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main style={{ maxWidth: 880, margin: "2rem auto", padding: "0 1rem" }}>
      <header style={{ marginBottom: "1.75rem", textAlign: "center" }}>
        <h1 className="page-title">選擇角色進入 ExposureFlow</h1>
        <p className="page-subtitle">
          本地開發模式：依 RBAC 角色體驗不同後台與權限邊界
        </p>
      </header>

      {error ? (
        <p style={{ color: "var(--danger)", textAlign: "center", marginBottom: "1rem" }}>{error}</p>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {DEV_PERSONAS.map((p) => (
          <button
            key={p.role}
            type="button"
            className="card"
            disabled={busy !== null}
            onClick={() => enter(p)}
            style={{
              textAlign: "left",
              cursor: busy ? "wait" : "pointer",
              border: busy === p.role ? "2px solid var(--accent)" : undefined,
              opacity: busy && busy !== p.role ? 0.6 : 1,
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{ROLE_LABELS[p.role]}</div>
            <div style={{ fontSize: "0.82rem", color: "var(--muted)", lineHeight: 1.5 }}>{p.blurb}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--accent-text)", marginTop: "0.5rem" }}>
              {busy === p.role ? "進入中…" : `${p.email} →`}
            </div>
          </button>
        ))}
      </div>
    </main>
  );
}
