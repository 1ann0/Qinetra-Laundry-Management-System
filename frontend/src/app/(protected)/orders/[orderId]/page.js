"use client";

import { getUserMessage } from "@/lib/user-messages";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import ServiceItemEntry, {
  createBlankGarment,
  createBlankTallyException,
} from "@/components/orders/service-item-entry";
import { useAuth } from "@/context/auth-context";
import usePendingSave from "@/components/orders/use-pending-save";
import PendingSaveNotice from "@/components/orders/pending-save-notice";
import OutsourceRegister from "@/components/orders/outsource-register";
import PaymentCorrections from "@/components/orders/payment-corrections";
import OrderCorrections from "@/components/orders/order-corrections";
import QuantityCorrection from "@/components/orders/quantity-correction";
import CustomerReassignment from "@/components/orders/customer-reassignment";
import { buildOrderReceiptMessage } from "@/lib/order-receipt";
import { formatNairobiDateTime } from "@/lib/format-nairobi";

// Keep money and dates readable on the receipt.
function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function getNairobiToday() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function formatDate(value) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeZone: "Africa/Nairobi",
  }).format(new Date(`${value}T12:00:00+03:00`));
}

function getStatusLabel(status) {
  if (status === "cancelled") return "Cancelled";
  if (status === "in_progress") return "In Progress";
  if (status === "ready") return "Ready for Collection";
  if (status === "collected") return "Collected";
  return "Received";
}

function getPaymentLabel(status) {
  if (status === "settled") return "Settled";
  if (status === "refund_due") return "Refund due to customer";
  if (status === "cancelled") return "Cancelled";
  if (status === "part_paid") return "Part paid";
  if (status === "paid") return "Paid";
  return "Not paid";
}

function getPaymentMethodLabel(method) {
  if (method === "mpesa") return "M-PESA";
  if (method === "legacy") return "Previous payment record";
  return "Cash";
}

// Convert common Kenyan phone formats into the number expected by WhatsApp.
function getWhatsAppNumber(phone) {
  const digits = String(phone || "").replace(/\D/g, "");

  if (digits.startsWith("0") && digits.length === 10) {
    return `254${digits.slice(1)}`;
  }

  if (digits.startsWith("254") && digits.length === 12) {
    return digits;
  }

  return "";
}

// Turn saved API items back into the fields used by the clothing editor.
function createEditableItems(serviceLine) {
  if (serviceLine.item_recording_mode === "tally") {
    return serviceLine.items.map((item) => ({
      item_type_id: item.item_type_id,
      quantity: item.quantity,
      exceptions: (item.exceptions || []).map((exception, index) => ({
        ...createBlankTallyException(index + 1),
        description: exception.description || "",
        is_damaged: Boolean(exception.is_damaged),
        damage_note: exception.damage_note || "",
        stain_note: exception.stain_note || "",
      })),
    }));
  }

  const editableItems = serviceLine.items.map((item, index) => ({
    localId: index + 1,
    existing_item_id: item.id,
    garment_reference: item.garment_reference,
    item_type_id: String(item.item_type_id),
    description: item.description || "",
    is_damaged:
      item.is_damaged === null ? "" : String(Boolean(item.is_damaged)),
    damage_note: item.damage_note || "",
    stain_note: item.stain_note || "",
  }));
  const requiredQuantity = Number(serviceLine.quantity);

  while (editableItems.length < requiredQuantity) {
    editableItems.push(
      createBlankGarment(
        editableItems.length + 1,
        serviceLine.fixed_item_type_id || "",
      ),
    );
  }
  return editableItems;
}

// Validate a completed check before replacing its saved rows.
function getItemError(serviceLine, items) {
  if (serviceLine.item_recording_mode === "tally" && items.length === 0) {
    return `Record at least one clothing item for ${serviceLine.service_name}.`;
  }

  if (serviceLine.item_recording_mode === "tally") {
    for (const item of items) {
      for (const [index, exception] of (item.exceptions || []).entries()) {
        if (exception.is_damaged && !exception.damage_note.trim()) {
          return `Describe the existing damage for condition note ${index + 1}.`;
        }
        if (
          !exception.description.trim() &&
          !exception.is_damaged &&
          !exception.stain_note.trim()
        ) {
          return `Complete or remove condition note ${index + 1}.`;
        }
      }
    }
  }

  if (serviceLine.item_recording_mode === "detailed") {
    if (items.length < Number(serviceLine.quantity)) {
      return `Record at least ${serviceLine.quantity} physical pieces for ${serviceLine.service_name}.`;
    }

    for (const [index, item] of items.entries()) {
      if (!item.item_type_id) {
        return `Select the clothing type for garment ${index + 1}.`;
      }
      if (item.is_damaged === "") {
        return `Confirm whether garment ${index + 1} is already damaged.`;
      }
      if (!item.description.trim()) {
        return `Describe garment ${index + 1} so it can be identified.`;
      }
    }
  }
  return "";
}

