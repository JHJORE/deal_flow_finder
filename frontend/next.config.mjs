/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Same-origin /api/* in dev mirrors what Vercel Services does in prod: the
  // browser always calls /api/..., and the /api prefix is stripped before the
  // request hits the FastAPI app (Vercel does this via routePrefix + ASGI
  // root_path; here we strip it explicitly in the dev rewrite).
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/:path*" },
    ];
  },
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
};

export default nextConfig;
