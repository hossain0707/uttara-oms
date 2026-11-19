import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Uttara OMS | Organizational Management",
  description: "Private organizational administration, authorized access only.",
  applicationName: "Uttara OMS",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