export default function OrderDetailPage() {
  const { authenticatedRequest, role, reauthenticationRequired } = useAuth();
  const loadedOrderId = useRef(null);
  const params = useParams();
  const orderId = Number(params.orderId);

  // Store the complete receipt, matching customer and active clothing choices.
  const [order, setOrder] = useState(null);
  const [customer, setCustomer] = useState(null);
  const [customerOptions, setCustomerOptions] = useState([]);
  const [itemTypes, setItemTypes] = useState([]);

  // Keep one service editor open at a time.
  const [editingLineId, setEditingLineId] = useState(null);
  const [editingRevision, setEditingRevision] = useState(0);
  const [draftItems, setDraftItems] = useState([]);
  const [changeReason, setChangeReason] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Payments are appended to history instead of changing an earlier record.
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentReceivedDate, setPaymentReceivedDate] =
    useState(getNairobiToday);
  const [paymentConfirmed, setPaymentConfirmed] = useState(false);
  const paymentSave = usePendingSave(`/orders/${orderId}/payments`);
  const isRecordingPayment = paymentSave.isSaving;
  const [shareError, setShareError] = useState("");
  const [holdReason, setHoldReason] = useState("");
  const [resolutionNote, setResolutionNote] = useState("");
  const [holdAction, setHoldAction] = useState("");

  // Load the receipt and lookup data without requiring customer information in the URL.
  useEffect(() => {
    if (reauthenticationRequired) return;
    let ignore = false;
    async function loadOrderDetails() {
      if (!Number.isInteger(orderId) || orderId <= 0) {
        setError("This order link is not valid. Open Track orders and find the order again.");
        setIsLoading(false);
        return;
      }

      try {
        const [orderResponse, customerResponse, itemResponse] =
          await Promise.all([
            authenticatedRequest(`/orders/${orderId}`),
            authenticatedRequest("/customers"),
            authenticatedRequest("/catalog/item-types?include_inactive=true"),
          ]);
        if (ignore) return;
        setOrder(orderResponse);
        setCustomerOptions(customerResponse);
        if (loadedOrderId.current !== orderId) setPaymentAmount(String(orderResponse.balance_due));
        loadedOrderId.current = orderId;
        setCustomer(
          customerResponse.find(
            (item) => item.id === orderResponse.customer_id,
          ) || null,
        );
        setItemTypes(itemResponse);
        setError("");
      } catch (loadError) {
        if (!ignore) setError(getUserMessage(loadError, "The order receipt could not be loaded."));
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    loadOrderDetails();
    return () => { ignore = true; };
  }, [authenticatedRequest, orderId, reauthenticationRequired]);

  // Open the selected service with its current saved clothing records.
  function startItemEdit(serviceLine) {
    setEditingLineId(serviceLine.id);
    setEditingRevision(serviceLine.item_revision);
    setDraftItems(createEditableItems(serviceLine));
    setChangeReason("");
    setError("");
    setMessage("");
  }

  function replaceServiceLine(savedLine) {
    setOrder((currentOrder) => ({
      ...currentOrder,
      service_lines: currentOrder.service_lines.map((line) =>
        line.id === savedLine.id ? savedLine : line,
      ),
    }));
  }

  // Add a missing Laundry choice while completing a saved order's item check.
  async function addMissingTallyItem(name) {
    const savedItem = await authenticatedRequest("/catalog/item-types", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, item_group: "laundry" }),
    });

    setItemTypes((currentItems) =>
      currentItems.some((item) => item.id === savedItem.id)
        ? currentItems
        : [...currentItems, savedItem],
    );
    return savedItem;
  }

  // Send the complete replacement list to FastAPI and update the visible receipt.
  async function saveItems(serviceLine) {
    const validationError = getItemError(serviceLine, draftItems);
    if (validationError) {
      setError(validationError);
      return;
    }

    const requestItems =
      serviceLine.item_recording_mode === "detailed"
        ? draftItems.map((item) => ({
            existing_item_id: item.existing_item_id,
            item_type_id: Number(item.item_type_id),
            quantity: 1,
            description: item.description.trim() || null,
            is_damaged: item.is_damaged === "true",
            damage_note:
              item.is_damaged === "true"
                ? item.damage_note.trim() || null
                : null,
            stain_note: item.stain_note.trim() || null,
          }))
        : draftItems.map((item) => ({
            item_type_id: item.item_type_id,
            quantity: item.quantity,
            description: null,
            is_damaged: null,
            damage_note: null,
            stain_note: null,
            exceptions: (item.exceptions || []).map((exception) => ({
              description: exception.description.trim() || null,
              is_damaged: exception.is_damaged,
              damage_note: exception.is_damaged
                ? exception.damage_note.trim() || null
                : null,
              stain_note: exception.stain_note.trim() || null,
            })),
          }));

    if (
      serviceLine.item_check_status === "completed" &&
      !changeReason.trim()
    ) {
      setError("Explain why the completed clothing check needs to change.");
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const savedLine = await authenticatedRequest(
        `/orders/${order.id}/services/${serviceLine.id}/items`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: requestItems,
            expected_revision: editingRevision,
            change_reason:
              serviceLine.item_check_status === "completed"
                ? changeReason.trim()
                : null,
          }),
        },
      );

      replaceServiceLine(savedLine);
      setEditingLineId(null);
      setDraftItems([]);
      setChangeReason("");
      setMessage(`${serviceLine.service_name} item check saved.`);
    } catch (saveError) {
      setError(getUserMessage(saveError, "QLMS could not confirm the clothing changes. Check the order before you save again."));
    } finally {
      setIsSaving(false);
    }
  }

  // Add a confirmed cash or M-PESA amount and let the backend calculate the balance.
  async function recordPayment(event) {
    event.preventDefault();
    const amount = Number(paymentAmount);

    if (!Number.isFinite(amount) || amount <= 0) {
      setError("Enter the payment amount received.");
      return;
    }

    if (amount > Number(order.balance_due)) {
      setError(
        `Payment cannot be more than the ${formatKes(order.balance_due)} balance.`,
      );
      return;
    }

    if (!paymentReceivedDate) {
      setError("Select the date the payment was received.");
      return;
    }

    if (paymentReceivedDate < order.order_date) {
      setError("The payment date cannot be before the order date.");
      return;
    }

    if (paymentReceivedDate > getNairobiToday()) {
      setError("The payment date cannot be in the future.");
      return;
    }

    if (!paymentConfirmed) {
      setError(
        paymentMethod === "cash"
          ? "Confirm that the cash was received."
          : "Confirm the M-PESA message on the official business phone.",
      );
      return;
    }

    setError("");
    setMessage("");

    try {
      finishPayment(await paymentSave.save({
            payment_method: paymentMethod,
            amount,
            confirmed: true,
            received_date: paymentReceivedDate,
      }));
    } catch (paymentError) {
      setError(getUserMessage(paymentError, "QLMS could not confirm the payment. Use Retry previous save."));
    }
  }

  async function retryPayment() {
    setError("");
    setMessage("");
    try {
      finishPayment(await paymentSave.retry());
    } catch (paymentError) {
      setError(getUserMessage(paymentError));
    }
  }

  function finishPayment(updatedOrder) {
      setOrder((current) => current?.id === updatedOrder.id ? updatedOrder : current);
      setPaymentAmount(String(updatedOrder.balance_due));
      setPaymentConfirmed(false);
      setPaymentReceivedDate(getNairobiToday());
      setMessage("Payment saved. Check the payment history below.");
  }

  async function placeCustomerHold(event) {
    event.preventDefault();
    if (!holdReason.trim()) {
      setError("Enter what needs the customer's reply.");
      return;
    }

    setHoldAction("placing");
    setError("");
    setMessage("");
    try {
      const updatedOrder = await authenticatedRequest(
        `/orders/${order.id}/holds`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: holdReason.trim() }),
        },
      );
      setOrder(updatedOrder);
      setHoldReason("");
      setMessage("Customer reply hold added. This order cannot move forward yet.");
    } catch (holdError) {
      setError(getUserMessage(
        holdError,
        "The hold could not be confirmed. Open the order again before you continue.",
      ));
    } finally {
      setHoldAction("");
    }
  }

  async function resolveCustomerHold(event, holdId) {
    event.preventDefault();
    if (!resolutionNote.trim()) {
      setError("Enter what the customer confirmed.");
      return;
    }

    setHoldAction("resolving");
    setError("");
    setMessage("");
    try {
      const updatedOrder = await authenticatedRequest(
        `/orders/${order.id}/holds/${holdId}/resolve`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resolution_note: resolutionNote.trim() }),
        },
      );
      setOrder(updatedOrder);
      setResolutionNote("");
      setMessage("Customer reply recorded. The hold is closed.");
    } catch (holdError) {
      setError(getUserMessage(
        holdError,
        "The customer's reply could not be confirmed. Open the order again before you continue.",
      ));
    } finally {
      setHoldAction("");
    }
  }

  // Prepare a receipt or ready notice while leaving the final Send action to staff.
  function shareOnWhatsApp() {
    const phone = getWhatsAppNumber(customer?.phone);

    if (!phone) {
      setShareError(
        "The customer phone number is not in a valid Kenyan format.",
      );
      return;
    }

    const text = buildOrderReceiptMessage(order, customer?.name);

    setShareError("");
    window.open(
      `https://wa.me/${phone}?text=${encodeURIComponent(text)}`,
      "_blank",
      "noopener,noreferrer",
    );
  }

  if (isLoading) {
    return (
      <p className="mx-auto max-w-5xl rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-600">
        Loading order receipt…
      </p>
    );
  }

  if (!order) {
    return (
      <section className="mx-auto max-w-3xl rounded-2xl border border-red-300 bg-red-50 p-6">
        <h1 className="text-2xl font-bold text-slate-900">
          Order could not be opened
        </h1>
        <p className="mt-3 text-red-800">{error}</p>
        <Link
          className="mt-5 inline-block font-bold text-[#005AAB] hover:underline"
          href="/orders/status"
        >
          Return to status tracking
        </Link>
      </section>
    );
  }

  const canEditItems =
    order.status === "received" || order.status === "in_progress";
  const activeHold = (order.holds || []).find((hold) => !hold.resolved_at);
  const resolvedHolds = (order.holds || []).filter((hold) => hold.resolved_at);

  return (
    <section className="mx-auto max-w-5xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
            Individual order
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Receipt {order.ticket_number}
          </h1>
          <p className="mt-3 text-slate-600">
            Review the services, clothing records and current order stage.
          </p>
        </div>
        <div className="flex flex-col items-start gap-3 sm:items-end">
          {order.status !== "cancelled" ? <button
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782]"
            type="button"
            onClick={shareOnWhatsApp}
          >
            {order.status === "ready"
              ? "Share ready update on WhatsApp"
              : "Share receipt on WhatsApp"}
          </button> : null}
          <Link
            className="font-bold text-[#005AAB] hover:underline"
            href="/orders/status"
          >
            Back to status tracking
          </Link>
        </div>
      </div>

      {shareError ? (
        <p
          className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {shareError}
        </p>
      ) : null}

      {error ? (
        <p
          className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {message ? (
        <p
          className="mb-6 rounded-xl border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800"
          role="status"
        >
          {message}
        </p>
      ) : null}

      {activeHold ? (
        <section className="mb-6 rounded-2xl border-2 border-amber-400 bg-amber-50 p-5">
          <p className="text-sm font-bold uppercase tracking-wide text-amber-900">
            Waiting for customer reply
          </p>
          <h2 className="mt-2 text-xl font-bold text-slate-900">
            {activeHold.reason}
          </h2>
          <p className="mt-2 text-sm text-slate-700">
            Added by {activeHold.created_by_username} · {formatNairobiDateTime(activeHold.created_at)}
          </p>
          <p className="mt-2 text-sm font-semibold text-amber-950">
            Do not move this order forward until the customer answers.
          </p>
          <form
            className="mt-4"
            onSubmit={(event) => resolveCustomerHold(event, activeHold.id)}
          >
            <label
              className="block text-sm font-bold text-slate-800"
              htmlFor="customer-hold-resolution"
            >
              What did the customer confirm?
            </label>
            <textarea
              className="mt-2 min-h-24 w-full rounded-xl border border-amber-300 bg-white p-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
              id="customer-hold-resolution"
              maxLength="300"
              value={resolutionNote}
              disabled={Boolean(holdAction)}
              onChange={(event) => setResolutionNote(event.target.value)}
            />
            <button
              className="mt-3 min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:opacity-50"
              type="submit"
              disabled={Boolean(holdAction)}
            >
              {holdAction === "resolving" ? "Closing hold…" : "Record reply and close hold"}
            </button>
          </form>
        </section>
      ) : canEditItems ? (
        <details className="mb-6 rounded-xl border border-slate-300 bg-white p-4">
          <summary className="cursor-pointer font-bold text-[#005AAB]">
            Wait for customer reply
          </summary>
          <form className="mt-4" onSubmit={placeCustomerHold}>
            <label
              className="block text-sm font-bold text-slate-800"
              htmlFor="customer-hold-reason"
            >
              What must the customer answer?
            </label>
            <textarea
              className="mt-2 min-h-24 w-full rounded-xl border border-slate-300 p-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
              id="customer-hold-reason"
              maxLength="300"
              placeholder="Example: Confirm whether bleach may be used on the white shirt"
              value={holdReason}
              disabled={Boolean(holdAction)}
              onChange={(event) => setHoldReason(event.target.value)}
            />
            <button
              className="mt-3 min-h-11 rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-50"
              type="submit"
              disabled={Boolean(holdAction)}
            >
              {holdAction === "placing" ? "Adding hold…" : "Add customer reply hold"}
            </button>
          </form>
        </details>
      ) : null}

      {resolvedHolds.length > 0 ? (
        <details className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <summary className="cursor-pointer font-bold text-[#005AAB]">
            Customer reply history ({resolvedHolds.length})
          </summary>
          <ol className="mt-4 space-y-4">
            {resolvedHolds.map((hold) => (
              <li className="text-sm text-slate-700" key={hold.id}>
                <p className="font-bold text-slate-900">Question: {hold.reason}</p>
                <p className="mt-1">Reply: {hold.resolution_note}</p>
                <p className="mt-1 text-xs text-slate-600">
                  Closed by {hold.resolved_by_username} · {formatNairobiDateTime(hold.resolved_at)}
                </p>
              </li>
            ))}
          </ol>
        </details>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="grid gap-5 border-b border-slate-200 pb-6 sm:grid-cols-2 lg:grid-cols-6">
          <div>
            <p className="text-sm text-slate-500">Customer</p>
            <p className="mt-1 font-bold text-slate-900">
              {customer?.name || `Customer ${order.customer_id}`}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Phone</p>
            <p className="mt-1 font-bold text-slate-900">
              {customer?.phone || "Not available"}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Order date</p>
            <p className="mt-1 font-bold text-slate-900">
              {formatDate(order.order_date)}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Status</p>
            <p className="mt-1 font-bold text-[#005AAB]">
              {getStatusLabel(order.status)}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Promised ready</p>
            <p className="mt-1 font-bold text-slate-900">
              {order.promised_ready_at
                ? formatNairobiDateTime(order.promised_ready_at)
                : "Older order; not set"}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Recorded in QLMS</p>
            <p className="mt-1 font-bold text-slate-900">
              {formatNairobiDateTime(order.created_at)}
            </p>
          </div>
        </div>

        {role === "owner" ? <CustomerReassignment
          order={order}
          customers={customerOptions}
          onUpdated={(updatedOrder) => {
            setOrder(updatedOrder);
            setCustomer(customerOptions.find((item) => item.id === updatedOrder.customer_id) || null);
            setMessage("Customer corrected. Check the ticket and correction history.");
          }}
        /> : null}

        {Number(order.discount_amount) > 0 ? (
          <div className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-4">
            <div className="flex flex-wrap justify-between gap-3">
              <span className="font-semibold text-slate-700">
                Catalogue subtotal: {formatKes(order.subtotal_before_discount)}
              </span>
              <span className="font-bold text-amber-900">
                Discount: -{formatKes(order.discount_amount)}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Reason: {order.discount_reason} · Recorded by {" "}
              {order.discounted_by_username}
            </p>
          </div>
        ) : null}

        <div className="mt-6 space-y-5">
          {order.service_lines.length === 0 ? (
            <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
              This older order uses the original single-service receipt format.
            </p>
          ) : (
            order.service_lines.map((serviceLine) => (
              <article
                className="rounded-xl border border-slate-200 p-4 sm:p-5"
                key={serviceLine.id}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">
                      {serviceLine.service_name}
                    </h2>
                    <p className="mt-1 text-sm text-slate-600">
                      {serviceLine.quantity} {serviceLine.service_unit} at{" "}
                      {formatKes(serviceLine.unit_price)}
                    </p>
                  </div>
                  <div className="text-right">
                    {Number(serviceLine.discount_amount) > 0 ? (
                      <p className="text-sm text-slate-500 line-through">
                        {formatKes(serviceLine.subtotal)}
                      </p>
                    ) : null}
                    <p className="font-bold text-slate-900">
                      {formatKes(serviceLine.line_total)}
                    </p>
                    {Number(serviceLine.discount_amount) > 0 ? (
                      <p className="mt-1 text-xs font-semibold text-amber-900">
                        Saved {formatKes(serviceLine.discount_amount)}
                      </p>
                    ) : null}
                    <span
                      className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-bold ${
                        serviceLine.item_check_status === "pending"
                          ? "bg-amber-100 text-amber-900"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {serviceLine.item_check_status === "pending"
                        ? "Item check pending"
                        : serviceLine.item_check_status === "completed"
                          ? "Item check complete"
                          : "No item check needed"}
                    </span>
                  </div>
                </div>

                {editingLineId === serviceLine.id ? (
                  <div className="mt-5 border-t border-slate-200 pt-5">
                    <ServiceItemEntry
                      recordingMode={serviceLine.item_recording_mode}
                      itemTypes={itemTypes}
                      items={draftItems}
                      disabled={isSaving}
                      fieldPrefix={`saved-service-${serviceLine.id}`}
                      allowedInactiveItemTypeIds={serviceLine.items.map(
                        (item) => item.item_type_id,
                      )}
                      fixedItemType={
                        serviceLine.fixed_item_type_id
                          ? itemTypes.find(
                              (itemType) =>
                                itemType.id ===
                                serviceLine.fixed_item_type_id,
                            ) || null
                          : null
                      }
                      onAddMissingItem={addMissingTallyItem}
                      onItemsChange={setDraftItems}
                    />
                    {serviceLine.item_check_status === "completed" ? (
                      <div className="mt-4">
                        <label
                          className="block text-sm font-bold text-slate-800"
                          htmlFor={`saved-service-${serviceLine.id}-change-reason`}
                        >
                          Why is this check changing?
                        </label>
                        <input
                          className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-2 focus:ring-blue-100"
                          id={`saved-service-${serviceLine.id}-change-reason`}
                          maxLength="200"
                          placeholder="Example: Customer confirmed one shirt was not theirs"
                          value={changeReason}
                          disabled={isSaving}
                          onChange={(event) => setChangeReason(event.target.value)}
                        />
                        <p className="mt-1 text-xs text-slate-600">
                          QLMS keeps the earlier check and this reason in the order history.
                        </p>
                      </div>
                    ) : null}
                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        className="min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:opacity-50"
                        type="button"
                        disabled={isSaving}
                        onClick={() => saveItems(serviceLine)}
                      >
                        {isSaving ? "Saving…" : "Save item check"}
                      </button>
                      <button
                        className="min-h-11 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50"
                        type="button"
                        disabled={isSaving}
                        onClick={() => {
                          setEditingLineId(null);
                          setDraftItems([]);
                          setChangeReason("");
                          setError("");
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    {serviceLine.items.length > 0 ? (
                      <ul className="mt-4 space-y-2 border-t border-slate-200 pt-4">
                        {serviceLine.items.map((item) => (
                          <li className="text-sm text-slate-700" key={item.id}>
                            <span className="font-bold text-slate-900">
                              {item.garment_reference
                                ? `${item.garment_reference} · `
                                : ""}
                              {item.quantity} × {item.item_name}
                            </span>
                            {item.description ? ` · ${item.description}` : ""}
                            {item.is_damaged === true
                              ? ` · Existing damage${item.damage_note ? `: ${item.damage_note}` : ""}`
                              : ""}
                            {item.stain_note
                              ? ` · Note: ${item.stain_note}`
                              : ""}
                            {(item.exceptions || []).length > 0 ? (
                              <ul className="mt-2 space-y-1 border-l-2 border-amber-300 pl-3">
                                {item.exceptions.map((exception, index) => (
                                  <li key={exception.id}>
                                    <span className="font-semibold text-amber-950">
                                      Condition note {index + 1}
                                    </span>
                                    {exception.description
                                      ? ` · ${exception.description}`
                                      : ""}
                                    {exception.is_damaged
                                      ? ` · Existing damage: ${exception.damage_note}`
                                      : ""}
                                    {exception.stain_note
                                      ? ` · Stain: ${exception.stain_note}`
                                      : ""}
                                  </li>
                                ))}
                              </ul>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    ) : null}

                    {serviceLine.item_checked_by_username ? (
                      <p className="mt-3 text-xs text-slate-600">
                        Last checked by {serviceLine.item_checked_by_username} ·{" "}
                        {formatNairobiDateTime(serviceLine.item_checked_at)}
                      </p>
                    ) : null}

                    {(serviceLine.item_history || []).length > 1 ? (
                      <details className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                        <summary className="cursor-pointer text-sm font-bold text-[#005AAB]">
                          Clothing check history ({serviceLine.item_history.length})
                        </summary>
                        <ol className="mt-3 space-y-3">
                          {serviceLine.item_history.map((entry) => (
                            <li className="text-sm text-slate-700" key={entry.id}>
                              <p className="font-semibold text-slate-900">
                                Version {entry.revision + 1} · {entry.changed_by_username}
                              </p>
                              <p className="text-xs text-slate-600">
                                {formatNairobiDateTime(entry.created_at)}
                              </p>
                              <p className="mt-1">
                                {(entry.item_snapshot || [])
                                  .map((item) => `${item.garment_reference ? `${item.garment_reference} · ` : ""}${item.quantity} × ${item.item_name}`)
                                  .join(", ") || "No clothing recorded"}
                              </p>
                              {entry.change_reason ? (
                                <p className="mt-1">Reason: {entry.change_reason}</p>
                              ) : null}
                            </li>
                          ))}
                        </ol>
                      </details>
                    ) : null}

                    {serviceLine.item_recording_mode !== "none" &&
                    canEditItems &&
                    !serviceLine.outsourcing_handover &&
                    !serviceLine.in_house_at ? (
                      <button
                        className="mt-4 font-bold text-[#005AAB] hover:underline"
                        type="button"
                        onClick={() => startItemEdit(serviceLine)}
                      >
                        {serviceLine.item_check_status === "pending"
                          ? "Complete item check"
                          : "Edit clothing items"}
                      </button>
                    ) : null}

                    <OutsourceRegister
                      orderId={order.id}
                      orderStatus={order.status}
                      serviceLine={serviceLine}
                      role={role}
                      authenticatedRequest={authenticatedRequest}
                      onServiceLineSaved={replaceServiceLine}
                    />
                  </>
                )}
              </article>
            ))
          )}
        </div>

        <div className="mt-6 grid gap-4 border-t border-slate-200 pt-6 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <p className="text-sm text-slate-500">Catalogue subtotal</p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              {formatKes(order.subtotal_before_discount)}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Discount</p>
            <p className="mt-1 text-xl font-bold text-amber-900">
              -{formatKes(order.discount_amount)}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">
              {order.status === "cancelled" ? "Original order total" : "Order total before refunds"}
            </p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              {formatKes(order.total_price)}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Money retained</p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              {formatKes(order.amount_paid)}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Balance</p>
            <p
              className={`mt-1 text-xl font-bold ${
                Number(order.balance_due) > 0
                  ? "text-red-700"
                  : "text-green-700"
              }`}
            >
              {formatKes(order.balance_due)}
            </p>
            <p className="mt-1 text-sm font-semibold text-slate-600">
              {getPaymentLabel(order.payment_status)}
            </p>
          </div>
          <div><p className="text-sm text-slate-500">Net charge</p><p className="mt-1 text-xl font-bold text-slate-900">{formatKes(order.net_charge)}</p></div>
          <div><p className="text-sm text-slate-500">Service refunds</p><p className="mt-1 text-xl font-bold text-slate-900">{formatKes(order.service_refunds)}</p></div>
          <div><p className="text-sm text-slate-500">Refund due to customer</p><p className="mt-1 text-xl font-bold text-amber-900">{formatKes(order.refund_due)}</p></div>
        </div>
      </section>

      {role === "owner" ? <QuantityCorrection order={order} onUpdated={(updatedOrder) => {
        setOrder(updatedOrder);
        setMessage("Quantity corrected. Check the new total and clothing record.");
      }} /> : null}

      <OrderCorrections
        order={order}
        isOwner={role === "owner"}
        onUpdated={(updatedOrder) => {
          setOrder(updatedOrder);
          setMessage("Order corrected. Check its stage and history.");
        }}
      />

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <h2 className="text-2xl font-bold text-slate-900">Payment history</h2>
        <p className="mt-2 text-slate-600">
          Each confirmed payment remains on the receipt for accountability.
        </p>

        {order.payments.length > 0 ? (
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-600">
                  <th className="px-3 py-3 font-semibold">Method</th>
                  <th className="px-3 py-3 font-semibold">Amount</th>
                  <th className="px-3 py-3 font-semibold">Confirmed by</th>
                  <th className="px-3 py-3 font-semibold">Received date</th>
                  <th className="px-3 py-3 font-semibold">Recorded in QLMS</th>
                </tr>
              </thead>
              <tbody>
                {order.payments.map((payment) => (
                  <tr className="border-b border-slate-100" key={payment.id}>
                    <td className="px-3 py-3 font-semibold text-slate-900">
                      {getPaymentMethodLabel(payment.payment_method)}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {formatKes(payment.amount)}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {payment.confirmed_by_username}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {formatDate(payment.received_date)}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {formatNairobiDateTime(payment.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 font-semibold text-amber-900">
            No payment has been recorded for this order.
          </p>
        )}

        <PaymentCorrections
          key={order.payments.find((payment) => payment.payment_method !== "legacy")?.id || 0}
          order={order}
          isOwner={role === "owner"}
          onUpdated={(updatedOrder) => {
            setOrder(updatedOrder);
            setPaymentAmount(String(updatedOrder.balance_due));
          }}
        />

        <PendingSaveNotice {...paymentSave} onRetry={retryPayment} />
        {Number(order.balance_due) > 0 && (order.status !== "collected" || role === "owner") ? (
          <form
            className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4 sm:p-5"
            onSubmit={recordPayment}
            noValidate
          >
            <fieldset disabled={isRecordingPayment || Boolean(paymentSave.pending) || !paymentSave.ready}>
            <h3 className="text-lg font-bold text-slate-900">
              Record another payment
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              Remaining balance: {formatKes(order.balance_due)}
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label
                  className="block font-semibold text-slate-800"
                  htmlFor="payment_method"
                >
                  Payment method
                </label>
                <select
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                  id="payment_method"
                  value={paymentMethod}
                  disabled={isRecordingPayment}
                  onChange={(event) => {
                    setPaymentMethod(event.target.value);
                    setPaymentConfirmed(false);
                    setError("");
                  }}
                >
                  <option value="cash">Cash</option>
                  <option value="mpesa">M-PESA Paybill</option>
                </select>
              </div>

              <div>
                <label
                  className="block font-semibold text-slate-800"
                  htmlFor="payment_amount"
                >
                  Amount received (KES)
                </label>
                <input
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                  id="payment_amount"
                  type="number"
                  min="1"
                  max={order.balance_due}
                  step="1"
                  value={paymentAmount}
                  disabled={isRecordingPayment}
                  onChange={(event) => {
                    setPaymentAmount(event.target.value);
                    setError("");
                  }}
                />
              </div>

              <div>
                <label
                  className="block font-semibold text-slate-800"
                  htmlFor="payment_received_date"
                >
                  Date received
                </label>
                <input
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                  id="payment_received_date"
                  type="date"
                  min={order.order_date}
                  max={getNairobiToday()}
                  value={paymentReceivedDate}
                  disabled={isRecordingPayment}
                  onChange={(event) => {
                    setPaymentReceivedDate(event.target.value);
                    setError("");
                  }}
                />
              </div>
            </div>

            <button
              className="mt-3 text-sm font-bold text-[#005AAB] hover:underline"
              type="button"
              disabled={isRecordingPayment}
              onClick={() => setPaymentAmount(String(order.balance_due))}
            >
              Use full remaining balance
            </button>

            <label className="mt-4 flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm font-semibold text-amber-950">
              <input
                className="mt-1"
                type="checkbox"
                checked={paymentConfirmed}
                disabled={isRecordingPayment}
                onChange={(event) => {
                  setPaymentConfirmed(event.target.checked);
                  setError("");
                }}
              />
              {paymentMethod === "cash"
                ? "I have received this cash from the customer."
                : "I have seen the confirmed payment message on Qinetra Laundry’s official business phone."}
            </label>

            <button
              className="mt-4 inline-flex min-h-11 items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:opacity-60"
              type="submit"
              disabled={isRecordingPayment}
            >
              {isRecordingPayment ? "Saving payment…" : "Record payment"}
            </button>
          </fieldset>
          </form>
        ) : order.status === "cancelled" ? (
          <p className="mt-5 rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 font-semibold text-slate-800">
            This ticket was cancelled. No balance is due.
          </p>
        ) : Number(order.refund_due) > 0 ? (
          <p className="mt-5 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 font-semibold text-amber-900">
            The customer is owed {formatKes(order.refund_due)}. The owner should record the excess payment return after returning the money.
          </p>
        ) : Number(order.balance_due) === 0 ? (
          <p className="mt-5 rounded-xl border border-green-300 bg-green-50 px-4 py-3 font-semibold text-green-800">
            {order.status === "collected" ? "No balance due. Clothing already collected." : "No balance due. This order can be collected when it is ready."}
          </p>
        ) : null}

        <p className="mt-5 text-sm text-slate-600">
          WhatsApp sharing opens a prepared message. Staff check it before
          pressing Send.
        </p>
      </section>
    </section>
  );
}
