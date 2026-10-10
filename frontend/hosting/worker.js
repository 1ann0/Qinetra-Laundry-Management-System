import { securityHeaders } from "../src/lib/security-headers.js";

// Keep numeric bookmarks usable without running a page-rendering server.
const worker = {
  async fetch(request, env) {
    const url = new URL(request.url);
    const legacy = /^\/(orders|customers)\/([1-9]\d*)\/?$/.exec(url.pathname);
    const headers = new Headers(securityHeaders(env.PUBLIC_API_ORIGIN).map(({key, value}) => [key, value]));
    if (legacy && Number.isSafeInteger(Number(legacy[2])) && (request.method === "GET" || request.method === "HEAD")) {
      const destination = new URL(legacy[1] === "orders" ? "/orders/receipt" : "/customers/contact", url.origin);
      destination.searchParams.set("id", legacy[2]);
      headers.set("Location", destination.href);
      return new Response(null, {status: 302, headers});
    }
    const asset = await env.ASSETS.fetch(request);
    const response = new Response(asset.body, asset);
    headers.forEach((value, key) => response.headers.set(key, value));
    return response;
  },
};

export default worker;
