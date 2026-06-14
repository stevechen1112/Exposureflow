import type { Metadata } from "next";
import { IBM_Plex_Sans, Noto_Sans_TC } from "next/font/google";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const notoSansTc = Noto_Sans_TC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-tc",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ExposureFlow",
  description: "Natural exposure maximization platform",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW" className={`${ibmPlexSans.variable} ${notoSansTc.variable}`}>
      <body>{children}</body>
    </html>
  );
}
