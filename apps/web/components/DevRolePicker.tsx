"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ensureDevSession } from "@/lib/api-client";
import { DEV_PERSONA_TIERS, type DevPersona } from "@/lib/dev-personas";
import { ROLE_LABELS, resolveEntryPath } from "@/lib/permissions";

export function DevRolePicker() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function enter(persona: DevPersona) {
    setBusy(persona.role);
    setError(null);
    try {
      const { workspaceId, siteId, role } = await ensureDevSession(
        persona.email,
        persona.name,
        persona.role,
      );
      if (!workspaceId) {
        setError("dev session 未建立 workspace，請確認 API 已啟動");
        return;
      }
      router.replace(resolveEntryPath(workspaceId, role ?? persona.role, siteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "登入失敗");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      {error ? (
        <p style={{ color: "var(--danger)", textAlign: "center", marginBottom: "1rem" }}>{error}</p>
      ) : null}

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {DEV_PERSONA_TIERS.map((tier) => (
          <section key={tier.id}>
            <div style={{ marginBottom: "0.65rem" }}>
              <h2 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>{tier.label}</h2>
              <p style={{ margin: "0.25rem 0 0", fontSize: "0.85rem", color: "var(--muted)" }}>
                {tier.description}
              </p>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                gap: "0.75rem",
              }}
            >
              {tier.personas.map((p) => (
                <button
                  key={p.role}
                  type="button"
                  className="card"
                  disabled={busy !== null}
                  onClick={() => enter(p)}
                  style={{
                    textAlign: "left",
                    cursor: busy ? "wait" : "pointer",
                    border: busy === p.role ? "2px solid var(--accent)" : undefined,
                    opacity: busy && busy !== p.role ? 0.6 : 1,
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{ROLE_LABELS[p.role]}</div>
                  <div style={{ fontSize: "0.82rem", color: "var(--muted)", lineHeight: 1.5 }}>{p.blurb}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--accent-text)", marginTop: "0.5rem" }}>
                    {busy === p.role ? "進入中…" : `${p.email} →`}
                  </div>
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
