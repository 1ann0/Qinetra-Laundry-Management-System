import assert from "node:assert/strict";
import { test } from "node:test";
import { responseError } from "../src/lib/user-messages.js";
import { loginRequest } from "../src/lib/api.js";
import { getActiveRequest, getRequestFeedback } from "../src/lib/request-feedback.js";

test("throttled sign-in explains the bounded wait without suggesting a save retry", () => {
  const error = responseError(429, {}, "/auth/login", "Retry the original save.");
  assert.equal(error.code, "QLMS-LOGIN-LIMIT");
  assert.match(error.message, /up to five minutes/);
  assert.doesNotMatch(error.message, /save|one minute/);
});

test("sign-in feedback stays in its form without hiding a concurrent record request", () => {
  const login = { id: 1, ...getRequestFeedback("/auth/login", "POST") };
  const read = { id: 2, ...getRequestFeedback("/customers", "GET") };
  assert.equal(getActiveRequest({ 1: login }), null);
  assert.equal(getActiveRequest({ 1: login, 2: read }), read);
});

test("a slow sign-in can finish after thirty seconds without resending credentials", async (t) => {
  process.env.NEXT_PUBLIC_API_URL = "http://qlms.invalid";
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let finish;
  const fetch = t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((resolve, reject) => {
    finish = resolve;
    signal.addEventListener("abort", () => reject(new Error("aborted")));
  }));
  const pending = loginRequest("fixture", "dummy");
  t.mock.timers.tick(60_000);
  finish(new Response(JSON.stringify({ role: "owner" }), { headers: { "content-type": "application/json" } }));
  assert.deepEqual(await pending, { role: "owner" });
  assert.equal(fetch.mock.callCount(), 1);
});

test("unresponsive sign-in stops after two minutes and never repeats the POST", async (t) => {
  process.env.NEXT_PUBLIC_API_URL = "http://qlms.invalid";
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const fetch = t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener("abort", () => reject(new Error("aborted")));
  }));
  const pending = assert.rejects(loginRequest("fixture", "dummy"), { code: "QLMS-TIMEOUT" });
  t.mock.timers.tick(119_999);
  assert.equal(fetch.mock.calls[0].arguments[1].signal.aborted, false);
  t.mock.timers.tick(1);
  await pending;
  assert.equal(fetch.mock.callCount(), 1);
});
