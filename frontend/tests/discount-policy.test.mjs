import assert from "node:assert/strict";
import { test } from "node:test";
import { getDiscountPolicyError, getEmployeeDiscountAllowance, getRoundedServiceSubtotal } from "../src/lib/discount-policy.js";
import { responseError } from "../src/lib/user-messages.js";
import { prepareSave, sendPendingSave, readPendingSave } from "../src/lib/pending-save.js";

test("employee preview enforces the whole-order cent boundary and floors fractional cents", () => {
  const policy = { employee_max_discount_percent: "10.00" };
  assert.equal(getEmployeeDiscountAllowance(1000, policy.employee_max_discount_percent), 100);
  assert.equal(getDiscountPolicyError("employee", policy, 1000, 100), "");
  assert.match(getDiscountPolicyError("employee", policy, 1000, 100.01), /must not exceed/);
  assert.match(getDiscountPolicyError("employee", policy, 1000, 200), /whole-order/);
  assert.equal(getEmployeeDiscountAllowance(1.99, 50), 0.99);
  assert.equal(getEmployeeDiscountAllowance(0.29, 100), 0.29);
  assert.equal(getRoundedServiceSubtotal(1.15, 0.9), 1.04);
  const roundedSubtotal = getRoundedServiceSubtotal(1.33, 1.5) * 2;
  assert.equal(roundedSubtotal, 4);
  assert.equal(getDiscountPolicyError("employee", { employee_max_discount_percent: "50" }, roundedSubtotal, 2), "");
});

test("zero or unavailable employee authority rejects a discount but owners keep their authority", () => {
  assert.notEqual(getDiscountPolicyError("employee", { employee_max_discount_percent: "0" }, 1000, 1), "");
  assert.notEqual(getDiscountPolicyError("employee", null, 1000, 1), "");
  assert.equal(getDiscountPolicyError("employee", null, 1000, 0), "");
  assert.equal(getDiscountPolicyError("owner", null, 1000, 200), "");
});

test("definite discount rejection clears only the rejected attempt", async () => {
  const values = new Map();
  const storage = { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) };
  const attempt = prepareSave(storage, "discount-fixture", { amount: 100.01 }, () => "original-key");
  const error = responseError(409, { detail: { code: "QLMS-DISCOUNT-LIMIT", save_state: "not_saved" } }, "/orders/detailed");
  assert.equal(error.saveState, "not_saved");
  assert.match(error.message, /order was not saved/);
  await assert.rejects(sendPendingSave(async () => { throw error; }, storage, "discount-fixture", "/orders/detailed", attempt));
  assert.equal(readPendingSave(storage, "discount-fixture"), null);
});
