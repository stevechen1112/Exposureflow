import { PageHeader } from "@/components/PageHeader";

export default function HelpIntegrationsPage() {
  return (
    <>
      <PageHeader title="Integration Setup" subtitle="資料源連接指南" />
      <section className="card" style={{ marginBottom: "1rem" }}>
        <h3>Google Search Console</h3>
        <p>OAuth 或 Service Account。Sync 後 opportunity 與 dashboard 會更新。</p>
      </section>
      <section className="card" style={{ marginBottom: "1rem" }}>
        <h3>GA4 / Bing / Tech SEO</h3>
        <p>Settings → Integrations 新增 credential 後觸發對應 job。</p>
      </section>
      <section className="card">
        <h3>SERP</h3>
        <p>設定 SERPER_API_KEY 或 SERPAPI_API_KEY 環境變數。</p>
      </section>
    </>
  );
}
