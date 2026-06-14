import { test, expect, type Page, type Response } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

const OUT_DIR = path.join(process.cwd(), "e2e-artifacts", "ui-audit");
const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://127.0.0.1:8000";

type PageResult = {
  name: string;
  path: string;
  status: "ok" | "warn" | "fail";
  notes: string[];
  consoleErrors: string[];
  failedRequests: string[];
  screenshot: string;
};

const MARKETING_ROUTES = [
  { name: "Marketing 首頁", path: "/" },
  { name: "Pricing", path: "/pricing" },
  { name: "Help", path: "/help" },
  { name: "Help Onboarding", path: "/help/onboarding" },
  { name: "Help Integrations", path: "/help/integrations" },
  { name: "Help API", path: "/help/api" },
  { name: "Security", path: "/security" },
  { name: "Status", path: "/status" },
  { name: "Terms", path: "/terms" },
  { name: "Privacy", path: "/privacy" },
  { name: "DPA", path: "/dpa" },
  { name: "App Entry", path: "/app-entry" },
];

const INTERNAL_ADMIN_ROUTES = [
  { name: "Internal Launch", path: "/internal-admin/launch" },
  { name: "Internal Workspaces", path: "/internal-admin/workspaces" },
  { name: "Internal Jobs", path: "/internal-admin/jobs" },
  { name: "Internal Audit", path: "/internal-admin/audit" },
  { name: "Internal CS", path: "/internal-admin/cs" },
  { name: "Internal Integration Health", path: "/internal-admin/integration-health" },
  { name: "Internal Provider Costs", path: "/internal-admin/provider-costs" },
  { name: "Internal Support", path: "/internal-admin/support" },
  { name: "Internal Status", path: "/internal-admin/status" },
];

function slug(name: string) {
  return name.replace(/[^\w\u4e00-\u9fff]+/g, "-").replace(/^-|-$/g, "").slice(0, 80);
}

async function attachListeners(page: Page) {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const text = msg.text();
      if (text.includes("Download the React DevTools")) return;
      consoleErrors.push(text.slice(0, 300));
    }
  });

  page.on("response", (resp: Response) => {
    const url = resp.url();
    if (resp.status() >= 400 && !url.includes("favicon")) {
      failedRequests.push(`${resp.status()} ${url.slice(0, 200)}`);
    }
  });

  return { consoleErrors, failedRequests };
}

async function auditPage(
  page: Page,
  name: string,
  urlPath: string,
  opts?: { waitMs?: number; expectSelector?: string },
): Promise<PageResult> {
  const { consoleErrors, failedRequests } = await attachListeners(page);
  const notes: string[] = [];

  await page.goto(urlPath, { waitUntil: "networkidle", timeout: 45_000 });
  if (opts?.waitMs) await page.waitForTimeout(opts.waitMs);

  const title = await page.title();
  if (!title || title === "") notes.push("頁面 title 為空");

  const bodyText = await page.locator("body").innerText();
  if (/ExposureFlow API \d{3}/.test(bodyText)) notes.push("頁面顯示原始 API 錯誤 JSON");
  if (/PERMISSION_DENIED|Platform admin access required/.test(bodyText)) {
    notes.push("權限不足（預期行為或需 platform admin）");
  }
  if (/無法連線 API|Session bootstrap failed|Internal admin session failed/.test(bodyText)) {
    notes.push("Session / API 連線失敗");
  }
  if (/Site not found|site_id=null|422/.test(bodyText)) notes.push("站點 ID 無效或 API 422");

  const dangerEls = page.locator('[style*="var(--danger)"], .badge-critical');
  const dangerCount = await dangerEls.count();
  if (dangerCount > 0) {
    const snippets: string[] = [];
    for (let i = 0; i < Math.min(dangerCount, 3); i++) {
      const t = (await dangerEls.nth(i).innerText()).trim();
      if (t && !snippets.includes(t)) snippets.push(t.slice(0, 120));
    }
    if (snippets.length) notes.push(`紅色錯誤/警告文字：${snippets.join(" | ")}`);
  }

  if (opts?.expectSelector) {
    const visible = await page.locator(opts.expectSelector).first().isVisible().catch(() => false);
    if (!visible) notes.push(`缺少預期元素：${opts.expectSelector}`);
  }

  const uniqueFailed = [...new Set(failedRequests)].slice(0, 8);
  const uniqueConsole = [...new Set(consoleErrors)].slice(0, 8);

  let status: PageResult["status"] = "ok";
  if (
    notes.some((n) => n.includes("失敗") || n.includes("422") || n.includes("API 錯誤")) ||
    uniqueFailed.some((r) => r.startsWith("5"))
  ) {
    status = "fail";
  } else if (notes.length > 0 || uniqueFailed.length > 0 || uniqueConsole.length > 0) {
    status = "warn";
  }

  const shotPath = path.join(OUT_DIR, "screenshots", `${slug(name)}.png`);
  await page.screenshot({ path: shotPath, fullPage: true });

  return {
    name,
    path: urlPath,
    status,
    notes,
    consoleErrors: uniqueConsole,
    failedRequests: uniqueFailed,
    screenshot: shotPath,
  };
}

