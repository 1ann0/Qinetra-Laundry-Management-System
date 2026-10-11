import assert from "node:assert/strict";
import { test } from "node:test";
import { matchesSearch, searchWorkspace } from "../src/lib/workspace-search.js";

test("list search matches words in any order, accents and catalogue codes", () => {
  assert.equal(matchesSearch(" SHIRT dry ", "Dry Cleaning — Shirt", "dry_cleaning_shirt"), true);
  assert.equal(matchesSearch("cafe", "Café cloth"), true);
  assert.equal(matchesSearch("   ", "Duvet"), true);
  assert.equal(matchesSearch("shirt duvet", "Dry Cleaning — Shirt"), false);
});

test("workspace search uses one query and only existing read endpoints", async () => {
  const calls = [];
  const request = async (path) => {
    calls.push(path);
    return path.startsWith("/catalog/") ? [{id: 3, name: "Dry Cleaning Shirt", code: "dry_shirt"}, {id: 4, name: "Duvet"}] : [{id: 1}];
  };
  const result = await searchWorkspace(request, " Shirt ");
  assert.deepEqual(calls, ["/customers?search=Shirt", "/orders?search=Shirt", "/catalog/services?include_inactive=true"]);
  assert.deepEqual(result.services.value.map(service => service.id), [3]);
  assert.equal(result.customers.status, "fulfilled");
  assert.equal(result.query, "Shirt");
});

test("a failed section is distinguished from no matches and other results remain usable", async () => {
  const failure = new Error("fixture unavailable");
  const result = await searchWorkspace(async path => {
    if (path.startsWith("/orders")) throw failure;
    return [];
  }, "QL-20261011-001");
  assert.equal(result.orders.status, "rejected");
  assert.equal(result.orders.reason, failure);
  assert.deepEqual(result.customers.value, []);
  assert.deepEqual(result.services.value, []);
});

test("blank and oversized searches make no requests; special query characters are encoded", async () => {
  let calls = 0;
  const request = async () => { calls++; return []; };
  await assert.rejects(searchWorkspace(request, "  "));
  await assert.rejects(searchWorkspace(request, "a".repeat(101)));
  assert.equal(calls, 0);
  let first;
  await searchWorkspace(async path => { first ??= path; return []; }, "A&B /?");
  assert.equal(first, "/customers?search=A%26B%20%2F%3F");
});
