import { PageHeader } from "@/components/PageHeader";

export default function HelpApiPage() {
  return (
    <>
      <PageHeader title="API & Webhooks" subtitle="REST API 與事件整合" />
      <pre className="card" style={{ overflow: "auto", fontSize: "0.85rem" }}>
        {`GET  /health
GET  /api/v1/workspaces
GET  /api/v1/exposure/sites/{site_id}/opportunities
POST /api/v1/webhooks/stripe`}
      </pre>
      <p>
        Headers: <code>Authorization: Bearer &lt;token&gt;</code>,{" "}
        <code>X-Workspace-Id: &lt;uuid&gt;</code>
      </p>
      <p style={{ color: "var(--muted)" }}>完整規格見 docs/api/README.md 與 docs/api/webhooks.md</p>
    </>
  );
}
