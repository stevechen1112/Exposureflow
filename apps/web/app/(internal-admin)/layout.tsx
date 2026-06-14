"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ensureInternalAdminSession } from "@/lib/internal-api-client";

const NAV = [
  { href: "/internal-admin/launch", label: "Launch Readiness" },
  { href: "/internal-admin/workspaces", label: "Workspaces" },
  { href: "/internal-admin/jobs", label: "Jobs & Sync" },
  { href: "/internal-admin/audit", label: "Audit Logs" },
  { href: "/internal-admin/cs", label: "Customer Success" },
  { href: "/internal-admin/integration-health", label: "Integration Health" },
  { href: "/internal-admin/provider-costs", label: "Provider Costs" },
  { href: "/internal-admin/support", label: "Support Tickets" },
  { href: "/internal-admin/status", label: "Status Page" },
];

export default function InternalAdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ensureInternalAdminSession()
      .then(() => setReady(true))
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) {
    return (
      <main style={{ padding: "2rem" }}>
        <p style={{ color: "var(--danger)" }}>Internal admin session failed: {error}</p>
      </main>
    );
  }

  if (!ready) {
    return (
      <main style={{ padding: "2rem" }}>
        <p style={{ color: "var(--muted)" }}>Loading internal admin…</p>
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
        <div style={{ padding: "0 1.25rem 1rem", fontWeight: 600 }}>ExposureFlow Ops</div>
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
                  color: active ? "var(--text)" : "var(--muted)",
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: "1.5rem 2rem" }}>{children}</main>
    </div>
  );
}
