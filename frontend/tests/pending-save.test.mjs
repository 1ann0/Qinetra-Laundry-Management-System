import { test } from "node:test";
import assert from "node:assert/strict";
import { ApiError } from "../src/lib/user-messages.js";
import { apiRequest } from "../src/lib/api.js";
import { saveScope, readPendingSave, prepareSave, sendPendingSave } from "../src/lib/pending-save.js";

function storage() {
  const records = new Map();
  return {
    getItem: (key) => records.get(key) ?? null,
    setItem: (key, value) => records.set(key, value),
    removeItem: (key) => records.delete(key),
  };
}
const path = "/orders/detailed";
const scope = saveScope(1, path);

test("a lost reply retains the exact request across a simulated page refresh", async () => {
  const store = storage();
  const attempt = prepareSave(store, scope, { quantity: 5 }, () => "original-key");
  await assert.rejects(sendPendingSave(async () => { throw new ApiError("Timeout", 0); }, store, scope, path, attempt));
  const restored = readPendingSave(store, scope);
  assert.deepEqual(restored, attempt);
  let sent;
  const response = await sendPendingSave(async (url, options) => {
    sent = { url, ...options };
    return { id: 42 };
  }, store, scope, path, restored);
  assert.equal(sent.headers["Idempotency-Key"], "original-key");
  assert.equal(sent.body, '{"quantity":5}');
  assert.equal(response.id, 42);
  assert.equal(readPendingSave(store, scope), null);
  assert.equal(prepareSave(store, scope, {}, () => "next-key").key, "next-key");
});

test("a second click or changed form cannot replace a pending request", () => {
  const store = storage();
  prepareSave(store, scope, { quantity: 5 }, () => "first");
  assert.throws(() => prepareSave(store, scope, { quantity: 9 }), /Retry previous save/);
  assert.equal(readPendingSave(store, scope).body, '{"quantity":5}');
});

for (const status of [0, 401, 403, 404, 409, 429, 500, 503]) {
  test(`status ${status} keeps the reference for recovery`, async () => {
    const store = storage();
    const attempt = prepareSave(store, scope, {}, () => "original");
    await assert.rejects(sendPendingSave(async () => { throw new ApiError("Rejected", status); }, store, scope, path, attempt));
    assert.deepEqual(readPendingSave(store, scope), attempt);
  });
}

for (const status of [400, 422]) {
  test(`validation response ${status} allows corrected details`, async () => {
    const store = storage();
    const attempt = prepareSave(store, scope, {}, () => "invalid");
    await assert.rejects(sendPendingSave(async () => { throw new ApiError("Check details", status); }, store, scope, path, attempt));
    assert.equal(readPendingSave(store, scope), null);
  });
}

test("requests belong to one staff account and one destination", () => {
  const store = storage();
  prepareSave(store, scope, {}, () => "key");
  assert.equal(readPendingSave(store, saveScope(2, path)), null);
  assert.equal(readPendingSave(store, saveScope(1, "/orders/1/payments")), null);
});

test("storage failure stops preparation before any request is sent", () => {
  const store = storage();
  store.setItem = () => { throw new Error("Full"); };
  assert.throws(() => prepareSave(store, scope, {}, () => "key"), /QLMS-SAVE-STORAGE/);
});

test("invalid stored data asks for support instead of silently using a new key", () => {
  const store = storage();
  store.setItem(scope, "broken JSON");
  assert.throws(() => readPendingSave(store, scope), /QLMS-SAVE-STORAGE/);
});

test("a protected save tells staff to use its recovery button", async () => {
  const originalFetch = globalThis.fetch;
  const originalUrl = process.env.NEXT_PUBLIC_API_URL;
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8100";
  globalThis.fetch = async () => { throw new TypeError("Offline"); };
  try {
    await assert.rejects(apiRequest(path, {
      method: "POST", headers: { "Idempotency-Key": "original-key" }, body: "{}",
    }), /select Retry previous save/);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalUrl === undefined) delete process.env.NEXT_PUBLIC_API_URL;
    else process.env.NEXT_PUBLIC_API_URL = originalUrl;
  }
});
