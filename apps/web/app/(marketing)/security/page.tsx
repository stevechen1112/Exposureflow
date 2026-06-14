import { PageHeader } from "@/components/PageHeader";

export default function SecurityPage() {
  return (
    <>
      <PageHeader title="Security" subtitle="Enterprise-ready 多租戶安全架構" />
      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3>Multi-tenant isolation</h3>
        <p>所有 workspace 資料以 `workspace_id` 強制隔離；跨租戶存取回 403。</p>
      </div>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3>Credential encryption</h3>
        <p>Integration credentials 加密儲存；API 不回傳 plaintext secret。</p>
      </div>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3>Authentication</h3>
        <p>Production 使用 Clerk；支援 workspace RBAC、2FA step-up、IP allowlist。</p>
      </div>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3>Audit & compliance</h3>
        <p>敏感操作寫入 audit log；GDPR data export；DPA template 可下載。</p>
      </div>
      <div className="card">
        <h3>Reliability</h3>
        <p>每日 backup、SLO 監控、circuit breaker、rate limiting。詳見 Security Review Checklist。</p>
      </div>
    </>
  );
}
