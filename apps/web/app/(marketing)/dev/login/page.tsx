import Link from "next/link";
import { DevRolePicker } from "@/components/DevRolePicker";
import { DEV_AUTH_ENABLED } from "@/lib/config";

export default function DevLoginPage() {
  if (!DEV_AUTH_ENABLED) {
    return (
      <main style={{ maxWidth: 480, margin: "2rem auto", padding: "0 1rem" }}>
        <div className="card">
          <p style={{ color: "var(--danger)", margin: 0 }}>開發者角色切換僅在本地開發環境可用。</p>
          <p style={{ marginTop: "1rem" }}>
            <Link href="/app-entry">返回登入</Link>
          </p>
        </div>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 920, margin: "2rem auto", padding: "0 1rem" }}>
      <header style={{ marginBottom: "1.75rem" }}>
        <p
          style={{
            display: "inline-block",
            fontSize: "0.72rem",
            fontWeight: 600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "var(--accent-text)",
            background: "var(--accent-soft)",
            padding: "0.2rem 0.55rem",
            borderRadius: 999,
            marginBottom: "0.75rem",
          }}
        >
          開發者工具
        </p>
        <h1 className="page-title">RBAC 角色切換</h1>
        <p className="page-subtitle" style={{ maxWidth: 640 }}>
          僅供本地開發與 QA 測試權限邊界。正式使用者請從{" "}
          <Link href="/app-entry">登入頁</Link> 進入，角色由工作區管理員指派。
        </p>
      </header>

      <DevRolePicker />
    </main>
  );
}
