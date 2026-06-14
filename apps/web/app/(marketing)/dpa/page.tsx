import { PageHeader } from "@/components/PageHeader";

export default function DpaPage() {
  return (
    <>
      <PageHeader title="Data Processing Agreement" subtitle="Enterprise 客戶範本" />
      <div className="card" style={{ lineHeight: 1.7 }}>
        <p>本 DPA 範本適用 ExposureFlow 作為 Processor、客戶作為 Controller 之情形（GDPR / 個資法）。</p>
        <h3>處理目的</h3>
        <p>提供自然曝光分析、決策、報表與內容執行 SaaS。</p>
        <h3>資料類型</h3>
        <p>帳號識別、網站 URL、搜尋效能、內容草稿與審核紀錄。</p>
        <h3>安全措施</h3>
        <p>加密傳輸與靜態加密、RBAC、audit log、備份與 incident 流程。詳見 Security 頁。</p>
        <h3>子處理者</h3>
        <p>清單可應要求提供。重大變更提前 30 日通知。</p>
        <p style={{ marginTop: "1.5rem", color: "var(--muted)" }}>
          正式簽署版請聯繫 legal@exposureflow.com
        </p>
      </div>
    </>
  );
}
