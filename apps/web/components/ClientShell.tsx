"use client";

import Link from "next/link";
import { ExposureFlowLogo } from "@exposureflow/ui";
import { roleLabel, useWorkspaceAuth } from "@/lib/auth-context";

export function ClientShell({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: React.ReactNode;
}) {
  const { loading, user, role } = useWorkspaceAuth();

  return (
    <div className="layout-shell">
      <aside className="sidebar" style={{ maxWidth: 260 }}>
        <div style={{ marginBottom: "1.25rem" }}>
          <ExposureFlowLogo />
          {!loading ? (
            <div style={{ marginTop: "0.65rem", fontSize: "0.78rem", color: "var(--muted)", lineHeight: 1.5 }}>
              <div>{user?.name ?? user?.email ?? "客戶"}</div>
              <div style={{ color: "var(--accent-text)", fontWeight: 500 }}>
                {roleLabel(role)} · 客戶入口
              </div>
            </div>
          ) : null}
        </div>
        <nav>
          <Link href={`/client/${workspaceId}`} className="active">
            儀表板
          </Link>
        </nav>
        <p
          style={{
            marginTop: "1.5rem",
            fontSize: "0.78rem",
            color: "var(--muted)",
            lineHeight: 1.5,
            padding: "0 0.75rem",
          }}
        >
          此入口僅顯示月報、Roadmap 待核准與曝光摘要。如需完整分析後台，請聯絡您的策略顧問。
        </p>
      </aside>
      <div className="content">{children}</div>
    </div>
  );
}