async function bootstrapAppSession(page: Page): Promise<{ workspaceId: string; siteId: string } | null> {
  await page.goto("/app-entry", { waitUntil: "networkidle", timeout: 45_000 });
  await page.waitForTimeout(2500);

  let url = page.url();
  const wsMatch = url.match(/\/app\/([0-9a-f-]{36})/i);
  let siteMatch = url.match(/\/sites\/([0-9a-f-]{36})/i);

  if (!wsMatch) {
    const tokenResp = await page.request.post(`${API_BASE}/api/v1/auth/dev-token`, {
      data: { email: "playwright-audit@example.com", name: "Playwright Audit" },
    });
    if (!tokenResp.ok()) return null;
    const { access_token } = (await tokenResp.json()) as { access_token: string };

    const wsResp = await page.request.get(`${API_BASE}/api/v1/workspaces`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    const workspaces = (await wsResp.json()) as Array<{ id: string }>;
    const workspaceId = workspaces[0]?.id;
    if (!workspaceId) return null;

    const sitesResp = await page.request.get(`${API_BASE}/api/v1/sites`, {
      headers: {
        Authorization: `Bearer ${access_token}`,
        "X-Workspace-Id": workspaceId,
      },
    });
    const sites = (await sitesResp.json()) as Array<{ id: string }>;
    const siteId = sites[0]?.id;
    if (!siteId) {
      await page.goto(`/app/${workspaceId}/onboarding`, { waitUntil: "networkidle" });
      return { workspaceId, siteId: "" };
    }

    await page.goto(`/app/${workspaceId}/sites/${siteId}/dashboard`, { waitUntil: "networkidle" });
    url = page.url();
    siteMatch = url.match(/\/sites\/([0-9a-f-]{36})/i);
    return { workspaceId, siteId: siteMatch?.[1] ?? siteId };
  }

  return {
    workspaceId: wsMatch[1],
    siteId: siteMatch?.[1] ?? "",
  };
}

function buildDashboardRoutes(workspaceId: string, siteId: string) {
  const base = `/app/${workspaceId}/sites/${siteId}`;
  return [
    { name: "曝光儀表板", path: `${base}/dashboard` },
    { name: "機會佇列", path: `${base}/opportunities` },
    { name: "SERP 矩陣", path: `${base}/serp-matrix` },
    { name: "AI 能見度", path: `${base}/ai-visibility` },
    { name: "曝光地圖", path: `${base}/exposure-map` },
    { name: "技術問題", path: `${base}/technical-issues` },
    { name: "行動成果", path: `${base}/outcomes` },
    { name: "Roadmap", path: `${base}/roadmap` },
    { name: "策略 Intake", path: `${base}/strategy` },
    { name: "關鍵字金字塔", path: `${base}/keyword-pyramid` },
    { name: "交付承諾", path: `${base}/delivery-commitments` },
    { name: "知識庫", path: `${base}/knowledge` },
    { name: "內容審核", path: `${base}/content-review` },
    { name: "品牌實體", path: `${base}/brand` },
    { name: "SERPO", path: `${base}/serpo` },
    { name: "Onboarding", path: `/app/${workspaceId}/onboarding` },
    { name: "設定", path: `/app/${workspaceId}/settings` },
    { name: "整合", path: `/app/${workspaceId}/settings/integrations` },
    { name: "成員", path: `/app/${workspaceId}/settings/members` },
    { name: "計費", path: `/app/${workspaceId}/settings/billing` },
    { name: "Agency 總覽", path: `/app/${workspaceId}/agency` },
  ];
}

function writeReport(results: PageResult[]) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const jsonPath = path.join(OUT_DIR, "report.json");
  fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));

  const lines: string[] = [
    "# ExposureFlow UI/UX Playwright 巡檢報告",
    "",
    `生成時間：${new Date().toISOString()}`,
    "",
    "| 狀態 | 頁面 | 路徑 | 備註 |",
    "|------|------|------|------|",
  ];

  for (const r of results) {
    const icon = r.status === "ok" ? "✅" : r.status === "warn" ? "⚠️" : "❌";
    const note = [
      ...r.notes,
      ...r.failedRequests.map((f) => `HTTP: ${f}`),
      ...r.consoleErrors.map((c) => `Console: ${c}`),
    ]
      .join("; ")
      .slice(0, 200);
    lines.push(`| ${icon} | ${r.name} | \`${r.path}\` | ${note || "—"} |`);
  }

  const failCount = results.filter((r) => r.status === "fail").length;
  const warnCount = results.filter((r) => r.status === "warn").length;
  lines.push("", "## 摘要", "", `- 共 ${results.length} 頁`, `- ❌ 失敗 ${failCount}`, `- ⚠️ 警告 ${warnCount}`, `- ✅ 正常 ${results.length - failCount - warnCount}`);
  lines.push("", "截圖目錄：`apps/web/e2e-artifacts/ui-audit/screenshots/`");

  const mdPath = path.join(OUT_DIR, "report.md");
  fs.writeFileSync(mdPath, lines.join("\n"));
}

