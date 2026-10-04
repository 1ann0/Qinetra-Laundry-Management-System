import assert from "node:assert/strict";
import { test } from "node:test";
import { apiRequest, loginRequest } from "../src/lib/api.js";
import { getActiveRequest, getRequestFeedback } from "../src/lib/request-feedback.js";

const flush = async () => { for (let i = 0; i < 12; i += 1) await Promise.resolve(); };
const json = (status = 200, headers = {}) => new Response(JSON.stringify({ id: 1 }), { status, headers: { "content-type": "application/json", ...headers } });
function setup(t) {
  process.env.NEXT_PUBLIC_API_URL = "http://qlms.invalid";
  t.mock.timers.enable({ apis: ["setTimeout", "Date"], now: 0 });
  t.mock.method(Math, "random", () => 0);
}

test("read recovery uses increasing delays and at most three attempts", async (t) => {
  setup(t);
  const fetch = t.mock.method(globalThis, "fetch", async () => json(503));
  const pending = assert.rejects(apiRequest("/orders"), { code: "QLMS-SERVICE" });
  await flush();
  t.mock.timers.tick(499); await flush(); assert.equal(fetch.mock.callCount(), 1);
  t.mock.timers.tick(1); await flush(); assert.equal(fetch.mock.callCount(), 2);
  t.mock.timers.tick(999); await flush(); assert.equal(fetch.mock.callCount(), 2);
  t.mock.timers.tick(1); await pending; assert.equal(fetch.mock.callCount(), 3);
});

test("a temporary network failure can recover a read", async (t) => {
  setup(t);
  let calls = 0;
  t.mock.method(globalThis, "fetch", async () => { if (++calls === 1) throw new TypeError("network"); return json(); });
  const pending = apiRequest("/customers");
  await flush(); t.mock.timers.tick(500);
  assert.deepEqual(await pending, { id: 1 }); assert.equal(calls, 2);
});

for (const retryAfter of ["2", new Date(2000).toUTCString()]) {
  test(`Retry-After ${retryAfter} is respected before a rate-limited read`, async (t) => {
    setup(t);
    let calls = 0;
    t.mock.method(globalThis, "fetch", async () => ++calls === 1 ? json(429, { "retry-after": retryAfter }) : json());
    const pending = apiRequest("/orders");
    await flush(); t.mock.timers.tick(1999); await flush(); assert.equal(calls, 1);
    t.mock.timers.tick(1); assert.deepEqual(await pending, { id: 1 });
  });
}

test("a server wait beyond the total deadline is not shortened", async (t) => {
  setup(t);
  const fetch = t.mock.method(globalThis, "fetch", async () => json(503, { "retry-after": "31" }));
  await assert.rejects(apiRequest("/orders"), { code: "QLMS-SERVICE" });
  assert.equal(fetch.mock.callCount(), 1);
});

test("backoff and a slow fetch share the original thirty-second timeout", async (t) => {
  setup(t);
  let calls = 0;
  t.mock.method(globalThis, "fetch", async (_url, { signal }) => {
    if (++calls === 1) return json(503);
    return new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new Error("aborted"))));
  });
  const pending = assert.rejects(apiRequest("/orders"), { code: "QLMS-TIMEOUT" });
  await flush(); t.mock.timers.tick(500); await flush();
  t.mock.timers.tick(29499); await flush(); assert.equal(calls, 2);
  t.mock.timers.tick(1); await pending; assert.equal(calls, 2);
});

test("cancelling during backoff prevents another fetch", async (t) => {
  setup(t);
  const controller = new AbortController();
  const fetch = t.mock.method(globalThis, "fetch", async () => json(503));
  const pending = assert.rejects(apiRequest("/orders", { signal: controller.signal }), { code: "QLMS-CANCELLED" });
  await flush(); controller.abort(); await pending;
  t.mock.timers.tick(30000); assert.equal(fetch.mock.callCount(), 1);
});

test("an already cancelled request never fetches", async (t) => {
  setup(t);
  const controller = new AbortController(); controller.abort();
  const fetch = t.mock.method(globalThis, "fetch", async () => json());
  await assert.rejects(apiRequest("/orders", { signal: controller.signal }), { code: "QLMS-CANCELLED" });
  assert.equal(fetch.mock.callCount(), 0);
});

test("malformed Retry-After values cannot authorize a rate-limit retry", async (t) => {
  setup(t);
  for (const value of ["invalid", "-1", "1.5"]) {
    const fetch = t.mock.method(globalThis, "fetch", async () => json(429, { "retry-after": value }));
    await assert.rejects(apiRequest("/orders"), { code: "QLMS-BUSY" });
    assert.equal(fetch.mock.callCount(), 1); fetch.mock.restore();
  }
});

test("writes, login and permanent read failures are never automatically repeated", async (t) => {
  setup(t);
  for (const status of [400, 401, 403, 404, 409, 422, 500]) {
    const fetch = t.mock.method(globalThis, "fetch", async () => json(status));
    await assert.rejects(apiRequest("/orders")); assert.equal(fetch.mock.callCount(), 1); fetch.mock.restore();
  }
  const fetch = t.mock.method(globalThis, "fetch", async () => json(503));
  await assert.rejects(apiRequest("/orders/detailed", { method: "POST", headers: { "Idempotency-Key": "original-reference" } }));
  await assert.rejects(loginRequest("fixture", "dummy"));
  assert.equal(fetch.mock.callCount(), 2);
});

test("feedback prioritizes saves and never includes identifiers or request details", () => {
  const read = { id: 1, ...getRequestFeedback("/customers?phone=private") };
  const write = { id: 2, ...getRequestFeedback("/orders/123/refunds", "POST") };
  assert.equal(getActiveRequest({ 1: read, 2: write }), write);
  assert.equal(getActiveRequest({ 1: read }), read);
  assert.equal(getActiveRequest({}), null);
  assert.equal(write.label, "Recording refund…");
  assert.doesNotMatch(JSON.stringify([read, write]), /private|123/);
});
