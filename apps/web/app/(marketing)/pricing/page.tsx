import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";

const PLANS = [
  { code: "starter", name: "Starter", price: "$99/mo", sites: 1, members: 5 },
  { code: "growth", name: "Growth", price: "$299/mo", sites: 5, members: 15 },
  { code: "agency", name: "Agency", price: "$799/mo", sites: 25, members: 50 },
];

export default function PricingPage() {
  return (
    <>
      <PageHeader title="Pricing" subtitle="依方案配額計費；Enterprise 請聯繫銷售" />
      <div className="kpi-grid">
        {PLANS.map((p) => (
          <div key={p.code} className="card">
            <h3>{p.name}</h3>
            <div className="kpi-value">{p.price}</div>
            <p style={{ color: "var(--muted)" }}>
              {p.sites} sites · {p.members} members
            </p>
            <Link href="/app-entry" style={{ display: "inline-block", marginTop: "0.75rem" }}>
              Get started →
            </Link>
          </div>
        ))}
      </div>
      <p style={{ marginTop: "2rem", color: "var(--muted)", fontSize: "0.9rem" }}>
        實際方案以應用內 Billing 頁與 Stripe 為準。含 SERP snapshot、AI probe 等用量配額。
      </p>
    </>
  );
}
