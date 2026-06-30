import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "OnTrackChain",
    short_name: "OnTrack",
    description: "Compliance driven by on-chain intelligence.",
    start_url: "/",
    display: "standalone",
    background_color: "#02050d",
    theme_color: "#02050d",
    icons: [
      {
        src: "/branding/ontrackchain-badge-192.png",
        sizes: "192x192",
        type: "image/png"
      },
      {
        src: "/branding/ontrackchain-badge-512.png",
        sizes: "512x512",
        type: "image/png"
      }
    ]
  };
}
