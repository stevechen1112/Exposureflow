"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ForbiddenState, parseApiError } from "@/components/ForbiddenState";
import { createClient } from "@exposureflow/sdk";
import { API_BASE_URL, storageKey } from "@/lib/config";
import { isPlatformSupport } from "@/lib/permissions";

const NAV = [
  { href: "/internal-admin/launch", label: "Launch Readiness" },
  { href: "/internal-admin/workspaces", label: "Workspaces" },
  { href: "/internal-admin/jobs", label: "Jobs & Sync" },
  { href: "/internal-admin/audit", label: "Audit Logs" },
  { href: "/internal-admin/cs", label: "Customer Success" },
  { href: "/internal-admin/integration-health", label: "Integration Health" },
  { href: "/internal-admin/ops-maintenance", label: "維護工程師" },
  { href: "/internal-admin/provider-costs", label: "Provider Costs" },
  { href: "/internal-admin/support", label: "Support Tickets" },
  { href: "/internal-admin/status", label: "Status Page" },
];

export default function InternalAdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem(storageKey("token"));
    if (!token) {
      setError("請先登入，或從 /dev/login 以「平台支援」角色登入。");
      return;
    }
    const client = createClient({ baseUrl: API_BASE_URL, token });
    client
      .getMe()
      .then((me) => {
        const role = (me.workspaces as Array<{ role: string }>)[0]?.role;
        if (!isPlatformSupport(role)) {
          setAuthorized(false);
        } else {
          setAuthorized(true);
        }
        setReady(true);
      })
      .catch((err: Error) => {
        setError(parseApiError(err.message).friendly);
        setReady(true);
      });
  }, []);

  if (!ready) {
    return (
      <main style={{ padding: "2rem" }}>
        <p style={{ color: "var(--muted)" }}>驗證平台權限…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main style={{ padding: "2rem" }}>
        <ForbiddenState title="無法進入平台後台" message={error} homeHref="/app-entry" homeLabel="返回登入" />
      </main>
    );
  }

  if (!authorized) {
    return (
      <main style={{ padding: "2rem" }}>
        <ForbiddenState
          title="此區域僅限平台支援人員"
          message="您目前的工作區角色無法存取 Internal Admin。請從 /dev/login 以 support@example.com（平台支援）登入。"
          homeHref="/dev/login"
          homeLabel="開發者角色切換"
        />
      </main>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 240,
          borderRight: "1px solid var(--border)",
          background: "var(--surface)",
          padding: "1.25rem 0",
        }}
      >
        <div style={{ padding: "0 1.25rem 1rem" }}>
          <div style={{ fontWeight: 600 }}>ExposureFlow Ops</div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.25rem" }}>平台支援後台</div>
        </div>
        <nav>
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "block",
                  padding: "0.5rem 1.25rem",
                  background: active ? "var(--accent-soft)" : "transparent",
                  color: active ? "var(--accent-text)" : "var(--muted)",
                  fontWeight: active ? 500 : 400,
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div style={{ padding: "1rem 1.25rem 0", fontSize: "0.78rem" }}>
          <Link href="/dev/login">← 切換角色</Link>
        </div>
      </aside>
      <main style={{ flex: 1, padding: "1.5rem 2rem" }}>{children}</main>
    </div>
  );
}
