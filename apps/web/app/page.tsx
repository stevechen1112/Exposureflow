"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ensureDevSession } from "@/lib/api-client";
import { DEV_AUTH_ENABLED } from "@/lib/config";

export default function HomePage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!DEV_AUTH_ENABLED) {
      setError("正式環境請由 Clerk 登入流程進入應用");
      return;
    }
    ensureDevSession()
      .then(({ workspaceId, siteId }) => {
        if (workspaceId && siteId) {
          router.replace(`/app/${workspaceId}/sites/${siteId}/dashboard`);
        } else if (workspaceId) {
          router.replace(`/app/${workspaceId}/onboarding`);
        } else {
          setError("dev session 未建立 workspace，請確認 API bootstrap");
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [router]);

  if (error) {
    return (
      <div className="card" style={{ margin: "2rem" }}>
        <p>{error}</p>
      </div>
    );
  }

  return <div style={{ padding: "2rem", color: "var(--muted)" }}>正在進入 ExposureFlow…</div>;
}
