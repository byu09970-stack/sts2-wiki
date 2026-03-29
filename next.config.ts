import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "slaythespire.wiki.gg",
        pathname: "/images/**",
      },
    ],
  },
};

export default nextConfig;
