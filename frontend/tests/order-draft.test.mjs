import test from "node:test";
import assert from "node:assert/strict";

import {
  clearOrderDraft,
  hasMeaningfulOrderDraft,
  orderDraftScope,
  readOrderDraft,
  saveOrderDraft,
} from "../src/lib/order-draft.js";

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

function draft(overrides = {}) {
  return {
    selectedCustomerId: "",
    selectedServices: [],
    isEarlierOrder: false,
    orderDate: "2026-09-15",
    discountReason: "",
    promisedReadyAt: "",
    isPeakTime: false,
    paymentChoice: "unpaid",
    paymentAmountType: "full",
    depositAmount: "",
    paymentReceivedDate: "2026-09-15",
    paymentConfirmed: false,
    ...overrides,
  };
}

test("draft keys are separated by staff account", () => {
  assert.equal(orderDraftScope(3), "qlms-order-draft:3");
  assert.notEqual(orderDraftScope(3), orderDraftScope(4));
});

test("empty defaults are not treated as unfinished work", () => {
  assert.equal(hasMeaningfulOrderDraft(draft()), false);
  assert.equal(hasMeaningfulOrderDraft(draft({ selectedCustomerId: "7" })), true);
  assert.equal(hasMeaningfulOrderDraft(draft({ selectedServices: [{ service_id: 2 }] })), true);
});

test("meaningful draft round trips and can be cleared", () => {
  const storage = memoryStorage();
  const scope = orderDraftScope(9);
  const unfinished = draft({ selectedCustomerId: "7", depositAmount: "100" });

  saveOrderDraft(storage, scope, unfinished);
  assert.deepEqual(readOrderDraft(storage, scope), unfinished);

  clearOrderDraft(storage, scope);
  assert.equal(readOrderDraft(storage, scope), null);
});

test("saving empty defaults removes an older draft", () => {
  const storage = memoryStorage();
  const scope = orderDraftScope(9);
  saveOrderDraft(storage, scope, draft({ selectedCustomerId: "7" }));
  saveOrderDraft(storage, scope, draft());
  assert.equal(readOrderDraft(storage, scope), null);
});

test("invalid stored data is rejected and removed", () => {
  const storage = memoryStorage();
  const scope = orderDraftScope(9);
  storage.setItem(scope, "{bad json");
  assert.throws(() => readOrderDraft(storage, scope), /could not restore/i);
  assert.equal(storage.getItem(scope), null);
});
