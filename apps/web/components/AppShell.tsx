"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ExposureFlowLogo } from "@exposureflow/ui";

type NavItem = { href: string; label: string };

function navItems(workspaceId: string, siteId: string): NavItem[] {
  const base = `/app/${workspaceId}/sites/${siteId}`;
  return [
    { href: `${base}/dashboard`, label: "曝光儀表板" },
    { href: `${base}/opportunities`, label: "機會佇列" },
    { href: `${base}/serp-matrix`, label: "SERP 矩陣" },
    { href: `${base}/ai-visibility`, label: "AI 能見度" },
    { href: `${base}/exposure-map`, label: "曝光地圖" },
    { href: `${base}/technical-issues`, label: "技術問題" },
    { href: `${base}/outcomes`, label: "行動成果" },
    { href: `${base}/roadmap`, label: "Roadmap" },
    { href: `${base}/strategy`, label: "策略 Intake" },
    { href: `${base}/keyword-pyramid`, label: "關鍵字金字塔" },
    { href: `${base}/delivery-commitments`, label: "交付承諾" },
    { href: `${base}/knowledge`, label: "知識庫" },
    { href: `${base}/content-review`, label: "內容審核" },
    { href: `${base}/brand`, label: "品牌實體" },
    { href: `${base}/serpo`, label: "SERPO" },
  ];
}

function workspaceNav(workspaceId: string): NavItem[] {
  return [
    { href: `/app/${workspaceId}/onboarding`, label: "Onboarding" },
    { href: `/app/${workspaceId}/settings`, label: "設定" },
    { href: `/app/${workspaceId}/settings/integrations`, label: "整合" },
    { href: `/app/${workspaceId}/settings/members`, label: "成員" },
    { href: `/app/${workspaceId}/settings/billing`, label: "計費" },
    { href: `/app/${workspaceId}/agency`, label: "Agency 總覽" },
  ];
}

export function AppShell({
  workspaceId,
  siteId,
  children,
}: {
  workspaceId: string;
  siteId?: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const siteLinks = siteId ? navItems(workspaceId, siteId) : [];
  const wsLinks = workspaceNav(workspaceId);

  return (
    <div className="layout-shell">
      <aside className="sidebar">
        <div style={{ marginBottom: "1.5rem" }}>
          <ExposureFlowLogo />
        </div>
        <nav>
          {siteLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "active" : undefined}
            >
              {item.label}
            </Link>
          ))}
          <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "1rem 0" }} />
          {wsLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "active" : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="content">{children}</div>
    </div>
  );
}
