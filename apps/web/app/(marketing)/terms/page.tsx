import { PageHeader } from "@/components/PageHeader";

export default function TermsPage() {
  return (
    <>
      <PageHeader title="Terms of Service" subtitle="最後更新：2026-06-14" />
      <div className="card" style={{ lineHeight: 1.7 }}>
        <p>使用 ExposureFlow 即表示您同意本服務條款。本服務提供 SEO 曝光分析、決策與內容執行工具。</p>
        <h3>帳號與使用</h3>
        <p>您須對 workspace 成員與整合憑證負責。禁止逆向工程、濫用 API 或嘗試跨租戶存取。</p>
        <h3>付款</h3>
        <p>訂閱方案依 Stripe 帳單週期收費。取消後依方案條款處理資料保留。</p>
        <h3>免責</h3>
        <p>ExposureFlow 不提供 SEO 排名保證。AI 與 SERP 資料僅供決策參考。</p>
      </div>
    </>
  );
}
