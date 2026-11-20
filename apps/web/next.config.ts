import type { NextConfig } from "next";
const staticExport = process.env.NEXT_OUTPUT_MODE === "export";
const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: staticExport ? "export" : "standalone",
  trailingSlash: staticExport,
  poweredByHeader: false,
  headers: staticExport ? undefined : async () => [{
      source: "/:path*",
      headers: [
        {key: "X-Content-Type-Options", value: "nosniff"},
        {key: "Referrer-Policy", value: "no-referrer"},
        {key: "X-Frame-Options", value: "DENY"},
        {key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()"}
      ]
    }]
};
export default nextConfig;
