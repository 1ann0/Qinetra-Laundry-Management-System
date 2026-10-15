import assert from "node:assert/strict";
import { test } from "node:test";
import { availableHelpSteps } from "../src/lib/page-help.js";

test("help omits sections hidden by loading, permissions or the current record", () => {
  const steps = availableHelpSteps("/orders/receipt", id => id === "receipt-payments-step");
  assert.equal(steps.length, 1);
  assert.equal(steps[0].targetId, "receipt-payments-step");
  assert.deepEqual(availableHelpSteps("/finance", () => false), []);
  assert.deepEqual(availableHelpSteps("/unknown", () => true), []);
});

test("each staff screen has a short help flow with clear actions", () => {
  const paths = ["/workspace", "/customers", "/customers/search", "/customers/contact", "/orders", "/orders/status", "/orders/receipt", "/dashboard", "/finance", "/expenses", "/staff", "/settings/catalog"];
  for (const path of paths) {
    const steps = availableHelpSteps(path, () => true);
    assert.ok(steps.length >= 2 && steps.length <= 5, path);
    assert.equal(new Set(steps.map(step => step.title)).size, steps.length, path);
    assert.ok(steps.every(step => step.title && step.description), path);
  }
});
