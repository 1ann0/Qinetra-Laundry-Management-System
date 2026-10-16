import test from "node:test";
import assert from "node:assert/strict";
import {existsSync} from "node:fs";

const source = new URL("../../backend/ops/cloudflare-trigger/worker.mjs", import.meta.url);
const present = existsSync(source);
const worker = present ? (await import(source)).default : null;
const time = Date.parse("2026-10-16T19:00:00Z");

test("independent trigger exists without a public HTTP handler", () => {
  assert.ok(present, "Independent trigger must be implemented");
  assert.equal(typeof worker.scheduled, "function");
  assert.equal(worker.fetch, undefined);
});

test("daily trigger dispatches only the fixed workflow, main and exact slot", {skip: !present}, async () => {
  const previous = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (...args) => { calls.push(args); return new Response(null, {status: 204}); };
  try {
    await worker.scheduled({cron: "0 19 * * *", scheduledTime: time}, {GITHUB_BACKUP_DISPATCH: "fictional-test-only"});
    assert.equal(calls.length, 1);
    const [url, options] = calls[0];
    assert.equal(url, "https://api.github.com/repos/1ann0/Qinetra-Laundry-Management-System/actions/workflows/pilot-backup.yml/dispatches");
    assert.equal(options.method, "POST");
    assert.equal(options.redirect, "error");
    assert.ok(options.signal);
    assert.deepEqual(JSON.parse(options.body), {ref: "main", inputs: {mode: "daily-trigger", slot: "2026-10-16T19:00:00Z"}});
  } finally { globalThis.fetch = previous; }
});

test("invalid schedule or missing secret never dispatch; provider failures expose no token", {skip: !present}, async () => {
  const previous = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw new Error("fictional-test-only secret provider body"); };
  try {
    for (const controller of [{cron: "* * * * *", scheduledTime: time}, {cron: "0 19 * * *", scheduledTime: time + 60000}]) {
      await assert.rejects(worker.scheduled(controller, {GITHUB_BACKUP_DISPATCH: "fictional-test-only"}), /Invalid backup trigger/);
    }
    await assert.rejects(worker.scheduled({cron: "0 19 * * *", scheduledTime: time}, {}), /Missing backup dispatch credential/);
    assert.equal(calls, 0);
    await assert.rejects(worker.scheduled({cron: "0 19 * * *", scheduledTime: time}, {GITHUB_BACKUP_DISPATCH: "fictional-test-only"}), error => error.message === "Backup dispatch failed");
    assert.equal(calls, 1);
  } finally { globalThis.fetch = previous; }
});

test("dispatch acceptance is not reported as verified backup completion", {skip: !present}, async () => {
  const previous = globalThis.fetch;
  try {
    for (const status of [200, 204]) {
      globalThis.fetch = async () => new Response(null, {status});
      await worker.scheduled({cron: "0 19 * * *", scheduledTime: time}, {GITHUB_BACKUP_DISPATCH: "fictional-test-only"});
    }
    for (const status of [301, 401, 403, 429, 500]) {
      globalThis.fetch = async () => new Response("untrusted private response", {status});
      await assert.rejects(worker.scheduled({cron: "0 19 * * *", scheduledTime: time}, {GITHUB_BACKUP_DISPATCH: "fictional-test-only"}), error => error.message === `Backup dispatch rejected (${status})`);
    }
  } finally { globalThis.fetch = previous; }
});
