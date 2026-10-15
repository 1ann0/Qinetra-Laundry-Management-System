import { nairobiToday } from "./report-tools.js";

export const EXPENSE_CATEGORIES = { supplies: "Supplies", utilities: "Utilities", rent: "Rent", wages: "Wages", outsourcing: "Outsourcing", other: "Other" };
export const EXPENSE_FIELDS = ["paid_date", "category", "amount", "payment_method", "reference", "note"];

export function expenseBody(values, record = null, today = nairobiToday()) {
  const errors = {};
  const body = Object.fromEntries(EXPENSE_FIELDS.map(field => [field, String(values[field] ?? "").trim()]));
  const date = new Date(`${body.paid_date}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(body.paid_date) || !Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== body.paid_date || body.paid_date > today) errors.paid_date = "Choose today or an earlier paid date.";
  if (!Object.hasOwn(EXPENSE_CATEGORIES, body.category)) errors.category = "Choose an expense category.";
  if (!/^\d{1,10}(\.\d{1,2})?$/.test(body.amount) || Number(body.amount) <= 0 || Number(body.amount) > 9999999999) errors.amount = "Enter KES 0.01 or more, using at most two decimal places.";
  if (!["cash", "mpesa"].includes(body.payment_method)) errors.payment_method = "Choose Cash or M-Pesa.";
  if (body.reference.length > 100 || /[\x00-\x1f\x7f]/.test(body.reference)) errors.reference = "Use a reference of at most 100 characters without line breaks.";
  if (body.note.length > 1000 || /[\x00-\x09\x0b-\x1f\x7f]/.test(body.note)) errors.note = "Use a note of at most 1,000 characters without control characters.";
  if (record) {
    const reason = String(values.reason ?? "").trim();
    if (!reason || reason.length > 200 || /[\x00-\x1f\x7f]/.test(reason)) errors.reason = "Explain the correction in at most 200 characters.";
    body.expected_revision = record.revision;
    body.reason = reason;
    body.is_voided = values.is_voided === true;
  }
  return { body, errors };
}

export function pendingExpenseValues(pending) {
  try {
    const body = JSON.parse(pending?.body);
    if (!body || !EXPENSE_FIELDS.every(field => typeof body[field] === "string")) return null;
    return Object.fromEntries([...EXPENSE_FIELDS, "reason", "is_voided"].filter(field => Object.hasOwn(body, field)).map(field => [field, body[field]]));
  } catch { return null; }
}
