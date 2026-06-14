import { canRole } from "./permissions";

export type NavItem = {
  href: string;
  label: string;
  permission?: string;
  description?: string;
};

export function siteNavItems(workspaceId: string, siteId: string): NavItem[] {
  const base = `/app/${workspaceId}/sites/${siteId}`;
  return [
    { href: `${base}/dashboard`, label: "曝光儀表板", permission: "site:read" },
    { href: `${base}/opportunities`, label: "機會佇列", permission: "site:read" },
    { href: `${base}/serp-matrix`, label: "SERP 矩陣", permission: "site:read" },
    { href: `${base}/ai-visibility`, label: "AI 能見度", permission: "site:read" },
    { href: `${base}/exposure-map`, label: "曝光地圖", permission: "site:read" },
    { href: `${base}/technical-issues`, label: "技術問題", permission: "site:read" },
    { href: `${base}/outcomes`, label: "行動成果", permission: "site:read" },
    { href: `${base}/roadmap`, label: "Roadmap", permission: "site:read" },
    { href: `${base}/strategy`, label: "策略 Intake", permission: "site:read" },
    { href: `${base}/keyword-pyramid`, label: "關鍵字金字塔", permission: "site:read" },
    { href: `${base}/delivery-commitments`, label: "交付承諾", permission: "site:read" },
    { href: `${base}/knowledge`, label: "知識庫", permission: "site:read" },
    { href: `${base}/content-review`, label: "內容審核", permission: "site:read" },
    { href: `${base}/brand`, label: "品牌實體", permission: "site:read" },
    { href: `${base}/serpo`, label: "SERPO", permission: "site:read" },
  ];
}

export function workspaceNavItems(workspaceId: string): NavItem[] {
  return [
    {
      href: `/app/${workspaceId}/onboarding`,
      label: "Onboarding",
      permission: "site:read",
      description: "完成站點與資料源設定",
    },
    {
      href: `/app/${workspaceId}/settings`,
      label: "設定",
      permission: "workspace:read",
    },
    {
      href: `/app/${workspaceId}/settings/integrations`,
      label: "整合",
      permission: "integration:read",
    },
    {
      href: `/app/${workspaceId}/settings/members`,
      label: "成員",
      permission: "member:read",
    },
    {
      href: `/app/${workspaceId}/settings/billing`,
      label: "計費",
      permission: "billing:read",
    },
    {
      href: `/app/${workspaceId}/agency`,
      label: "Agency 總覽",
      permission: "agency:read",
    },
  ];
}

export function filterNav(items: NavItem[], role: string | undefined): NavItem[] {
  return items.filter((item) => !item.permission || canRole(role, item.permission));
}
