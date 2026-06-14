import Link from "next/link";

const LINKS = [
  { href: "/pricing", label: "Pricing" },
  { href: "/help", label: "Help" },
  { href: "/security", label: "Security" },
  { href: "/status", label: "Status" },
];

export function MarketingNav() {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "1rem 2rem",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <Link href="/" style={{ fontWeight: 700, fontSize: "1.1rem" }}>
        ExposureFlow
      </Link>
      <nav style={{ display: "flex", gap: "1.25rem", alignItems: "center" }}>
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} style={{ color: "var(--muted)" }}>
            {l.label}
          </Link>
        ))}
        <Link href="/app-entry" className="btn-primary" style={{ padding: "0.4rem 0.9rem", borderRadius: 8 }}>
          Sign in
        </Link>
      </nav>
    </header>
  );
}

export function MarketingFooter() {
  return (
    <footer
      style={{
        marginTop: "4rem",
        padding: "2rem",
        borderTop: "1px solid var(--border)",
        color: "var(--muted)",
        fontSize: "0.85rem",
      }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
        <Link href="/terms">Terms</Link>
        <Link href="/privacy">Privacy</Link>
        <Link href="/dpa">DPA</Link>
        <Link href="/help/api">API</Link>
      </div>
      <p>© {new Date().getFullYear()} ExposureFlow. Natural exposure maximization for B2B teams.</p>
    </footer>
  );
}
