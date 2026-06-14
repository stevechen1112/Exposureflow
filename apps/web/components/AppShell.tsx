"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ExposureFlowLogo } from "@exposureflow/ui";
import { roleLabel, useWorkspaceAuth } from "@/lib/auth-context";
import { filterNav, siteNavItems, workspaceNavItems } from "@/lib/nav-config";
import { isPlatformSupport, canRole } from "@/lib/permissions";
import { storageKey } from "@/lib/config";

function siteIdFromPath(pathname: string, workspaceId: string): string | undefined {
  const m = pathname.match(new RegExp(`^/app/${workspaceId}/sites/([^/]+)`));
  return m?.[1];
}

function resolveSiteId(pathname: string, workspaceId: string): string | undefined {
  return siteIdFromPath(pathname, workspaceId);
}

export function AppShell({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { loading, user, role } = useWorkspaceAuth();
  const [navSiteId, setNavSiteId] = useState<string | undefined>();

  useEffect(() => {
    const fromPath = resolveSiteId(pathname, workspaceId);
    if (fromPath) {
      setNavSiteId(fromPath);
      return;
    }
    const stored = localStorage.getItem(storageKey("siteId"));
    setNavSiteId(stored ?? undefined);
  }, [pathname, workspaceId]);

  const siteLinks = navSiteId ? filterNav(siteNavItems(workspaceId, navSiteId), role) : [];
  const wsLinks = filterNav(workspaceNavItems(workspaceId), role);

  return (
    <div className="layout-shell">
      <aside className="sidebar">
        <div style={{ marginBottom: "1.25rem" }}>
          <ExposureFlowLogo />
          {!loading && role ? (
            <div style={{ marginTop: "0.65rem", fontSize: "0.78rem", color: "var(--muted)", lineHeight: 1.5 }}>
              <div>{user?.name ?? user?.email}</div>
              <div style={{ color: "var(--accent-text)", fontWeight: 500 }}>{roleLabel(role)}</div>
            </div>
          ) : null}
        </div>
        <nav>
          {siteLinks.length > 0 ? (
            <>
              <div
                style={{
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--muted)",
                  marginBottom: "0.35rem",
                  paddingLeft: "0.75rem",
                }}
              >
                站點分析
              </div>
              {siteLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={pathname === item.href ? "active" : undefined}
                  title={item.description}
                >
                  {item.label}
                </Link>
              ))}
            </>
          ) : !loading && role && canRole(role, "site:read") ? (
            <p style={{ fontSize: "0.82rem", color: "var(--muted)", padding: "0 0.75rem" }}>
              <Link href={`/app/${workspaceId}/onboarding`}>完成 Onboarding</Link> 以建立站點並開始分析。
            </p>
          ) : !loading && role ? (
            <p style={{ fontSize: "0.82rem", color: "var(--muted)", padding: "0 0.75rem" }}>
              您的角色無站點分析權限。
            </p>
          ) : null}
          {wsLinks.length > 0 ? (
            <>
              <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1rem 0" }} />
              <div
                style={{
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--muted)",
                  marginBottom: "0.35rem",
                  paddingLeft: "0.75rem",
                }}
              >
                工作區
              </div>
              {wsLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={pathname === item.href ? "active" : undefined}
                  title={item.description}
                >
                  {item.label}
                </Link>
              ))}
            </>
          ) : null}
          {isPlatformSupport(role) ? (
            <>
              <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1rem 0" }} />
              <Link href="/internal-admin/workspaces" className="active" style={{ fontSize: "0.88rem" }}>
                平台營運後台 →
              </Link>
            </>
          ) : null}
        </nav>
      </aside>
      <div className="content">{children}</div>
    </div>
  );
}
