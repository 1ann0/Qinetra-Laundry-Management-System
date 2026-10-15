import assert from "node:assert/strict";
import { test } from "node:test";
import { expenseBody, pendingExpenseValues } from "../src/lib/expense-tools.js";

const values = { paid_date: "2026-10-14", category: "supplies", amount: "250.50", payment_method: "cash", reference: " receipt 4 ", note: "Soap", reason: "Wrong amount", is_voided: true };
test("expenses preserve decimal input and correction revision without trusting extra fields", () => {
  const created = expenseBody({ ...values, confirmed_by_username: "fake" }, null, "2026-10-14");
  assert.deepEqual(created.errors, {});
  assert.equal(created.body.amount, "250.50");
  assert.equal(created.body.reference, "receipt 4");
  assert.equal(created.body.confirmed_by_username, undefined);
  assert.equal(created.body.is_voided, undefined);
  const corrected = expenseBody(values, { revision: 3 }, "2026-10-14");
  assert.equal(corrected.body.expected_revision, 3);
  assert.equal(corrected.body.is_voided, true);
  assert.equal(corrected.body.reason, "Wrong amount");
});
test("paid dates, precision, controls and correction reasons fail before preparing a save", () => {
  for (const amount of ["0", "-1", "NaN", "1.001", "1e3", "10000000000"]) assert.ok(expenseBody({ ...values, amount }, null, "2026-10-14").errors.amount);
  for (const paid_date of ["2026-10-15", "2026-02-30", ""]) assert.ok(expenseBody({ ...values, paid_date }, null, "2026-10-14").errors.paid_date);
  assert.ok(expenseBody({ ...values, reason: "  " }, { revision: 0 }, "2026-10-14").errors.reason);
  assert.ok(expenseBody({ ...values, reference: "one\ntwo" }, null, "2026-10-14").errors.reference);
  assert.deepEqual(expenseBody({ ...values, note: "Soap\nDelivery" }, null, "2026-10-14").errors, {});
});
test("pending save display shows the original allowed fields and tolerates damaged storage", () => {
  const { body } = expenseBody(values, { revision: 2 }, "2026-10-14");
  const shown = pendingExpenseValues({ body: JSON.stringify({ ...body, request_key: "hidden" }) });
  assert.equal(shown.amount, "250.50");
  assert.equal(shown.reason, "Wrong amount");
  assert.equal(shown.request_key, undefined);
  assert.equal(pendingExpenseValues({ body: "broken" }), null);
  assert.equal(pendingExpenseValues({ body: "null" }), null);
});
