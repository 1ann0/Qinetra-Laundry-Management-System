import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "../hosting/worker.js";
import { readRecordId } from "../src/lib/record-id.js";
import { securityHeaders } from "../src/lib/security-headers.js";

test("detail links accept one positive safe integer and reject ambiguous IDs", () => {
  assert.equal(readRecordId(new URLSearchParams("id=17")), 17);
  assert.equal(readRecordId(new URLSearchParams("id=9007199254740991")), Number.MAX_SAFE_INTEGER);
  for (const query of ["", "id=", "id=0", "id=-1", "id=1.5", "id=01", "id=1e2", "id=%201", "id=NaN", "id=9007199254740992", "id=1&id=2"]) {
    assert.equal(readRecordId(new URLSearchParams(query)), null, query);
  }
});

test("production policy preserves private responses and allows only the paired API origin", () => {
  const headers = new Headers(securityHeaders("https://api.example.test").map(({key, value}) => [key, value]));
  assert.equal(headers.get("cache-control"), "no-store, private, max-age=0");
  assert.equal(headers.get("x-frame-options"), "DENY");
  assert.equal(headers.get("x-content-type-options"), "nosniff");
  assert.equal(headers.get("referrer-policy"), "no-referrer");
  assert.equal(headers.get("strict-transport-security"), "max-age=31536000");
  assert.match(headers.get("content-security-policy"), /connect-src 'self' https:\/\/api\.example\.test;/);
  assert.match(headers.get("content-security-policy"), /frame-ancestors 'none'/);
  assert.doesNotMatch(headers.get("content-security-policy"), /unsafe-eval|ws:|\*/);
  assert.equal(securityHeaders("http://127.0.0.1:8012").some(header => header.key === "Strict-Transport-Security"), false);
});

test("numeric bookmarks redirect safely with private headers for GET and HEAD", async () => {
  const env = {PUBLIC_API_ORIGIN: "https://api.example.test", ASSETS: {fetch() { throw new Error("Redirect should not fetch an asset"); }}};
  for (const [path, destination] of [["/orders/17", "/orders/receipt?id=17"], ["/customers/2/", "/customers/contact?id=2"]]) {
    for (const method of ["GET", "HEAD"]) {
      const response = await worker.fetch(new Request(`https://qlms.example.test${path}?id=99&next=https://untrusted.example`, {method}), env);
      assert.equal(response.status, 302);
      assert.equal(response.headers.get("location"), `https://qlms.example.test${destination}`);
      assert.match(response.headers.get("cache-control"), /no-store/);
      assert.equal(response.headers.get("x-frame-options"), "DENY");
      assert.equal(await response.text(), "");
    }
  }
});

test("fixed pages, payloads, invalid paths and POSTs retain asset status and content", async () => {
  for (const [path, method] of [["/orders/status", "GET"], ["/orders/receipt?id=17", "GET"], ["/orders/receipt.txt", "GET"], ["/customers/contact?id=2", "GET"], ["/orders/0", "GET"], ["/orders/9007199254740992", "GET"], ["/orders/17/payments", "GET"], ["/orders/17", "POST"]]) {
    const request = new Request(`https://qlms.example.test${path}`, {method});
    const asset = new Response("asset-content", {status: 404, headers: {"Content-Type": "text/plain", "Cache-Control": "public"}});
    const response = await worker.fetch(request, {
      PUBLIC_API_ORIGIN: "https://api.example.test",
      ASSETS: {async fetch(received) { assert.equal(received, request); return asset; }},
    });
    assert.equal(response.status, 404);
    assert.equal(response.headers.get("content-type"), "text/plain");
    assert.equal(response.headers.get("cache-control"), "no-store, private, max-age=0");
    assert.equal(asset.headers.get("cache-control"), "public");
    assert.equal(await response.text(), "asset-content");
  }
});
