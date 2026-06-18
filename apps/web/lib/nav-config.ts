import { canRole } from "./permissions";

export type NavItem = {
  href: string;
  label: string;
  permission?: string;
  description?: string;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export function siteNavGroups(workspaceId: string, siteId: string): NavGroup[] {
  const base = `/app/${workspaceId}/sites/${siteId}`;
  return [
    {
      label: "📊 總覽",
      items: [
        { href: `${base}/dashboard`, label: "曝光儀表板", permission: "site:read", description: "行動導向儀表板：待處理事項、KPI、Topic Cluster 表現" },
        { href: `${base}/today`, label: "今日工作", permission: "site:read", description: "今日待處理：審核、gap 節點、進行中任務" },
      ],
    },
    {
      label: "🎯 策略與研究",
      items: [
        { href: `${base}/strategy`, label: "策略 Intake", permission: "site:read", description: "顧問面談後記錄 business scope" },
        { href: `${base}/keyword-pyramid`, label: "關鍵字金字塔", permission: "site:read", description: "Pillar / Cluster / Long-tail 結構與 SERP 評分" },
        { href: `${base}/serp-matrix`, label: "SERP 版位矩陣", permission: "site:read", description: "keyword × slot 版位覆蓋視覺化" },
      ],
    },
    {
      label: "📋 機會與決策",
      items: [
        { href: `${base}/opportunities`, label: "機會佇列", permission: "site:read", description: "審核建議行動，批次 approve / reject / defer" },
        { href: `${base}/roadmap`, label: "執行路線圖", permission: "site:read", description: "4 / 8 / 16 週執行路線與客戶核准" },
        { href: `${base}/delivery-commitments`, label: "交付承諾", permission: "site:read", description: "週期性內容與技術交付目標" },
      ],
    },
    {
      label: "✍️ 內容與發布",
      items: [
        { href: `${base}/content-review`, label: "內容審核", permission: "site:read", description: "4 步驟工作流：選擇機會 → Brief → 生成 → 審核發布" },
        { href: `${base}/knowledge`, label: "知識庫", permission: "site:read", description: "品牌素材、產品事實與合規政策" },
        { href: `${base}/ai-brand`, label: "AI 與品牌能見度", permission: "site:read", description: "AI 引用、品牌情緒監控、品牌實體" },
      ],
    },
    {
      label: "📈 量測與診斷",
      items: [
        { href: `${base}/exposure-map`, label: "曝光地圖", permission: "site:read", description: "Topic Cluster 覆蓋版圖與 gap 分析" },
        { href: `${base}/technical-issues`, label: "技術問題", permission: "site:read", description: "爬蟲阻擋、索引異常、Core Web Vitals" },
        { href: `${base}/outcomes`, label: "行動成果", permission: "site:read", description: "已執行行動的曝光變化追蹤" },
      ],
    },
  ];
}

/** @deprecated Use siteNavGroups for grouped navigation. Kept for backward compat. */
export function siteNavItems(workspaceId: string, siteId: string): NavItem[] {
  return siteNavGroups(workspaceId, siteId).flatMap((g) => g.items);
}

export function workspaceNavItems(workspaceId: string): NavItem[] {
  return [
    {
      href: `/app/${workspaceId}/consultant-inbox`,
      label: "顧問工作台",
      permission: "site:read",
      description: "跨站點／跨客戶待辦彙總：技術問題、審核、決策、索引修復",
    },
    {
      href: `/app/${workspaceId}/onboarding`,
      label: "Onboarding",
      permission: "site:read",
      description: "完成站點與資料源設定",
    },
    {
      href: `/app/${workspaceId}/settings/sites`,
      label: "站點",
      permission: "site:read",
      description: "管理客戶網站 domain 與基本資料",
    },
    {
      href: `/app/${workspaceId}/settings`,
      label: "設定",
      permission: "workspace:read",
    },
    {
      href: `/app/${workspaceId}/settings/integrations`,
      label: "GSC 連線",
      permission: "integration:read",
      description: "Google Search Console 授權與同步",
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
      label: "多站總覽",
      permission: "agency:read",
      description: "跨客戶待辦與 KPI；建立新客戶工作區",
    },
  ];
}

export function filterNav(items: NavItem[], role: string | undefined): NavItem[] {
  return items.filter((item) => !item.permission || canRole(role, item.permission));
}
