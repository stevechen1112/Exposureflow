import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ExposureFlow",
  description: "Natural exposure maximization platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  );
}
