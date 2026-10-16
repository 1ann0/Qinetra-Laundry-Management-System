// One allowlist keeps visible filters and downloaded filters together.
export const REPORT_TYPES = [
  { value: "orders", label: "Orders", filters: ["start_date", "end_date", "customer_id", "service_id", "status"] },
  { value: "customer", label: "One customer", filters: ["start_date", "end_date", "customer_id", "status", "payment_method"] },
  { value: "service", label: "One service", filters: ["start_date", "end_date", "service_id", "customer_id", "status"] },
  { value: "money", label: "Payments and returns", filters: ["start_date", "end_date", "customer_id", "payment_method"] },
  { value: "attention", label: "Needs attention now", filters: ["customer_id", "service_id", "status", "attention"] },
  { value: "catalogue", label: "Shop catalogue", filters: [] },
  { value: "expenses", label: "Shop expenses", filters: ["start_date", "end_date", "category", "payment_method"] },
];

export const ATTENTION_LABELS = {
  due_today: "Due today", production_late: "Late production", ready: "Ready for collection", overdue: "Collection overdue",
  holds: "Waiting for a customer answer", outsourcing: "Outsourcing needs attention", outstanding: "Money still owed", refund_due: "Refund still due",
};

export const SUMMARY_LABELS = {
  cash_received: "Cash received", mpesa_received: "M-Pesa received", total_received: "Total money received",
  refunds_sent: "Money returned", net_cash_movement: "Money received less returns",
  current_balance_due: "Money currently owed to the shop", current_refund_due: "Money currently owed back",
  booked_value: "Booked service value",
  cash_expenses: "Cash expenses", mpesa_expenses: "M-Pesa expenses", total_expenses: "Total shop expenses",
  shop_funded_expenses: "Paid from shop money", owner_funded_expenses: "Paid personally by Owner", unconfirmed_funding_expenses: "Payer not confirmed",
};

export function nairobiToday(now = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(now).filter(part => part.type !== "literal").map(part => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

export function reportQuery(kind, filters) {
  const type = REPORT_TYPES.find(type => type.value === kind);
  if (!type) throw new Error("Unknown report");
  const query = new URLSearchParams();
  for (const field of type.filters) if (filters[field]) query.set(field, filters[field]);
  return query.toString();
}

export function formatKes(value) {
  return `KES ${Number(value).toLocaleString("en-KE", { maximumFractionDigits: 2 })}`;
}

export function dashboardWork(report) {
  const rows = [...(report?.sections.find(section => section.key === "attention")?.rows || [])];
  const priority = ["production_late", "outsourcing", "holds", "overdue", "due_today", "outstanding", "refund_due", "ready"];
  const rank = row => Math.min(...String(row.attention).split(", ").map(flag => {
    const index = priority.indexOf(flag);
    return index < 0 ? priority.length : index;
  }));
  rows.sort((left, right) => rank(left) - rank(right));
  const sumMoney = key => rows.reduce((total, row) => total + Math.round(Number(row[key] || 0) * 100), 0) / 100;
  return { rows, totalOwed: sumMoney("balance_due"), totalRefundDue: sumMoney("refund_due") };
}

export function saveReportFile({ blob, filename }) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Give Android's download manager time to acquire the file before revoking it.
  window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
