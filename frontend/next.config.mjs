import path from "node:path";
import { fileURLToPath } from "node:url";
import { securityHeaders } from "./src/lib/security-headers.js";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
  turbopack: {
    root: path.dirname(fileURLToPath(import.meta.url)),
  },
  ...(process.env.NODE_ENV !== "production" ? { async headers() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL ? new URL(process.env.NEXT_PUBLIC_API_URL).origin : "";
    return [{source: "/:path*", headers: securityHeaders(apiOrigin, true)}];
  }} : {}),
};

export default nextConfig;
