import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { securityHeaders } from "../src/lib/security-headers.js";

// Compile the API URL and hosting policy from the same public build setting.
const api = new URL(process.env.NEXT_PUBLIC_API_URL || "");
if (!["https:", "http:"].includes(api.protocol) || api.username || api.password || api.search || api.hash) {
  throw new Error("Set NEXT_PUBLIC_API_URL to an HTTP(S) API URL without credentials, query or fragment.");
}
const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
execFileSync(process.execPath, [fileURLToPath(new URL("../node_modules/next/dist/bin/next", import.meta.url)), "build"], {cwd: frontendRoot, stdio: "inherit"});
const headers = securityHeaders(api.origin);
writeFileSync(new URL("../out/_headers", import.meta.url), `/*\n${headers.map(({key, value}) => `  ${key}: ${value}`).join("\n")}\n`);
writeFileSync(new URL("./wrangler.generated.json", import.meta.url), JSON.stringify({
  name: "qlms-pilot-qualification",
  main: "worker.js",
  compatibility_date: "2026-08-27",
  compatibility_flags: ["nodejs_compat", "global_fetch_strictly_public"],
  assets: {directory: "../out", binding: "ASSETS", not_found_handling: "404-page", run_worker_first: ["/orders/*", "/customers/*"]},
  vars: {PUBLIC_API_ORIGIN: api.origin},
  observability: {enabled: false},
}, null, 2) + "\n");
