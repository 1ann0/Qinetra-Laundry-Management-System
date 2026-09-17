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
        outsourcing_handover: {
          partner_name: "Internal Cleaner Ltd",
          outstanding_count: 1,
        },
        items: [
          {
            item_name: "Shirt",
            quantity: 2,
            exceptions: [{
              description: "Blue school shirt",
              is_damaged: true,
              damage_note: "Small tear near the pocket",
              stain_note: "Ink on the cuff",
            }],
          },
          { item_name: "Trouser", quantity: 1 },
        ],
      },
      {
        service_name: "Dry Cleaning - Shirt",
        item_recording_mode: "detailed",
        item_check_status: "completed",
        items: [{
          garment_reference: "QL-20260915-001-G01",
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
  assert.match(message, /Wash & Fold:\n- Shirt x2/);
  assert.match(message, /Condition note 1 — Blue school shirt/);
  assert.match(message, /Existing damage: Small tear near the pocket/);
  assert.match(message, /Stain note: Ink on the cuff/);
  assert.match(message, /- Trouser x1/);
  assert.match(message, /Dry Cleaning - Shirt:\n- QL-20260915-001-G01 · Shirt — Blue long-sleeved shirt/);
  assert.match(message, /Existing damage: Small tear on left cuff/);
  assert.match(message, /Stain note: Ink on right sleeve/);
  assert.doesNotMatch(message, /Internal Cleaner/);
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

test("receipt shows net paid and identifies returned money without exposing reasons", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    amount_paid: 300,
    balance_due: 350,
    payment_adjustments: [
      { kind: "entry_error", amount: 100, reason: "Private shop note" },
      { kind: "refund", amount: 50, reason: "Private refund note" },
    ],
  }), "Pilot customer");

  assert.match(message, /Paid: KES 300/);
  assert.match(message, /Payment entry corrected: KES 100/);
  assert.match(message, /Refund returned: KES 50/);
  assert.doesNotMatch(message, /Private/);
});

test("cancelled ticket is not presented as an active collection promise", () => {
  const message = buildOrderReceiptMessage(savedOrder({
    status: "cancelled", amount_paid: 0, balance_due: 0,
  }), "Pilot customer");

  assert.match(message, /Status: Cancelled/);
  assert.doesNotMatch(message, /Ready by:|clear any balance before collection/);
});
