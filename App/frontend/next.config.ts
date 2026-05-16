import type { NextConfig } from "next";

const EC2_BACKEND = process.env.BACKEND_URL ?? "http://43.205.229.130:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${EC2_BACKEND}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
