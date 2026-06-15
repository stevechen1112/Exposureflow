"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ensureDevSession } from "@/lib/api-client";
import { DEV_AUTH_ENABLED } from "@/lib/config";
import { DEFAULT_DEV_PERSONA } from "@/lib/dev-personas";
import { resolveEntryPath } from "@/lib/permissions";

export default function AppEntryPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function signIn() {
    setBusy(true);
    setError(null);
    try {
      const { workspaceId, siteId, role } = await ensureDevSession(
        DEFAULT_DEV_PERSONA.email,
        DEFAULT_DEV_PERSONA.name,
      );
      if (!workspaceId) {
        setError("無法建立工作區，請確認 API 已啟動");
        return;
      }
      router.replace(resolveEntryPath(workspaceId, role, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "登入失敗");
    } finally {
      setBusy(false);
    }
  }

  if (!DEV_AUTH_ENABLED) {
    return (
      <main style={{ maxWidth: 520, margin: "2rem auto", padding: "0 1rem" }}>
        <div className="card" style={{ textAlign: "center" }}>
          <h1 className="page-title" style={{ fontSize: "1.5rem" }}>
            登入 ExposureFlow
          </h1>
          <p className="page-subtitle" style={{ marginBottom: "1.5rem" }}>
            使用公司 Email 或 SSO 登入。登入後系統會依您在工作區的角色，自動導向顧問後台、客戶入口或計費頁面。
          </p>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: "1rem" }}>
            角色由工作區管理員在「設定 → 成員」指派，無需自行選擇。
          </p>
          <p style={{ color: "var(--danger)", fontSize: "0.9rem" }}>
            正式環境請使用 Clerk 登入（尚未在此頁嵌入）。
          </p>
        </div>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 520, margin: "2rem auto", padding: "0 1rem" }}>
      <div className="card" style={{ textAlign: "center" }}>
        <h1 className="page-title" style={{ fontSize: "1.5rem" }}>
          登入 ExposureFlow
        </h1>
        <p className="page-subtitle" style={{ marginBottom: "1.5rem" }}>
          本地開發：登入後依工作區角色自動導向對應後台（顧問、客戶、計費或平台營運）。
        </p>

        {error ? (
          <p style={{ color: "var(--danger)", marginBottom: "1rem", fontSize: "0.9rem" }}>{error}</p>
        ) : null}

        <button
          type="button"
          className="btn btn-primary"
          disabled={busy}
          onClick={signIn}
          style={{ width: "100%", maxWidth: 280, marginBottom: "1.25rem" }}
        >
          {busy ? "登入中…" : "登入"}
        </button>

        <p style={{ color: "var(--muted)", fontSize: "0.85rem", lineHeight: 1.6, margin: 0 }}>
          角色由工作區管理員指派，一般使用者不需要選擇角色。
        </p>
      </div>

      <p style={{ textAlign: "center", marginTop: "1.25rem", fontSize: "0.85rem" }}>
        <Link href="/dev/login" style={{ color: "var(--muted)" }}>
          開發者：測試 RBAC 角色 →
        </Link>
      </p>
    </main>
  );
}
