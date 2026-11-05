import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The deployed frontend is static files served by the FastAPI app. The Dockerfile sets
  // NEXT_OUTPUT=standalone for its self-contained server.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : "export",
  // Builds login/index.html rather than login.html, which is what app.frontend() serves.
  trailingSlash: true,
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "avatar.vercel.sh",
      },
      {
        protocol: "https",
        hostname: "notion-avatars.netlify.app",
      },
      {
        protocol: "https",
        hostname: "assets.aceternity.com",
      },
    ],
  },
};

export default nextConfig;