test.describe("UI/UX full site audit", () => {
  test("audit all marketing + app menus + internal admin", async ({ page }) => {
    fs.mkdirSync(path.join(OUT_DIR, "screenshots"), { recursive: true });
    const results: PageResult[] = [];

    for (const route of MARKETING_ROUTES) {
      results.push(await auditPage(page, route.name, route.path, { waitMs: 800 }));
    }

    const session = await bootstrapAppSession(page);
    expect(session, "dev session 應能建立 workspace").toBeTruthy();
    const { workspaceId, siteId } = session!;

    if (siteId) {
      for (const route of buildDashboardRoutes(workspaceId, siteId)) {
        results.push(await auditPage(page, route.name, route.path, { waitMs: 1200 }));
      }
    } else {
      results.push(
        await auditPage(page, "Onboarding（無 site）", `/app/${workspaceId}/onboarding`, {
          waitMs: 1200,
        }),
      );
    }

    for (const route of INTERNAL_ADMIN_ROUTES) {
      results.push(await auditPage(page, route.name, route.path, { waitMs: 1200 }));
    }

    writeReport(results);

    const fails = results.filter((r) => r.status === "fail");
    expect(
      fails,
      `UI audit 有 ${fails.length} 頁 fail，詳見 e2e-artifacts/ui-audit/report.md`,
    ).toHaveLength(0);
  });
});
