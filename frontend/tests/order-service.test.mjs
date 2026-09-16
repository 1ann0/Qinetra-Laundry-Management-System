import assert from "node:assert/strict";
import { test } from "node:test";
import { getServiceQuantity } from "../src/lib/order-service.js";

test("detailed service price uses charged quantity instead of physical pieces", () => {
  const serviceLine = {
    item_recording_mode: "detailed",
    quantity: "1",
    items: [{ description: "Suit jacket" }, { description: "Suit trousers" }],
  };

  assert.equal(getServiceQuantity(serviceLine), 1);
});
