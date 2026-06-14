import { MarketingFooter, MarketingNav } from "@/components/MarketingShell";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="marketing-shell">
      <MarketingNav />
      <main className="marketing-hero" style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1.5rem" }}>
        {children}
      </main>
      <MarketingFooter />
    </div>
  );
}
