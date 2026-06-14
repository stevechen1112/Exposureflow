import { PageHeader } from "@/components/PageHeader";

export default function HelpOnboardingPage() {
  return (
    <>
      <PageHeader title="Onboarding Guide" subtitle="6 步驟完成啟用" />
      <ol style={{ lineHeight: 1.8 }}>
        <li>建立 workspace 與 site</li>
        <li>連接 Google Search Console 並觸發 sync</li>
        <li>檢視 Exposure Opportunities</li>
        <li>核准 decision candidate，檢視 roadmap</li>
        <li>產生第一份報表（PDF / DOCX）</li>
        <li>邀請團隊成員並設定 RBAC</li>
      </ol>
      <p style={{ color: "var(--muted)" }}>
        完整文件見 repo <code>docs/help/onboarding-guide.md</code>。應用內 Onboarding 頁面會自動追蹤各步驟狀態。
      </p>
    </>
  );
}
