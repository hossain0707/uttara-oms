import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Uttara OMS",
    short_name: "Uttara OMS",
    description: "Secure organizational management",
    start_url: "/",
    display: "standalone",
    background_color: "#F6F8F7",
    theme_color: "#123F34",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
  };
}
