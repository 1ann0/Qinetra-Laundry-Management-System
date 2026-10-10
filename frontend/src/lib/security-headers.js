// Use the same policy in local Next.js, static assets and hosting redirects.
export function securityHeaders(apiOrigin = "", development = false) {
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${development ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'", "img-src 'self' data: blob:",
    "font-src 'self' data:",
    `connect-src 'self' ${apiOrigin}${development ? " ws: wss:" : ""}`.trim(),
    "object-src 'none'", "base-uri 'self'", "frame-ancestors 'none'", "form-action 'self'",
  ].join("; ");
  return [
    {key: "Content-Security-Policy", value: csp},
    {key: "X-Content-Type-Options", value: "nosniff"},
    {key: "X-Frame-Options", value: "DENY"},
    {key: "Referrer-Policy", value: "no-referrer"},
    {key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()"},
    {key: "Cache-Control", value: "no-store, private, max-age=0"},
    ...(!development && apiOrigin.startsWith("https:") ? [{key: "Strict-Transport-Security", value: "max-age=31536000"}] : []),
  ];
}
