import { MarketingFooter, MarketingNav } from "@/components/MarketingShell";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <MarketingNav />
      <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1.5rem" }}>{children}</main>
      <MarketingFooter />
    </>
  );
}
