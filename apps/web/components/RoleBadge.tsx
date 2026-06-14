"use client";

import { roleLabel } from "@/lib/auth-context";

export function RoleBadge({ role }: { role: string | undefined }) {
  if (!role) return null;
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: "0.72rem",
        padding: "0.15rem 0.55rem",
        borderRadius: 999,
        background: "var(--accent-soft)",
        color: "var(--accent-text)",
        fontWeight: 500,
        marginLeft: "0.5rem",
        verticalAlign: "middle",
      }}
    >
      {roleLabel(role)}
    </span>
  );
}
