// Build customer receipt text from the saved order returned by FastAPI.

function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(value) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeZone: "Africa/Nairobi",
  }).format(new Date(`${value}T12:00:00+03:00`));
}

function formatDateTime(value) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Africa/Nairobi",
  }).format(new Date(value));
}

function getStatusLabel(status) {
  if (status === "in_progress") return "In Progress";
  if (status === "ready") return "Ready for Collection";
  if (status === "collected") return "Collected";
  return "Received";
}

function getServiceNames(order) {
  const lines = order.service_lines || [];
  if (lines.length > 0) return lines.map((line) => line.service_name).join(", ");
  return String(order.service_type || "Service").replaceAll("_", " ");
}

function getItemLines(item, recordingMode) {
  const quantity = Number(item.quantity) || 1;
  const quantityText = recordingMode === "tally" || quantity > 1
    ? ` x${quantity}`
    : "";
  const description = item.description ? ` — ${item.description}` : "";
  const lines = [`- ${item.item_name}${quantityText}${description}`];

  if (recordingMode === "detailed") {
    if (item.is_damaged === true) {
      lines.push(`  Existing damage: ${item.damage_note || "Recorded"}`);
    } else if (item.is_damaged === false) {
      lines.push("  Existing damage: None recorded");
    } else {
      lines.push("  Existing damage: Not recorded");
    }
  }
  if (item.stain_note) lines.push(`  Stain note: ${item.stain_note}`);
  for (const [index, exception] of (item.exceptions || []).entries()) {
    const exceptionDescription = exception.description
      ? ` — ${exception.description}`
      : "";
    lines.push(`  Condition note ${index + 1}${exceptionDescription}`);
    if (exception.is_damaged) {
      lines.push(`    Existing damage: ${exception.damage_note}`);
    }
    if (exception.stain_note) {
      lines.push(`    Stain note: ${exception.stain_note}`);
    }
  }
  return lines;
}

function getClothingLines(order) {
  const clothingLines = [];

  for (const serviceLine of order.service_lines || []) {
    if (serviceLine.item_recording_mode === "none") continue;

    const items = serviceLine.items || [];
    clothingLines.push(`${serviceLine.service_name}:`);
    for (const item of items) {
      clothingLines.push(...getItemLines(item, serviceLine.item_recording_mode));
    }

    if (serviceLine.item_check_status === "pending") {
      clothingLines.push("- Clothing check pending");
    }
  }

  return clothingLines.length > 0 ? ["", "Clothing record", ...clothingLines] : [];
}

export function buildOrderReceiptMessage(order, customerName) {
  const readyNotice = order.status === "ready";
  return [
    readyNotice ? "Your laundry is ready for collection" : "Qinetra Laundry receipt",
    `Customer: ${customerName || `Customer ${order.customer_id}`}`,
    `Ticket: ${order.ticket_number}`,
    `Order date: ${formatDate(order.order_date)}`,
    `Services: ${getServiceNames(order)}`,
    ...getClothingLines(order),
    "",
    `Total: ${formatKes(order.total_price)}`,
    `Paid: ${formatKes(order.amount_paid)}`,
    `Balance: ${formatKes(order.balance_due)}`,
    `Ready by: ${formatDateTime(order.promised_ready_at)}`,
    `Status: ${getStatusLabel(order.status)}`,
    "",
    readyNotice
      ? "Please clear any balance before collection."
      : "Thank you for choosing Qinetra Laundry.",
  ].join("\n");
}
