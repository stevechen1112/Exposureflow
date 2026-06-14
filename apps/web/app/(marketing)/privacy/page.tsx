import { PageHeader } from "@/components/PageHeader";

export default function PrivacyPage() {
  return (
    <>
      <PageHeader title="Privacy Policy" subtitle="最後更新：2026-06-14" />
      <div className="card" style={{ lineHeight: 1.7 }}>
        <p>ExposureFlow 處理帳號資料、網站分析資料與您上傳的 knowledge 內容以提供服務。</p>
        <h3>收集項目</h3>
        <ul>
          <li>帳號：email、name（Clerk / auth provider）</li>
          <li>整合：GSC/GA4 等 API 回傳之效能資料</li>
          <li>使用：audit log、usage events、job metadata</li>
        </ul>
        <h3>您的權利</h3>
        <p>可透過 Settings → Security 請求 data export。刪除帳號請聯繫 support。</p>
        <h3>子處理者</h3>
        <p>Stripe（付款）、雲端基礎設施與 observability 供應商。Enterprise 可索取 DPA。</p>
      </div>
    </>
  );
}
