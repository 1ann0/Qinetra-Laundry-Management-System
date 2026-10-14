import assert from "node:assert/strict";
import { test } from "node:test";
import * as reports from "../src/lib/report-tools.js";

test("dashboard work puts late laundry first and totals current debt separately from refunds", () => {
  const rows = [
    { ticket: "READY", attention: "ready, outstanding", balance_due: 499.95, refund_due: 0 },
    { ticket: "REFUND", attention: "refund_due", balance_due: 0, refund_due: 100 },
    { ticket: "LATE", attention: "production_late, outstanding", balance_due: 0.10, refund_due: 0 },
  ];
  const result = reports.dashboardWork({ sections: [{ key: "attention", rows }] });
  assert.deepEqual(result.rows.map(row => row.ticket), ["LATE", "READY", "REFUND"]);
  assert.equal(result.totalOwed, 500.05);
  assert.equal(result.totalRefundDue, 100);
  assert.equal(rows[0].ticket, "READY");
});

test("an empty dashboard has no invented work or money", () => {
  assert.deepEqual(reports.dashboardWork({ sections: [{ key: "attention", rows: [] }] }), {
    rows: [], totalOwed: 0, totalRefundDue: 0,
  });
});

test("Nairobi business date changes at 21:00 UTC", () => {
  assert.equal(reports.nairobiToday(new Date("2026-10-12T20:59:59Z")), "2026-10-12");
  assert.equal(reports.nairobiToday(new Date("2026-10-12T21:00:00Z")), "2026-10-13");
});

test("report query sends only applicable filters and preserves explicit all-date selection", () => {
  assert.equal(reports.reportQuery("attention", { start_date: "2026-10-01", attention: "holds", customer_id: "5" }), "customer_id=5&attention=holds");
  assert.equal(reports.reportQuery("customer", { customer_id: "5", start_date: "", end_date: "", service_id: "2" }), "customer_id=5");
  assert.throws(() => reports.reportQuery("not-a-report", {}));
});
