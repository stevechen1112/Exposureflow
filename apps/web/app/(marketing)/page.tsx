import Link from "next/link";

export default function MarketingHomePage() {
  return (
    <>
      <section style={{ textAlign: "center", padding: "3rem 0 2rem" }}>
        <h1 className="page-title" style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>
          自然曝光最大化平台
        </h1>
        <p className="page-subtitle" style={{ maxWidth: 560, margin: "0 auto 2rem" }}>
          ExposureFlow 協助 B2B 團隊從 GSC、SERP、AI 可見性資料中找出曝光機會，核准決策、執行內容並追蹤成果。
        </p>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
          <Link href="/app-entry" className="btn-primary" style={{ padding: "0.65rem 1.25rem", borderRadius: 8 }}>
            開始使用
          </Link>
          <Link href="/help/onboarding" style={{ padding: "0.65rem 1.25rem", border: "1px solid var(--border)", borderRadius: 8 }}>
            新手指南
          </Link>
        </div>
      </section>

      <section className="kpi-grid" style={{ marginTop: "2rem" }}>
        {[
          ["Exposure Opportunity", "跨 GSC、SERP、AI 的優先級佇列"],
          ["Decision Plane", "核准、延後、路線圖排程"],
          ["Grounded Content", "企業 KB + claim gate 後才發布"],
          ["Client Portal", "白標報表與客戶核准"],
        ].map(([title, desc]) => (
          <div key={title} className="card">
            <h3 style={{ marginTop: 0 }}>{title}</h3>
            <p style={{ color: "var(--muted)", margin: 0 }}>{desc}</p>
          </div>
        ))}
      </section>
    </>
  );
}
