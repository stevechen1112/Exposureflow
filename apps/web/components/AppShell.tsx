"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, useCallback, useRef } from "react";
import { ExposureFlowLogo } from "@exposureflow/ui";
import { roleLabel, useWorkspaceAuth } from "@/lib/auth-context";
import { filterNav, siteNavGroups, workspaceNavItems } from "@/lib/nav-config";
import { isPlatformSupport, canRole } from "@/lib/permissions";
import { storageKey } from "@/lib/config";
import { getApiClient } from "@/lib/api-client";
import { WorkspaceSwitcher } from "@/components/WorkspaceSwitcher";
import { SiteSwitcher } from "@/components/SiteSwitcher";

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
  const { loading, user, role, can, workspaces } = useWorkspaceAuth();
  const [navSiteId, setNavSiteId] = useState<string | undefined>();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ label: string; href: string; context: string }>>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [inboxUrgent, setInboxUrgent] = useState<number | null>(null);
  const searchRef = useRef<HTMLDivElement | null>(null);

  // Close search on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearch(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Build search index from nav items
  const searchIndex = useCallback((query: string) => {
    if (!query.trim() || !navSiteId) { setSearchResults([]); setShowSearch(false); return; }
    const q = query.toLowerCase();
    const results: Array<{ label: string; href: string; context: string }> = [];
    const siteGroups = siteNavGroups(workspaceId, navSiteId);
    for (const group of siteGroups) {
      for (const item of group.items) {
        if (item.label.toLowerCase().includes(q) || (item.description && item.description.toLowerCase().includes(q))) {
          results.push({ label: item.label, href: item.href, context: group.label });
        }
      }
    }
    for (const item of workspaceNavItems(workspaceId)) {
      if (item.label.toLowerCase().includes(q) || (item.description && item.description.toLowerCase().includes(q))) {
        results.push({ label: item.label, href: item.href, context: "工作區" });
      }
    }
    setSearchResults(results.slice(0, 8));
    setShowSearch(true);
  }, [workspaceId, navSiteId]);

  useEffect(() => {
    const fromPath = resolveSiteId(pathname, workspaceId);
    if (fromPath) {
      setNavSiteId(fromPath);
      return;
    }
    const stored = localStorage.getItem(storageKey("siteId"));
    setNavSiteId(stored ?? undefined);
  }, [pathname, workspaceId]);

  useEffect(() => {
    if (!role || !canRole(role, "site:read")) {
      setInboxUrgent(null);
      return;
    }
    const client = getApiClient(workspaceId);
    const clientWs = workspaces.filter((w) => w.workspace_type !== "agency_internal").length;
    const useAccountScope = clientWs > 1 || can("agency:read");
    client
      .getConsultantInbox(useAccountScope ? { scope: "account" } : undefined)
      .then((payload) => {
        const summary = payload.summary as { urgent?: number } | undefined;
        setInboxUrgent(Number(summary?.urgent ?? 0));
      })
      .catch(() => setInboxUrgent(null));
  }, [workspaceId, role, pathname, can, workspaces]);

  const siteGroups = navSiteId
    ? siteNavGroups(workspaceId, navSiteId).map((g) => ({
        ...g,
        items: filterNav(g.items, role),
      })).filter((g) => g.items.length > 0)
    : [];
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

        <WorkspaceSwitcher workspaceId={workspaceId} />
        {navSiteId ? <SiteSwitcher workspaceId={workspaceId} siteId={navSiteId} /> : null}

        {/* Global search */}
        <div className="global-search" ref={searchRef}>
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="搜尋頁面…"
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); searchIndex(e.target.value); }}
            onFocus={() => { if (searchQuery.trim()) setShowSearch(true); }}
          />
          {showSearch && searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((r, i) => (
                <Link key={i} href={r.href} className="search-result-item" onClick={() => { setShowSearch(false); setSearchQuery(""); }}>
                  <span className="result-label">{r.label}</span>
                  <span className="result-context"> · {r.context}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
        <nav>
          {siteGroups.length > 0 ? (
            <>
              {siteGroups.map((group) => (
                <div key={group.label} style={{ marginBottom: "0.75rem" }}>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      color: "var(--muted)",
                      marginBottom: "0.25rem",
                      paddingLeft: "0.75rem",
                    }}
                  >
                    {group.label}
                  </div>
                  {group.items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={pathname === item.href ? "active" : undefined}
                      title={item.description}
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              ))}
            </>
          ) : !loading && role && canRole(role, "site:read") ? (
            <p style={{ fontSize: "0.82rem", color: "var(--muted)", padding: "0 0.75rem" }}>
              <Link href={`/app/${workspaceId}/settings/sites`}>建立站點</Link> 以開始分析。
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
                  {item.href.includes("/consultant-inbox") && inboxUrgent != null && inboxUrgent > 0 ? (
                    <span
                      style={{
                        marginLeft: "0.4rem",
                        fontSize: "0.72rem",
                        background: "var(--danger-soft)",
                        color: "var(--danger)",
                        padding: "0.1rem 0.45rem",
                        borderRadius: 999,
                        fontWeight: 600,
                      }}
                    >
                      {inboxUrgent}
                    </span>
                  ) : null}
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
