"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { useWorkspaceAuth } from "@/lib/auth-context";
import { canRole } from "@/lib/permissions";

export default function SettingsPage() {
  const params = useParams<{ workspaceId: string }>();
  const { role } = useWorkspaceAuth();
  const base = `/app/${params.workspaceId}/settings`;

  const links = [
    {
      href: `${base}/integrations`,
      label: "整合（GSC、GA4、SERP…）",
      permission: "integration:read",
      desc: "資料源連線與同步狀態",
    },
    {
      href: `${base}/members`,
      label: "成員與 RBAC",
      permission: "member:read",
      desc: "邀請成員、調整角色",
    },
    {
      href: `${base}/billing`,
      label: "計費與方案",
      permission: "billing:read",
      desc: "訂閱、用量與付款",
    },
  ].filter((item) => canRole(role, item.permission));

  return (
    <>
      <PageHeader title="設定" subtitle="依您的角色顯示可管理的項目" />
      {links.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>此角色沒有可用的設定項目。</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {links.map((item) => (
            <li key={item.href} className="card">
              <Link href={item.href} style={{ fontWeight: 600 }}>
                {item.label}
              </Link>
              <p style={{ margin: "0.35rem 0 0", fontSize: "0.85rem", color: "var(--muted)" }}>{item.desc}</p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
