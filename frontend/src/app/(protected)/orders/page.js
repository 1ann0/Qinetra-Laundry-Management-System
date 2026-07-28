"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ServiceItemEntry, {
  createBlankGarment,
} from "@/components/orders/service-item-entry";
import { useAuth } from "@/context/auth-context";

const SUIT_BAG_CODE = "dry_cleaning_suit_bag";
const SUIT_BAG_PROMPT_CODES = new Set([
  "dry_cleaning_suit",
  "dry_cleaning_3_piece_suit",
  "dry_cleaning_suit_coat_school_blazer",
  "dry_cleaning_coloured_suit_coat",
  "dry_cleaning_trench_coat",
]);

// Display prices in the same KES format throughout this screen.
function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

// Empty optional text becomes null in the API request.
function cleanOptionalText(value) {
  const cleaned = value.trim();
  return cleaned || null;
}

// Build a selected service without changing its catalogue record.
function createServiceLine(service) {
  return {
    service_id: service.id,
    service_code: service.code,
    service_name: service.name,
    service_unit: service.unit,
    unit_price: Number(service.unit_price),
    category: service.category,
    fixed_item_type_id: service.default_item_type_id,
    item_recording_mode: service.item_recording_mode,
    quantity: "1",
    defer_items: false,
    items:
      service.item_recording_mode === "detailed"
        ? [createBlankGarment(1, service.default_item_type_id || "")]
        : [],
  };
}

// Dry Cleaning is the category, so employees only need the garment wording.
function getServiceDisplayName(service) {
  if (service.category === "dry_cleaning") {
    return service.name.replace(/^Dry Cleaning\s*-\s*/i, "");
  }
  return service.name;
}

// Detailed service quantity comes from its garment cards.
function getServiceQuantity(serviceLine) {
  return serviceLine.item_recording_mode === "detailed" &&
    !serviceLine.defer_items
    ? serviceLine.items.length
    : Number(serviceLine.quantity);
}

// Calculate only the employee's preview; FastAPI still confirms the final price.
function getServiceSubtotal(serviceLine) {
  const quantity = getServiceQuantity(serviceLine);
  return Number.isFinite(quantity) && quantity > 0
    ? serviceLine.unit_price * quantity
    : 0;
}

// Check all visible order values before sending them to FastAPI.
function getOrderError(customerId, serviceLines) {
  if (!customerId) {
    return "Select the customer for this order.";
  }

  if (serviceLines.length === 0) {
    return "Add at least one laundry service.";
  }

  for (const serviceLine of serviceLines) {
    const quantity = getServiceQuantity(serviceLine);

    if (!Number.isFinite(quantity) || quantity <= 0) {
      return `Enter a quantity greater than zero for ${serviceLine.service_name}.`;
    }

    if (
      serviceLine.item_recording_mode !== "detailed" &&
      serviceLine.service_unit !== "kg" &&
      !Number.isInteger(quantity)
    ) {
      return `${serviceLine.service_name} requires a whole-number quantity.`;
    }

    if (
      !serviceLine.defer_items &&
      serviceLine.item_recording_mode === "tally" &&
      serviceLine.items.length === 0
    ) {
      return `Record at least one clothing item for ${serviceLine.service_name}.`;
    }

    if (
      !serviceLine.defer_items &&
      serviceLine.item_recording_mode === "detailed"
    ) {
      for (const [index, item] of serviceLine.items.entries()) {
        if (!item.item_type_id) {
          return `Select the clothing type for garment ${index + 1} in ${serviceLine.service_name}.`;
        }

        if (item.is_damaged === "") {
          return `Confirm whether garment ${index + 1} in ${serviceLine.service_name} is already damaged.`;
        }
      }
    }
  }

  return "";
}

// Explain the owner's recording choice inside each selected service.
function getRecordingModeLabel(mode) {
  if (mode === "tally") return "Quick clothing tally";
  if (mode === "detailed") return "Individual garment details";
  return "No clothing list required";
}

