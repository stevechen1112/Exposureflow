import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";

const ARTICLES = [
  { href: "/help/onboarding", title: "Onboarding Guide", desc: "從註冊到第一份報表" },
  { href: "/help/integrations", title: "Integration Setup", desc: "GSC、GA4、SERP、Bing" },
  { href: "/help/api", title: "API & Webhooks", desc: "REST API 與 Stripe webhook" },
];

export default function HelpCenterPage() {
  return (
    <>
      <PageHeader title="Help Center" subtitle="自助啟用與整合文件" />
      <div style={{ display: "grid", gap: "1rem" }}>
        {ARTICLES.map((a) => (
          <Link key={a.href} href={a.href} className="card" style={{ display: "block" }}>
            <h3 style={{ margin: "0 0 0.35rem" }}>{a.title}</h3>
            <p style={{ margin: 0, color: "var(--muted)" }}>{a.desc}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
