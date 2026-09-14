import assert from "node:assert/strict";
import { test } from "node:test";
import { buildOrderReceiptMessage } from "../src/lib/order-receipt.js";

function savedOrder(overrides = {}) {
  return {
    customer_id: 4,
    ticket_number: "QL-20260915-001",
    order_date: "2026-09-15",
    service_type: "wash_fold",
    total_price: 650,
    amount_paid: 100,
    balance_due: 550,
    promised_ready_at: "2026-09-16T07:00:00Z",
    status: "received",
    service_lines: [],
    ...overrides,
  };
}

test("mixed receipt includes saved tally and garment condition details", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    service_lines: [
      {
        service_name: "Wash & Fold",
        item_recording_mode: "tally",
        item_check_status: "completed",
        items: [
          { item_name: "Shirt", quantity: 2 },
          { item_name: "Trouser", quantity: 1 },
        ],
      },
      {
        service_name: "Dry Cleaning - Shirt",
        item_recording_mode: "detailed",
        item_check_status: "completed",
        items: [{
          item_name: "Shirt",
          quantity: 1,
          description: "Blue long-sleeved shirt",
          is_damaged: true,
          damage_note: "Small tear on left cuff",
          stain_note: "Ink on right sleeve",
        }],
      },
    ],
  }), "Amina Wanjiku");

  assert.match(message, /Customer: Amina Wanjiku/);
  assert.match(message, /Wash & Fold:\n- Shirt x2\n- Trouser x1/);
  assert.match(message, /Dry Cleaning - Shirt:\n- Shirt — Blue long-sleeved shirt/);
  assert.match(message, /Existing damage: Small tear on left cuff/);
  assert.match(message, /Stain note: Ink on right sleeve/);
});

test("pending check is explicit and does not invent a zero-piece record", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    service_lines: [{
      service_name: "Wash & Fold",
      item_recording_mode: "tally",
      item_check_status: "pending",
      items: [],
    }],
  }), "Test customer");

  assert.match(message, /Wash & Fold:\n- Clothing check pending/);
  assert.doesNotMatch(message, /0 pieces|No damage/);
});

test("confirmed no damage is distinct from missing condition information", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    service_lines: [{
      service_name: "Dry Cleaning - Shirt",
      item_recording_mode: "detailed",
      item_check_status: "completed",
      items: [
        { item_name: "Shirt", quantity: 1, is_damaged: false },
        { item_name: "Shirt", quantity: 1, is_damaged: null },
      ],
    }],
  }), "Test customer");

  assert.match(message, /Existing damage: None recorded/);
  assert.match(message, /Existing damage: Not recorded/);
});

test("older orders keep a useful receipt without invented clothing details", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    service_type: "wash_fold",
    service_lines: [],
  }), "Older customer");

  assert.match(message, /Services: wash fold/);
  assert.doesNotMatch(message, /Clothing record/);
});

test("ready order uses the ready heading and current saved totals", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    status: "ready",
    total_price: 450,
    amount_paid: 450,
    balance_due: 0,
  }), "Ready customer");

  assert.match(message, /^Your laundry is ready for collection/);
  assert.match(message, /Paid: KES 450/);
  assert.match(message, /Balance: KES 0/);
  assert.match(message, /Status: Ready for Collection/);
});