// Check payment choices before creating the order so an accidental entry is caught early.
function getPaymentError(paymentChoice, paymentAmountType, depositAmount, total) {
  if (paymentChoice === "unpaid") {
    return "";
  }

  if (paymentAmountType === "deposit") {
    const amount = Number(depositAmount);

    if (!Number.isFinite(amount) || amount <= 0) {
      return "Enter the deposit amount received.";
    }

    if (amount >= total) {
      return "Use Full payment when the customer has paid the whole amount.";
    }
  }

  return "";
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

// Open WhatsApp with a prepared receipt; staff still review it and press Send.
function shareReceipt(order) {
  const phone = getWhatsAppNumber(order.customerPhone);

  if (!phone) {
    return "The customer phone number is not in a valid Kenyan format.";
  }

  const serviceNames = order.service_lines
    .map((line) => line.service_name)
    .join(", ");
  const message = [
    "Qinetra Laundry receipt",
    `Customer: ${order.customerName}`,
    `Ticket: ${order.ticket_number}`,
    `Services: ${serviceNames}`,
    `Total: ${formatKes(order.total_price)}`,
    `Paid: ${formatKes(order.amount_paid)}`,
    `Balance: ${formatKes(order.balance_due)}`,
    "Status: Received",
    "",
    "Thank you for choosing Qinetra Laundry.",
  ].join("\n");

  window.open(
    `https://wa.me/${phone}?text=${encodeURIComponent(message)}`,
    "_blank",
    "noopener,noreferrer",
  );
  return "";
}

export default function OrderEntryPage() {
  const { authenticatedRequest } = useAuth();

  // Load the three lists needed to create a catalogue-based order.
  const [customers, setCustomers] = useState([]);
  const [catalogServices, setCatalogServices] = useState([]);
  const [itemTypes, setItemTypes] = useState([]);
  const [isLoadingSetup, setIsLoadingSetup] = useState(true);

  // Store the customer choice and the services added to this ticket.
  const [customerSearch, setCustomerSearch] = useState("");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [serviceCategoryToAdd, setServiceCategoryToAdd] = useState("general");
  const [serviceToAddId, setServiceToAddId] = useState("");
  const [selectedServices, setSelectedServices] = useState([]);
  const [serviceAddError, setServiceAddError] = useState("");

  // Payment can be left unpaid, recorded in full, or recorded as a deposit.
  const [paymentChoice, setPaymentChoice] = useState("unpaid");
  const [paymentAmountType, setPaymentAmountType] = useState("full");
  const [depositAmount, setDepositAmount] = useState("");
  const [paymentConfirmed, setPaymentConfirmed] = useState(false);

  // Track form feedback and the final backend-created ticket.
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [receiptShareError, setReceiptShareError] = useState("");
  const [createdOrder, setCreatedOrder] = useState(null);

  // Load customers and active catalogue choices together.
  useEffect(() => {
    async function loadOrderSetup() {
      try {
        const [customerResponse, serviceResponse, itemResponse] =
          await Promise.all([
            authenticatedRequest("/customers"),
            authenticatedRequest("/catalog/services"),
            authenticatedRequest("/catalog/item-types?include_inactive=true"),
          ]);

        const requestedCustomerId = new URLSearchParams(
          window.location.search,
        ).get("customerId");
        const customerExists = customerResponse.some(
          (customer) => String(customer.id) === requestedCustomerId,
        );

        setCustomers(customerResponse);
        setCatalogServices(serviceResponse);
        setItemTypes(itemResponse);

        if (customerExists) {
          setSelectedCustomerId(requestedCustomerId);
        }
      } catch (loadError) {
        setError(loadError.message || "Order setup could not be loaded.");
      } finally {
        setIsLoadingSetup(false);
      }
    }

    loadOrderSetup();
  }, [authenticatedRequest]);

  // Move the returned ticket into view after React adds it to the page.
  useEffect(() => {
    if (createdOrder) {
      document.getElementById("created-order-result")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [createdOrder]);

  // Filter customers already loaded from the backend by name or phone.
  const normalizedCustomerSearch = customerSearch.trim().toLowerCase();
  const visibleCustomers = customers.filter((customer) => {
    const matchesSearch =
      !normalizedCustomerSearch ||
      customer.name.toLowerCase().includes(normalizedCustomerSearch) ||
      customer.phone.includes(normalizedCustomerSearch);

    return matchesSearch || String(customer.id) === selectedCustomerId;
  });

  // Remove services already on the ticket from the add-service menu.
  const selectedServiceIds = new Set(
    selectedServices.map((service) => service.service_id),
  );
  const availableServices = catalogServices.filter(
    (service) => !selectedServiceIds.has(service.id),
  );
  const availableCategoryServices = availableServices.filter(
    (service) =>
      service.category === serviceCategoryToAdd &&
      service.code !== SUIT_BAG_CODE,
  );
  const suitBagService = catalogServices.find(
    (service) => service.code === SUIT_BAG_CODE,
  );
  const shouldOfferSuitBag =
    suitBagService &&
    !selectedServiceIds.has(suitBagService.id) &&
    selectedServices.some((service) =>
      SUIT_BAG_PROMPT_CODES.has(service.service_code),
    );
  const estimatedTotal = selectedServices.reduce(
    (total, serviceLine) => total + getServiceSubtotal(serviceLine),
    0,
  );

  // Add one active catalogue service to the current ticket.
  function addService() {
    const serviceId = Number(serviceToAddId);
    const service = catalogServices.find((item) => item.id === serviceId);

    if (!service) {
      setServiceAddError("Select a laundry service to add.");
      return;
    }

    setSelectedServices((currentServices) => [
      ...currentServices,
      createServiceLine(service),
    ]);
    setServiceToAddId("");
    setServiceAddError("");
  }

  // Add the optional suit bag from its prompt without making staff find it again.
  function addSuitBag() {
    if (!suitBagService) {
      return;
    }

    setSelectedServices((currentServices) => [
      ...currentServices,
      createServiceLine(suitBagService),
    ]);
    setServiceAddError("");
  }

  // Change one selected service while leaving the others untouched.
  function updateServiceLine(serviceId, changes) {
    setSelectedServices((currentServices) =>
      currentServices.map((serviceLine) =>
        serviceLine.service_id === serviceId
          ? { ...serviceLine, ...changes }
          : serviceLine,
      ),
    );
  }

  // Remove a service that was selected by mistake.
  function removeService(serviceId) {
    setSelectedServices((currentServices) =>
      currentServices.filter(
        (serviceLine) => serviceLine.service_id !== serviceId,
      ),
    );
    setError("");
  }

  // Let staff postpone a check while keeping the service quantity needed for pricing.
  function setItemRecordingChoice(serviceLine, shouldDefer) {
    if (shouldDefer) {
      updateServiceLine(serviceLine.service_id, {
        defer_items: true,
        quantity: String(Math.max(1, getServiceQuantity(serviceLine))),
        items: [],
      });
      return;
    }

    const detailedQuantity = Math.max(
      1,
      Math.floor(Number(serviceLine.quantity) || 1),
    );
    updateServiceLine(serviceLine.service_id, {
      defer_items: false,
      items:
        serviceLine.item_recording_mode === "detailed"
          ? Array.from({ length: detailedQuantity }, (_, index) =>
              createBlankGarment(
                index + 1,
                serviceLine.fixed_item_type_id || "",
              ),
            )
          : [],
    });
  }

  // Convert the visible service lines into the nested backend request.
  function buildOrderPayload(customerId) {
    return {
      customer_id: customerId,
      services: selectedServices.map((serviceLine) => ({
        service_id: serviceLine.service_id,
        quantity: getServiceQuantity(serviceLine),
        items:
          serviceLine.item_recording_mode === "detailed"
            ? serviceLine.items.map((item) => ({
                item_type_id: Number(item.item_type_id),
                quantity: 1,
                description: cleanOptionalText(item.description),
                is_damaged: item.is_damaged === "true",
                damage_note:
                  item.is_damaged === "true"
                    ? cleanOptionalText(item.damage_note)
                    : null,
                stain_note: cleanOptionalText(item.stain_note),
              }))
            : serviceLine.items.map((item) => ({
                item_type_id: item.item_type_id,
                quantity: item.quantity,
                description: null,
                is_damaged: null,
                damage_note: null,
                stain_note: null,
              })),
      })),
    };
  }

  // Validate and create one ticket containing all selected services.
  async function handleSubmit(event) {
    event.preventDefault();
    const customerId = Number(selectedCustomerId);
    const orderError = getOrderError(customerId, selectedServices);
    const paymentError = getPaymentError(
      paymentChoice,
      paymentAmountType,
      depositAmount,
      estimatedTotal,
    );
    const validationError =
      orderError ||
      paymentError ||
      (paymentChoice !== "unpaid" && !paymentConfirmed
        ? paymentChoice === "cash"
          ? "Confirm that the cash was received."
          : "Confirm the M-PESA message on the official business phone."
        : "");

    if (validationError) {
      setError(validationError);
      return;
    }

    const customer = customers.find((item) => item.id === customerId);
    setError("");
    setCreatedOrder(null);
    setIsSubmitting(true);

    try {
      const response = await authenticatedRequest("/orders/detailed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildOrderPayload(customerId)),
      });

      let finalOrder = response;
      let paymentWarning = "";

      // Record payment only after FastAPI has created and priced the ticket.
      if (paymentChoice !== "unpaid") {
        const paymentAmount =
          paymentAmountType === "full"
            ? response.balance_due
            : Number(depositAmount);

        try {
          finalOrder = await authenticatedRequest(
            `/orders/${response.id}/payments`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                payment_method: paymentChoice,
                amount: paymentAmount,
                confirmed: true,
              }),
            },
          );
        } catch (paymentRequestError) {
          paymentWarning =
            paymentRequestError.message ||
            "The order was created, but its payment was not recorded.";
        }
      }

      setCreatedOrder({
        ...finalOrder,
        customerName: customer?.name || `Customer ${customerId}`,
        customerPhone: customer?.phone || "",
        paymentWarning,
      });
      setCustomerSearch("");
      setSelectedCustomerId("");
      setServiceCategoryToAdd("general");
      setServiceToAddId("");
      setSelectedServices([]);
      setPaymentChoice("unpaid");
      setPaymentAmountType("full");
      setDepositAmount("");
      setPaymentConfirmed(false);
      setReceiptShareError("");
    } catch (orderError) {
      setError(orderError.message || "The order could not be created.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Order and pricing module
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Create a laundry order
        </h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">
          Select the customer, add their services and record the clothing
          received. FastAPI confirms the final price and ticket number.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
          <Link
            className="inline-flex items-center gap-2 font-bold text-[#005AAB] no-underline hover:underline"
            href="/customers"
          >
            <svg
              aria-hidden="true"
              className="h-5 w-5 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
            Register a customer first
          </Link>
          <Link
            className="inline-flex items-center gap-2 font-bold text-[#005AAB] no-underline hover:underline"
            href="/orders/status"
          >
            <svg
              aria-hidden="true"
              className="h-5 w-5 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M5 12h14m-5-5 5 5-5 5" />
            </svg>
            Track order status
          </Link>
        </div>
      </div>

      <form
        className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="space-y-6">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-xl font-bold text-slate-900">1. Customer</h2>

            <label
              className="mt-4 block font-semibold text-slate-800"
              htmlFor="customer_search"
            >
              Find customer
            </label>
            <input
              className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="customer_search"
              type="search"
              value={customerSearch}
              onChange={(event) => setCustomerSearch(event.target.value)}
              disabled={isLoadingSetup || isSubmitting}
              placeholder="Search by customer name or phone"
            />

            <label
              className="mt-4 block font-semibold text-slate-800"
              htmlFor="customer_id"
            >
              Customer
            </label>
            <select
              className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="customer_id"
              value={selectedCustomerId}
              onChange={(event) => setSelectedCustomerId(event.target.value)}
              disabled={isLoadingSetup || isSubmitting}
            >
              <option value="">
                {isLoadingSetup
                  ? "Loading customers…"
                  : visibleCustomers.length === 0
                    ? "No matching customers"
                    : "Select a customer"}
              </option>
              {visibleCustomers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} — {customer.phone}
                </option>
              ))}
            </select>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-xl font-bold text-slate-900">2. Services</h2>
            <p className="mt-2 text-slate-600">
              Add every service the customer is receiving on this ticket.
            </p>

            <div className="mt-4 grid gap-3 sm:grid-cols-[190px_minmax(0,1fr)_auto]">
              <select
                className="min-h-12 rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
                value={serviceCategoryToAdd}
                onChange={(event) => {
                  setServiceCategoryToAdd(event.target.value);
                  setServiceToAddId("");
                  setServiceAddError("");
                }}
                disabled={isLoadingSetup || isSubmitting}
                aria-label="Service category"
              >
                <option value="general">Laundry services</option>
                <option value="dry_cleaning">Dry Cleaning</option>
              </select>
              <select
                className="min-h-12 min-w-0 rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
                value={serviceToAddId}
                onChange={(event) => {
                  setServiceToAddId(event.target.value);
                  setServiceAddError("");
                }}
                disabled={
                  isLoadingSetup ||
                  isSubmitting ||
                  availableCategoryServices.length === 0
                }
                aria-label={
                  serviceCategoryToAdd === "dry_cleaning"
                    ? "Dry Cleaning garment to add"
                    : "Laundry service to add"
                }
              >
                <option value="">
                  {availableCategoryServices.length === 0
                    ? "No more choices in this category"
                    : serviceCategoryToAdd === "dry_cleaning"
                      ? "Select a garment"
                      : "Select a service"}
                </option>
                {availableCategoryServices.map((service) => (
                  <option key={service.id} value={service.id}>
                    {getServiceDisplayName(service)} —{" "}
                    {formatKes(service.unit_price)} per {service.unit}
                  </option>
                ))}
              </select>
              <button
                className="min-h-12 rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-50"
                type="button"
                disabled={
                  isLoadingSetup ||
                  isSubmitting ||
                  availableCategoryServices.length === 0
                }
                onClick={addService}
              >
                {serviceCategoryToAdd === "dry_cleaning"
                  ? "Add garment"
                  : "Add service"}
              </button>
            </div>
            {serviceAddError ? (
              <p
                className="mt-3 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
                role="alert"
              >
                {serviceAddError}
              </p>
            ) : null}

            {shouldOfferSuitBag ? (
              <div className="mt-5 flex flex-col gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-bold text-amber-950">
                    Would the customer like a suit bag?
                  </p>
                  <p className="mt-1 text-sm text-amber-900">
                    Optional add-on: {formatKes(suitBagService.unit_price)}
                  </p>
                </div>
                <button
                  className="min-h-10 rounded-lg bg-amber-900 px-4 text-sm font-bold text-white hover:bg-amber-950"
                  type="button"
                  disabled={isSubmitting}
                  onClick={addSuitBag}
                >
                  Add suit bag
                </button>
              </div>
            ) : null}

            {selectedServices.length === 0 ? (
              <p className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center text-sm text-slate-600">
                No service added yet.
              </p>
            ) : (
              <div className="mt-5 space-y-5">
                {selectedServices.map((serviceLine, index) => {
                  const quantity = getServiceQuantity(serviceLine);
                  const subtotal = getServiceSubtotal(serviceLine);

                  return (
                    <article
                      className="rounded-2xl border border-slate-200 p-4 sm:p-5"
                      key={serviceLine.service_id}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-bold text-[#005AAB]">
                            Service {index + 1}
                          </p>
                          <h3 className="mt-1 text-xl font-bold text-slate-900">
                            {serviceLine.category === "dry_cleaning"
                              ? `Dry Cleaning · ${getServiceDisplayName(serviceLine)}`
                              : serviceLine.service_name}
                          </h3>
                          <p className="mt-1 text-sm text-slate-600">
                            {formatKes(serviceLine.unit_price)} per{" "}
                            {serviceLine.service_unit} ·{" "}
                            {getRecordingModeLabel(
                              serviceLine.item_recording_mode,
                            )}
                          </p>
                        </div>
                        <button
                          className="text-sm font-bold text-red-700 hover:underline disabled:opacity-50"
                          type="button"
                          disabled={isSubmitting}
                          onClick={() =>
                            removeService(serviceLine.service_id)
                          }
                        >
                          Remove service
                        </button>
                      </div>

                      {serviceLine.item_recording_mode !== "none" ? (
                        <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-4">
                          <p className="font-semibold text-slate-800">
                            When should clothing be recorded?
                          </p>
                          <div className="mt-3 flex flex-wrap gap-3">
                            <button
                              className={`min-h-10 rounded-lg border px-4 text-sm font-bold ${
                                !serviceLine.defer_items
                                  ? "border-[#005AAB] bg-[#005AAB] text-white"
                                  : "border-[#005AAB] bg-white text-[#005AAB]"
                              }`}
                              type="button"
                              disabled={isSubmitting}
                              onClick={() =>
                                setItemRecordingChoice(serviceLine, false)
                              }
                            >
                              Record items now
                            </button>
                            <button
                              className={`min-h-10 rounded-lg border px-4 text-sm font-bold ${
                                serviceLine.defer_items
                                  ? "border-amber-500 bg-amber-100 text-amber-950"
                                  : "border-slate-300 bg-white text-slate-700"
                              }`}
                              type="button"
                              disabled={isSubmitting}
                              onClick={() =>
                                setItemRecordingChoice(serviceLine, true)
                              }
                            >
                              Do this later
                            </button>
                          </div>
                          {serviceLine.defer_items ? (
                            <p className="mt-3 text-sm font-semibold text-amber-900">
                              The receipt will show Item check pending until
                              staff complete it from status tracking.
                            </p>
                          ) : null}
                        </div>
                      ) : null}

                      {serviceLine.item_recording_mode === "detailed" &&
                      !serviceLine.defer_items ? (
                        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 px-4 py-3">
                          <span className="font-semibold text-slate-700">
                            Charged quantity
                          </span>
                          <span className="font-bold text-slate-900">
                            {quantity}{" "}
                            {quantity === 1
                              ? serviceLine.service_unit
                              : `${serviceLine.service_unit}s`}
                          </span>
                        </div>
                      ) : (
                        <>
                          <label
                            className="mt-4 block font-semibold text-slate-800"
                            htmlFor={`service-quantity-${serviceLine.service_id}`}
                          >
                            Quantity ({serviceLine.service_unit})
                          </label>
                          <input
                            className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
                            id={`service-quantity-${serviceLine.service_id}`}
                            type="number"
                            min={
                              serviceLine.service_unit === "kg" ? "0.1" : "1"
                            }
                            step={
                              serviceLine.service_unit === "kg" ? "0.1" : "1"
                            }
                            value={serviceLine.quantity}
                            disabled={isSubmitting}
                            onChange={(event) =>
                              updateServiceLine(serviceLine.service_id, {
                                quantity: event.target.value,
                              })
                            }
                          />
                        </>
                      )}

                      <ServiceItemEntry
                        recordingMode={
                          serviceLine.defer_items
                            ? "none"
                            : serviceLine.item_recording_mode
                        }
                        itemTypes={itemTypes}
                        items={serviceLine.items}
                        disabled={isSubmitting}
                        fieldPrefix={`service-${serviceLine.service_id}`}
                        fixedItemType={
                          serviceLine.fixed_item_type_id
                            ? itemTypes.find(
                                (itemType) =>
                                  itemType.id ===
                                  serviceLine.fixed_item_type_id,
                              ) || null
                            : null
                        }
                        onItemsChange={(items) =>
                          updateServiceLine(serviceLine.service_id, { items })
                        }
                      />

                      <div className="mt-4 flex items-center justify-between border-t border-slate-200 pt-4">
                        <span className="font-semibold text-slate-600">
                          Service estimate
                        </span>
                        <span className="text-lg font-bold text-slate-900">
                          {formatKes(subtotal)}
                        </span>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-xl font-bold text-slate-900">3. Payment</h2>
            <p className="mt-2 text-slate-600">
              Record what the customer has paid now, or leave the balance for
              collection.
            </p>

            <fieldset className="mt-4">
              <legend className="font-semibold text-slate-800">
                Payment received
              </legend>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {[
                  { value: "unpaid", label: "Not paid yet" },
                  { value: "cash", label: "Cash" },
                  { value: "mpesa", label: "M-PESA Paybill" },
                ].map((option) => (
                  <label
                    className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border px-4 font-semibold ${
                      paymentChoice === option.value
                        ? "border-[#005AAB] bg-blue-50 text-[#005AAB]"
                        : "border-slate-300 text-slate-700"
                    }`}
                    key={option.value}
                  >
                    <input
                      type="radio"
                      name="payment_choice"
                      value={option.value}
                      checked={paymentChoice === option.value}
                      disabled={isSubmitting}
                      onChange={(event) => {
                        setPaymentChoice(event.target.value);
                        setPaymentConfirmed(false);
                        setError("");
                      }}
                    />
                    {option.label}
                  </label>
                ))}
              </div>
            </fieldset>

            {paymentChoice !== "unpaid" ? (
              <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <fieldset>
                  <legend className="font-semibold text-slate-800">
                    Amount received
                  </legend>
                  <div className="mt-3 flex flex-wrap gap-4">
                    <label className="flex items-center gap-2 font-semibold text-slate-700">
                      <input
                        type="radio"
                        name="payment_amount_type"
                        value="full"
                        checked={paymentAmountType === "full"}
                        disabled={isSubmitting}
                        onChange={() => {
                          setPaymentAmountType("full");
                          setDepositAmount("");
                          setError("");
                        }}
                      />
                      Full payment
                    </label>
                    <label className="flex items-center gap-2 font-semibold text-slate-700">
                      <input
                        type="radio"
                        name="payment_amount_type"
                        value="deposit"
                        checked={paymentAmountType === "deposit"}
                        disabled={isSubmitting}
                        onChange={() => {
                          setPaymentAmountType("deposit");
                          setError("");
                        }}
                      />
                      Deposit
                    </label>
                  </div>
                </fieldset>

                {paymentAmountType === "deposit" ? (
                  <div className="mt-4">
                    <label
                      className="block font-semibold text-slate-800"
                      htmlFor="deposit_amount"
                    >
                      Deposit amount (KES)
                    </label>
                    <input
                      className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 sm:max-w-xs"
                      id="deposit_amount"
                      type="number"
                      min="1"
                      step="1"
                      value={depositAmount}
                      disabled={isSubmitting}
                      onChange={(event) => {
                        setDepositAmount(event.target.value);
                        setError("");
                      }}
                      placeholder="Example: 500"
                    />
                  </div>
                ) : (
                  <p className="mt-4 text-sm font-semibold text-slate-700">
                    Full amount: {formatKes(estimatedTotal)}
                  </p>
                )}

                <label className="mt-5 flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm font-semibold text-amber-950">
                  <input
                    className="mt-1"
                    type="checkbox"
                    checked={paymentConfirmed}
                    disabled={isSubmitting}
                    onChange={(event) => {
                      setPaymentConfirmed(event.target.checked);
                      setError("");
                    }}
                  />
                  {paymentChoice === "cash"
                    ? "I have received this cash from the customer."
                    : "I have seen the confirmed payment message on Qinetra Laundry’s official business phone."}
                </label>
              </div>
            ) : (
              <p className="mt-4 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
                This order will show an outstanding balance and cannot be
                collected until it is fully paid.
              </p>
            )}
          </section>

          {error ? (
            <p
              className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              {error}
            </p>
          ) : null}

          <button
            className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
            type="submit"
            disabled={isSubmitting || isLoadingSetup}
          >
            {isSubmitting ? "Creating order…" : "Create order"}
          </button>
        </div>

        <aside className="h-fit rounded-2xl border border-blue-200 bg-blue-50 p-5 lg:sticky lg:top-6">
          <p className="text-sm font-bold uppercase tracking-wide text-[#005AAB]">
            Order estimate
          </p>
          <p className="mt-3 text-3xl font-bold text-slate-900">
            {formatKes(estimatedTotal)}
          </p>

          {selectedServices.length > 0 ? (
            <div className="mt-5 space-y-3 border-t border-blue-200 pt-4">
              {selectedServices.map((serviceLine) => (
                <div
                  className="flex items-start justify-between gap-3 text-sm"
                  key={serviceLine.service_id}
                >
                  <span className="text-slate-700">
                    {serviceLine.service_name}
                  </span>
                  <span className="font-bold text-slate-900">
                    {formatKes(getServiceSubtotal(serviceLine))}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Add services to see the estimated total.
            </p>
          )}

          <p className="mt-5 text-sm leading-6 text-slate-600">
            This is a preview only. The backend uses the saved catalogue prices
            to confirm the final amount.
          </p>

          <div className="mt-5 border-t border-blue-200 pt-4 text-sm">
            <p className="font-semibold text-slate-700">Payment choice</p>
            <p className="mt-1 font-bold text-slate-900">
              {paymentChoice === "unpaid"
                ? "Not paid yet"
                : paymentChoice === "cash"
                  ? "Cash"
                  : "M-PESA Paybill"}
            </p>
          </div>
        </aside>
      </form>

      {createdOrder ? (
        <section
          className="mt-8 scroll-mt-6 rounded-2xl border border-green-300 bg-green-50 p-6 sm:p-8"
          id="created-order-result"
          role="status"
          aria-live="polite"
        >
          <p className="text-sm font-bold uppercase tracking-wide text-green-800">
            Order created
          </p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Ticket {createdOrder.ticket_number}
          </h2>
          {createdOrder.paymentWarning ? (
            <p className="mt-5 rounded-xl border border-amber-400 bg-amber-100 px-4 py-3 font-semibold text-amber-950">
              The order was created, but its payment was not recorded.{" "}
              {createdOrder.paymentWarning} Open the receipt to record it
              without creating another order.
            </p>
          ) : null}
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-sm text-slate-600">Customer</p>
              <p className="mt-1 font-bold text-slate-900">
                {createdOrder.customerName}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Final total</p>
              <p className="mt-1 font-bold text-slate-900">
                {formatKes(createdOrder.total_price)}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Amount paid</p>
              <p className="mt-1 font-bold text-slate-900">
                {formatKes(createdOrder.amount_paid)}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Balance</p>
              <p
                className={`mt-1 font-bold ${
                  Number(createdOrder.balance_due) > 0
                    ? "text-red-700"
                    : "text-green-700"
                }`}
              >
                {formatKes(createdOrder.balance_due)}
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {createdOrder.service_lines.map((serviceLine) => (
              <article
                className="rounded-xl border border-green-200 bg-white p-4"
                key={serviceLine.id}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-slate-900">
                      {serviceLine.service_name}
                    </h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {serviceLine.quantity} {serviceLine.service_unit} at{" "}
                      {formatKes(serviceLine.unit_price)}
                    </p>
                  </div>
                  <p className="font-bold text-slate-900">
                    {formatKes(serviceLine.subtotal)}
                  </p>
                </div>

                {serviceLine.item_check_status === "pending" ? (
                  <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-bold text-amber-900">
                    Item check pending
                  </p>
                ) : null}

                {serviceLine.items.length > 0 ? (
                  <ul className="mt-4 space-y-2 border-t border-slate-200 pt-4">
                    {serviceLine.items.map((item) => (
                      <li className="text-sm text-slate-700" key={item.id}>
                        <span className="font-bold text-slate-900">
                          {item.quantity} × {item.item_name}
                        </span>
                        {item.description ? ` · ${item.description}` : ""}
                        {item.is_damaged === true
                          ? ` · Existing damage${item.damage_note ? `: ${item.damage_note}` : ""}`
                          : ""}
                        {item.stain_note
                          ? ` · Note: ${item.stain_note}`
                          : ""}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))}
          </div>

          {createdOrder.payments.length > 0 ? (
            <div className="mt-6 rounded-xl border border-green-200 bg-white p-4">
              <h3 className="font-bold text-slate-900">Payment recorded</h3>
              {createdOrder.payments.map((payment) => (
                <p className="mt-2 text-sm text-slate-700" key={payment.id}>
                  {payment.payment_method === "mpesa" ? "M-PESA" : "Cash"} ·{" "}
                  {formatKes(payment.amount)}
                </p>
              ))}
            </div>
          ) : null}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button
              className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782]"
              type="button"
              onClick={() => setReceiptShareError(shareReceipt(createdOrder))}
            >
              Share receipt on WhatsApp
            </button>
            <Link
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
              href={`/orders/${createdOrder.id}`}
            >
              Open full receipt
            </Link>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            WhatsApp opens a prepared message. Check it, then press Send.
          </p>
          {receiptShareError ? (
            <p
              className="mt-4 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              {receiptShareError}
            </p>
          ) : null}
        </section>
      ) : null}
    </section>
  );
}
