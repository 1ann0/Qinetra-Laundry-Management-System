// Keep help tied to controls the person can actually see on this page.
const PAGE_HELP = {
  "/workspace": [
    {targetId: "quick-find", title: "Find what you need", description: "Type a name, phone, ticket or service. Open a match to see its history or receipt."},
    {targetId: "daily-shortcuts", title: "Choose your next task", description: "Use New order for incoming laundry. Use Track orders to follow work already saved."},
  ],
  "/customers": [
    {targetId: "customer-add-step", title: "Check the customer details", description: "Enter the customer's name and Kenyan mobile number. Check both with the customer before saving."},
    {targetId: "customer-add-step", title: "Check a matching phone", description: "A matching number may belong to an existing customer or people sharing a phone. Check who they are before creating another record."},
  ],
  "/customers/search": [
    {targetId: "customer-search-step", title: "Find the right person", description: "Search by name or phone. Check the name and number, then choose View history."},
    {targetId: "service-history-step", title: "Find orders for a service", description: "Choose a service and select View service history to see its tickets."},
    {targetId: "customer-history-step", title: "Narrow down the history", description: "Choose dates, service or stage. Open a ticket to see its clothes, payments and receipt."},
  ],
  "/customers/contact": [
    {targetId: "customer-contact-step", title: "Correct the same customer", description: "Check the saved customer first. Explain the change and confirm the new details belong to this person. Their orders stay with this record."},
    {targetId: "customer-contact-history-step", title: "See previous changes", description: "The history shows what changed and why. It helps the owner check a correction later."},
  ],
  "/orders": [
    {targetId: "order-customer-step", title: "Choose the customer", description: "Search by name or phone. Check you have the right person before adding their laundry."},
    {targetId: "order-services-step", title: "Add the laundry", description: "Find a service and add it. Record the weight or pieces and any damage. Different services can share one ticket."},
    {targetId: "order-completion-step", title: "Agree on a ready time", description: "Check the suggested time with the customer. Change it if the shop needs longer."},
    {targetId: "order-payment-step", title: "Record money received", description: "Choose Cash or M-PESA only after confirming the payment. A deposit leaves the rest to pay later."},
    {targetId: "order-review-step", title: "Check, then save", description: "Check the customer, clothes, price and ready time. Select Create order once. If the result is uncertain, use Retry previous save."},
  ],
  "/orders/status": [
    {targetId: "status-search-step", title: "Find an order", description: "Search by ticket, customer, phone or service."},
    {targetId: "status-stages-step", title: "Choose a stage", description: "Select View orders for a stage. View all orders shows every match."},
    {targetId: "status-focus-step", title: "See what needs attention", description: "Find work due today, late work, money still owed or clothes waiting too long for collection."},
    {targetId: "status-board-step", title: "Check before moving forward", description: "Check the customer's name and clothes, then use the next-stage button. Open the receipt to record payments or handle a hold."},
  ],
  "/orders/receipt": [
    {targetId: "receipt-summary-step", title: "Check the ticket and clothes", description: "Check the customer, services, garment details, ready time and balance before changing this order."},
    {targetId: "receipt-hold-step", title: "Pause when an answer is needed", description: "Use a customer hold when work needs their answer. Record their answer before continuing."},
    {targetId: "receipt-payments-step", title: "Check money received", description: "Read the payment history first. Add only a confirmed payment and check the date and amount. Owner corrections keep a history."},
  ],
  "/dashboard": [
    {targetId: "dashboard-attention-step", title: "Choose what needs attention", description: "Open a list to see due laundry, late work, uncollected clothes or money still owed. These are the shop's current tickets."},
    {targetId: "dashboard-money-step", title: "Choose the money dates", description: "Apply dates to see cash, M-Pesa and returns in that period. Payments received are not profit; costs matter too."},
    {targetId: "dashboard-export-step", title: "Check and download this report", description: "Open the report for the displayed dates, then save Excel or CSV. Spreadsheet edits do not change QLMS."},
    {targetId: "dashboard-expenses-step", title: "Check what the shop spent", description: "Expense totals use the displayed paid dates. Open the history to check costs and corrections, or record an expense. Money received is still not profit."},
  ],
  "/reports": [
    {targetId: "reports-filters-step", title: "Choose the records", description: "Choose a report, then search for a customer or service and set any dates. Select View report to apply the choices."},
    {targetId: "reports-preview-step", title: "Check the meaning", description: "Work uses booking dates; payments use received dates. Current balances show what is owed now, even when you choose older dates."},
    {targetId: "reports-download-step", title: "Save a spreadsheet", description: "Download Excel or CSV from the displayed report. On a phone, look in Files, then Downloads. Editing that file does not change QLMS."},
  ],
  "/expenses": [
    {targetId: "expense-entry-step", title: "Record money already spent", description: "Choose when it was paid and what it was for. Paid using is Cash or M-Pesa; Paid from is shop money or the Owner's own money. Save once. If the reply is uncertain, use Retry previous save."},
    {targetId: "expense-history-step", title: "Correct without deleting", description: "Open an expense from Reports. Explain any correction. Reverse an incorrect entry to exclude it from totals; its original details and history remain."},
  ],
  "/daily-close": [
    {targetId: "close-date-step", title: "Choose the day", description: "Choose the Nairobi business date and load its records. Confirm who paid any unconfirmed cash expenses first; personal costs must not reduce the till."},
    {targetId: "close-activity-step", title: "Check what is recorded", description: "Check payments, returns, shop cash costs and cash movements. Add Owner withdrawals separately from expenses. Open a linked record to correct it, then reload this day."},
    {targetId: "close-counts-step", title: "Enter the real counts", description: "Enter opening and counted cash yourself. Use M-Pesa statement collections and returns, not the account balance. Enter 0 when there was none."},
    {targetId: "close-comparison-step", title: "Explain and confirm", description: "Short means counted cash is less than expected. Explain differences, then confirm once as Owner. If the reply is uncertain, retry the same save."},
    {targetId: "close-history-step", title: "Keep the original check", description: "Later changes show Needs review. Confirm again after checking the new figures; every earlier Owner confirmation remains in history."},
  ],
  "/till-movements": [
    {targetId: "movement-entry-step", title: "Record cash entering or leaving", description: "Choose Cash added to the till or Owner withdrawal. Purchases and wages belong in Expenses; do not record the same payment twice. Return to Close the day and reload its figures."},
    {targetId: "movement-history-step", title: "Correct with history", description: "Explain any correction or reversal. The original movement stays visible, and an affected daily closing will need review."},
  ],
  "/finance": [
    {targetId: "finance-period-step", title: "Choose the dates", description: "Choose a quick period or enter start and end dates. Apply the dates before reading the figures."},
    {targetId: "finance-figures-step", title: "Separate work from money", description: "Orders booked shows work sold. Payments received shows money received in the selected period. Money received is not profit."},
    {targetId: "finance-definitions-step", title: "Check what each figure means", description: "Read these definitions before comparing totals. Current balances can include later payments or refunds; they are not old balances for the selected end date."},
  ],
  "/staff": [
    {targetId: "staff-add-step", title: "Create a staff login", description: "Give each employee their own username and password. Keep the owner's login private."},
    {targetId: "staff-list-step", title: "Find who has access", description: "Search by username or role. Active staff can sign in; inactive staff cannot."},
    {targetId: "staff-security-step", title: "Change access safely", description: "Reset a forgotten password or turn off a staff login that should no longer have access."},
  ],
  "/settings/catalog": [
    {targetId: "catalogue-services", title: "Find a service or its history", description: "Search by service name or code. Order history opens its saved tickets. Price changes apply to new orders."},
    {targetId: "catalogue-clothing", title: "Find a clothing name", description: "Search the laundry and dry-cleaning lists. Deactivate an item to hide it from new entries without removing old records."},
    {targetId: "alert-settings-title", title: "Check backup preferences", description: "These are saved preferences. A saved email or time does not mean backups or alerts are running; they need separate setup and verification."},
  ],
};

export function availableHelpSteps(pathname, isVisible) {
  return (PAGE_HELP[pathname] || []).filter(step => isVisible(step.targetId));
}
