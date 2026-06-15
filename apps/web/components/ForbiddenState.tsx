import Link from "next/link";

export function ForbiddenState({
  title = "您沒有權限存取此功能",
  message = "請聯絡工作區管理員調整您的角色，或從側邊欄選擇您有權限的頁面。",
  homeHref,
  homeLabel = "返回首頁",
}: {
  title?: string;
  message?: string;
  homeHref?: string;
  homeLabel?: string;
}) {
  return (
    <div className="card" style={{ maxWidth: 520, margin: "2rem auto", textAlign: "center" }}>
      <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }} aria-hidden>
        🔒
      </div>
      <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.15rem" }}>{title}</h2>
      <p style={{ color: "var(--muted)", margin: "0 0 1.25rem", lineHeight: 1.6 }}>{message}</p>
      {homeHref ? (
        <Link href={homeHref} className="btn btn-primary">
          {homeLabel}
        </Link>
      ) : null}
    </div>
  );
}

export function parseApiError(message: string): { friendly: string; isForbidden: boolean } {
  if (message.includes("403") || message.includes("PERMISSION_DENIED")) {
    return {
      isForbidden: true,
      friendly: "您的角色目前無法執行此操作。如需調整權限，請聯絡工作區管理員。",
    };
  }
  if (message.includes("404") || message.includes("NOT_FOUND")) {
    return { isForbidden: false, friendly: "找不到要求的資源，可能尚未建立或已被移除。" };
  }
  if (message.includes("SITE_LIMIT")) {
    return { isForbidden: false, friendly: "已達目前方案的站點數量上限。請編輯現有站點或聯絡營運調整配額。" };
  }
  if (message.includes("422")) {
    return { isForbidden: false, friendly: "請求參數不完整，請確認站點與工作區設定是否完成。" };
  }
  return { isForbidden: false, friendly: message.slice(0, 240) };
}
