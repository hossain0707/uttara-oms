import type { MetadataRoute } from "next";
export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Uttara OMS",
    short_name: "Uttara OMS",
    description: "Secure organizational management",
    start_url: "/",
    display: "standalone",
    background_color: "#F6F8F7",
    theme_color: "#123F34",
    icons: [{src:"/brand/icon-192.png",sizes:"192x192",type:"image/png",purpose:"any"},{src:"/brand/icon-512.png",sizes:"512x512",type:"image/png",purpose:"any"},{src:"/brand/icon-512.png",sizes:"512x512",type:"image/png",purpose:"maskable"}],
  };
}
