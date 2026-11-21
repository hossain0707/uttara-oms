import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Uttara OMS | Organizational Management",
  description: "Private organizational administration, authorized access only.",
  applicationName: "Uttara OMS",
  icons: {icon:[{url:"/brand/icon-32.png",sizes:"32x32",type:"image/png"},{url:"/brand/icon-192.png",sizes:"192x192",type:"image/png"}],apple:[{url:"/brand/icon-180.png",sizes:"180x180",type:"image/png"}]},
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
