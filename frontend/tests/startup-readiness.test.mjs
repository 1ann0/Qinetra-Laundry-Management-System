import assert from "node:assert/strict";
import { test } from "node:test";
import { checkApiReadiness } from "../src/lib/api.js";

const json = (body) => new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });

test("public readiness can finish after a minute without credentials or business reads", async (t) => {
  process.env.NEXT_PUBLIC_API_URL = "https://api.example.invalid";
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let finish;
  const fetch = t.mock.method(globalThis, "fetch", (url, options) => {
    assert.equal(url, "https://api.example.invalid/health/ready");
    assert.equal(options.headers.has("Authorization"), false);
    assert.equal(options.body, undefined);
    return new Promise((resolve, reject) => {
      finish = resolve;
      options.signal.addEventListener("abort", () => reject(new Error("aborted")));
    });
  });
  const pending = checkApiReadiness();
  t.mock.timers.tick(60_000);
  finish(json({ status: "ready" }));
  await pending;
  assert.equal(fetch.mock.callCount(), 1);
});

test("a public readiness deadline stops at two minutes", async (t) => {
  process.env.NEXT_PUBLIC_API_URL = "https://api.example.invalid";
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const fetch = t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener("abort", () => reject(new Error("aborted")));
  }));
  const pending = assert.rejects(checkApiReadiness(), { code: "QLMS-TIMEOUT" });
  t.mock.timers.tick(119_999);
  assert.equal(fetch.mock.calls[0].arguments[1].signal.aborted, false);
  t.mock.timers.tick(1);
  await pending;
  assert.equal(fetch.mock.callCount(), 1);
});

test("leaving sign-in cancels readiness and cannot start another request", async (t) => {
  process.env.NEXT_PUBLIC_API_URL = "https://api.example.invalid";
  const controller = new AbortController();
  const fetch = t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener("abort", () => reject(new Error("aborted")));
  }));
  const pending = assert.rejects(checkApiReadiness({ signal: controller.signal }), { code: "QLMS-CANCELLED" });
  controller.abort();
  await pending;
  assert.equal(fetch.mock.callCount(), 1);
});

test("only an explicit ready reply may claim the server is ready", async (t) => {
  process.env.NEXT_PUBLIC_API_URL = "https://api.example.invalid";
  for (const body of [{ status: "not_ready" }, {}, { status: true }]) {
    t.mock.method(globalThis, "fetch", async () => json(body));
    await assert.rejects(checkApiReadiness(), { code: "QLMS-SERVICE" });
  }
});
