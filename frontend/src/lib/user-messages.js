// Keep staff instructions separate from technical details returned by the API.
export class ApiError extends Error {
  constructor(message, status = 0, code = "", saveState = "unknown") {
    super(code ? `${message} Support code: ${code}.` : message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.saveState = saveState;
  }
}

// Only messages we wrote for staff may reach the screen unchanged.
export function getUserMessage(error, fallback = "QLMS could not complete this action.") {
  if (error instanceof ApiError) return error.message;
  return `${fallback} Contact support before you try again. Support code: QLMS-UNEXPECTED.`;
}

const INPUT_MESSAGES = {
  "The clothing details changed on another screen. Open the order again before editing": "Someone changed this clothing list. Open the order again, check the list, then make your changes.",
  "This save reference was already used for different details": "QLMS found different details for this save. Keep this tab open and contact support before you continue.",
  "Use at most two decimal places for the quantity": "Enter the quantity with no more than two digits after the decimal point. For example, 2.25 kg.",
  "Username already taken": "This username is in use. Choose another username.",
  "You cannot deactivate your own account": "You cannot turn off your own account. Ask another owner to do this.",
  "You cannot change your own role": "You cannot change your own account role. Ask another owner to do this.",
  "At least one active owner must remain": "Keep at least one owner account active. Choose another account to change.",
  "Enter a service name using letters or numbers": "Enter a service name with letters or numbers.",
  "Service name cannot be blank": "Enter a service name.",
  "Clothing item name cannot be blank": "Enter a clothing item name.",
  "A similar service already exists": "A similar service is already in Shop setup. Use it or choose a different name.",
  "A service with this name already exists": "This service name is in use. Choose another name.",
  "This clothing item already exists": "This clothing item is already in the list. Select the existing item.",
  "This clothing item exists but is inactive. Ask the owner to restore it in Shop setup": "This clothing item is turned off. Ask the owner to turn it on in Shop setup.",
  "Employees can add Laundry tally items only": "You can add Laundry items here. Ask the owner to add Dry Cleaning items in Shop setup.",
  "This garment is linked to an active Dry Cleaning service": "A Dry Cleaning service still uses this item. Change that service in Shop setup first.",
  "Detailed garment services must use item or pair pricing": "Choose a price per item or per pair for a service with individual clothing details.",
  "Select the garment linked to this Dry Cleaning service": "Select the clothing item for this Dry Cleaning service.",
  "A linked garment requires individual garment details": "Choose individual clothing details for a service linked to a clothing item.",
  "The clothing details must match the selected Dry Cleaning garment": "Use the clothing item selected for this Dry Cleaning service.",
  "This service does not require a clothing list": "This service does not use a clothing list. Remove its clothing entries.",
  "Each clothing type should appear once in a quick tally": "List each clothing type once. Add its total quantity on that line.",
  "Detailed garments must be recorded one at a time": "Enter each clothing item on a separate line.",
  "Confirm whether every detailed garment is already damaged": "Select Yes or No for existing damage on each clothing item.",
  "Describe every detailed garment so it can be identified": "Describe each garment so staff can identify it later.",
  "Each saved garment can appear only once": "The same saved garment was added twice. Open the order again and retry.",
  "A saved garment does not belong to this service": "One garment record is no longer available here. Open the order again and retry.",
  "Clothing details cannot change after the dry-cleaning handling choice": "This clothing list is locked because its dry-cleaning handling is already confirmed. Check the handling details.",
  "Complete the garment check before recording the dry-cleaner handover": "Complete every garment description and condition check before the clothes leave the shop.",
  "This service already has a dry-cleaner handover": "This dry-cleaner handover is already recorded. Check the return list below.",
  "A returned garment is not part of this handover": "This garment is not on the handover list. Open the order again and check its reference.",
  "A returned garment was already confirmed": "This garment was already marked as returned. Check the saved return details.",
  "Confirm every outsourced garment return and resolve any issue before marking this order ready": "Some dry-cleaning garments are still outside or have an unresolved return issue. Check the handover before marking the order ready.",
  "Record the dry-cleaner handover or ask the owner to confirm in-shop cleaning before marking this order ready": "Choose how this dry cleaning was handled before marking the order ready. Record the outside handover, or ask the owner to confirm it stayed in Qinetra.",
  "Select each service only once per order": "Add each service once. Change its quantity to include more laundry.",
  "Enter a reason for the discount": "Enter a reason for the discount.",
  "One or more selected services are unavailable": "A selected service is no longer available. Ask the owner to check Shop setup.",
  "Clothing items cannot be changed after the order is ready": "This order is already ready. Contact the owner if its clothing details need a correction.",
  "Payments cannot be changed after an order is collected": "This order is already collected. Contact the owner if its payment needs a correction.",
  "Confirm that the shop received the payment before saving it": "Confirm that the shop received this payment before you save it.",
  "Payment must be at least KES 0.01": "Enter a payment amount of at least KES 0.01.",
  "Payment received date cannot be in the future": "Choose today or an earlier date for the payment.",
  "Payment received date cannot be before the order date": "Choose a payment date on or after the order date.",
  "Order date cannot be in the future": "Choose today or an earlier date for the order.",
  "Promised completion time must be in the future": "Choose a ready time later than now.",
  "Promised completion time must include a timezone": "Choose the ready date and time again. Contact support if this message returns.",
  "End date cannot be before start date": "Choose an end date on or after the start date.",
  "Select the customer or service for this report": "Choose one customer or service, then select View report.",
  "A filter does not apply to this report": "Choose the filters shown for this report, then select View report again.",
  "Choose valid report filters without repeated fields": "Open Reports again and choose the filters you need.",
  "Choose a recognized status or payment method": "Choose an order stage or payment method from the list.",
  "Choose a recognized attention list": "Choose what needs attention from the list.",
  "Choose a recognized expense category": "Choose an expense category from the list.",
  "Choose a paid date on or before today in Nairobi": "Choose today or an earlier paid date.",
  "Explain this correction": "Explain why this expense is being changed.",
  "Choose today or an earlier closing date": "Choose today or an earlier closing date.",
  "Explain the difference or why this day is being confirmed again": "Explain the money difference or why you are confirming this day again.",
  "Remove control characters": "Remove unusual control characters and try again.",
  "Orders can only move forward by one stage at a time": "Open Track orders to check the current stage. Use the next action shown on the order.",
  "Complete the pending clothing check before this order is ready": "Open the order and complete its clothing check before you mark it ready.",
  "Password cannot be blank": "Enter a password.",
  "Password must be at most 72 bytes": "This password is too long. Use a shorter password.",
  "Enter the customer's phone number": "Enter the customer's phone number.",
  "Use numbers, spaces or dashes only": "Enter the phone number using numbers, spaces or dashes only.",
  "Enter a Kenyan mobile number such as 0712 345 678": "Enter a Kenyan mobile number such as 0712 345 678.",
  "This phone number is already saved. Check the matching customer before creating another record.": "This phone number is already saved. Choose the matching customer, or create a separate record if people share the number.",
  "The linked garment was not found": "This clothing item is not available. Choose it again from the service list.",
  "A clothing item was not found": "A clothing item is not available. Ask the owner to check Shop setup.",
};

function inputMessage(detail) {
  if (typeof detail !== "string") return "";
  const message = detail.replace(/^Value error, /, "");
  if (Object.hasOwn(INPUT_MESSAGES, message)) return INPUT_MESSAGES[message];

  // Match known business rules without displaying arbitrary server text or names.
  if (/^Payment cannot exceed the remaining balance of KES \d+(\.\d+)?$/.test(message)) {
    return "Check the balance on the order. Enter a payment that does not exceed it.";
  }
  if (/^Record the remaining payment of KES \d+(\.\d+)? before collection$/.test(message)) {
    return "Open the order and record the remaining payment before you mark it collected.";
  }
  if (/ requires a whole-number quantity$/.test(message)) {
    return "Enter a whole number for items or pairs, such as 1 or 2.";
  }
  if (/^Discount for .+ must be less than its subtotal$/.test(message)) {
    return "Enter a discount smaller than the service total.";
  }
  if (/ is inactive and cannot be (added|linked)$/.test(message)) {
    return "This clothing item is turned off. Choose an active item or ask the owner to turn it on.";
  }
  if (/ is not in the .+ list$/.test(message)) {
    return "Choose a clothing item from the list for this service.";
  }
  return "";
}

const FIELD_NAMES = {
  username: "username", password: "password", name: "name", phone: "phone number",
  quantity: "quantity", amount: "payment amount", unit_price: "price",
  customer_id: "customer", service_id: "service", item_type_id: "clothing item",
  order_date: "order date", received_date: "payment date", promised_ready_at: "ready time",
  discount_amount: "discount", discount_reason: "discount reason",
  employee_max_discount_percent: "employee discount limit", expected_revision: "saved policy version",
  service_lines: "services", items: "clothing items", turnaround_minutes: "service time",
};

const REJECTED_SAVE_MESSAGES = {
  "QLMS-DISCOUNT-LIMIT": "The total discount is above the employee limit. This order was not saved. Reload to check the latest limit, then reduce the discount or ask an owner to create the order.",
  "QLMS-STALE-RECORD": "These details changed. Your changes were not saved. Reload this page, check the latest details, then enter your correction again.",
  "QLMS-PHONE-SHARED": "This phone number is already saved for another customer. Your changes were not saved. Check the matching customer, or confirm that they share this number.",
};

export function responseError(status, payload, path, recovery) {
  // A known rejection is safe to edit; an unknown conflict may follow a lost reply.
  if (status === 409) {
    const detail = payload?.detail;
    if (detail?.save_state === "not_saved" && Object.hasOwn(REJECTED_SAVE_MESSAGES, detail.code)) {
      if (path === '/daily-close' && detail.code === 'QLMS-STALE-RECORD') {
        const message = detail.message === 'Confirm who paid each unconfirmed cash expense before closing'
          ? 'Confirm who paid the listed cash expenses, then reload this day. Your closing was not saved.'
          : 'The day changed before confirmation. Your closing was not saved. Reload the figures and review your counts before confirming again.';
        return new ApiError(message,status,detail.code,'not_saved');
      }
      return new ApiError(REJECTED_SAVE_MESSAGES[detail.code], status, detail.code, "not_saved");
    }
    if (detail?.code === "QLMS-SAVE-CONFLICT") {
      return new ApiError(INPUT_MESSAGES["This save reference was already used for different details"], status, detail.code);
    }
  }
  if (status === 401) {
    return new ApiError(
      path === "/auth/login"
        ? "Check your username and password. If you still cannot sign in, ask the owner to check your account."
        : "Enter your password to continue. If you cannot sign in, ask the owner to check your account.",
      status, "QLMS-SIGNIN",
    );
  }
  if (status === 403) {
    return new ApiError("You cannot use this action with your account. Ask the owner for help.", status, "QLMS-ACCESS");
  }
  if (status === 404) {
    const missingMessages = {
      "Order not found": "This order is not available. Find it again in Track orders.",
      "Customer not found": "This customer is not available. Find the customer again in Customers.",
      "User not found": "This staff account is not available. Open Staff and check the account list.",
      "Service not found": "This service is not available. Ask the owner to check Shop setup.",
      "Clothing item not found": "This clothing item is not available. Ask the owner to check Shop setup.",
      "Order service not found": "This service is not on the order. Open the order again to check its services.",
      "Selected customer or service was not found": "Choose the customer or service again in Reports.",
      "Unknown report": "Open Reports and choose a report from the list.",
      "Expense not found": "This expense is not available. Open Expense history in Reports and select it again.",
      "Cash movement not found": "This cash movement is not available. Open Cash added and Owner withdrawals in Reports and select it again.",
    };
    const detail = payload?.detail;
    return new ApiError(
      typeof detail === "string" && Object.hasOwn(missingMessages, detail)
        ? missingMessages[detail]
        : "QLMS could not find this page or action. Contact support.",
      status, "QLMS-NOTFOUND",
    );
  }
  if (status === 429) {
    if (path === "/auth/login") {
      return new ApiError("Too many sign-in attempts. Wait up to five minutes, then try signing in again.", status, "QLMS-LOGIN-LIMIT");
    }
    return new ApiError(`QLMS is busy. Wait one minute. ${recovery} Contact support if this continues.`, status, "QLMS-BUSY");
  }
  if (status === 413 && path.startsWith("/dashboard/reports/")) {
    return new ApiError("This report is too large. Choose a shorter date range or fewer records, then select View report. Nothing was cut from the download.", status, "QLMS-REPORT-LIMIT");
  }
  if (status >= 500) {
    return new ApiError(`QLMS is not available right now. ${recovery} Contact support if this continues.`, status, "QLMS-SERVICE");
  }
  if ([400, 409, 422].includes(status)) {
    let message = inputMessage(payload?.detail);
    if (Array.isArray(payload?.detail)) {
      const messages = payload.detail.map((item) => {
        const known = inputMessage(item?.msg);
        if (known) return known;
        const key = Array.isArray(item?.loc) ? item.loc.at(-1) : "";
        const field = Object.hasOwn(FIELD_NAMES, key) ? FIELD_NAMES[key] : "";
        return field ? `Check the ${field} you entered.` : "Check the details you entered.";
      });
      message = [...new Set(messages)].slice(0, 3).join(" ");
    }
    return new ApiError(message || "Check the details you entered. Contact support if you cannot continue.", status, "QLMS-INPUT");
  }
  return new ApiError(`QLMS could not complete this action. ${recovery} Contact support.`, status, "QLMS-REQUEST");
}
