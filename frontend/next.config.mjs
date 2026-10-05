import path from "node:path";
import { fileURLToPath } from "node:url";

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: path.dirname(fileURLToPath(import.meta.url)),
  },
  async headers() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL ? new URL(process.env.NEXT_PUBLIC_API_URL).origin : "";
    const development = process.env.NODE_ENV !== "production";
    const csp = [
      "default-src 'self'",
      `script-src 'self' 'unsafe-inline'${development ? " 'unsafe-eval'" : ""}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      `connect-src 'self' ${apiOrigin}${development ? " ws: wss:" : ""}`.trim(),
      "object-src 'none'", "base-uri 'self'", "frame-ancestors 'none'", "form-action 'self'",
    ].join("; ");
    return [{source: "/:path*", headers: [
      {key: "Content-Security-Policy", value: csp},
      {key: "X-Content-Type-Options", value: "nosniff"},
      {key: "X-Frame-Options", value: "DENY"},
      {key: "Referrer-Policy", value: "no-referrer"},
      {key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()"},
      {key: "Cache-Control", value: "no-store, private, max-age=0"},
      ...(!development && apiOrigin.startsWith("https:") ? [{key: "Strict-Transport-Security", value: "max-age=31536000"}] : []),
    ]}];
  },
};

export default nextConfig;
