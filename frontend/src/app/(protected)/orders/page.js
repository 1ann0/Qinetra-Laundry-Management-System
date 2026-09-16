"use client";

import { getUserMessage } from "@/lib/user-messages";

import Link from "next/link";
import { useEffect, useState } from "react";
import CustomerForm from "@/components/customers/customer-form";
import ServiceItemEntry, {
  createBlankGarment,
} from "@/components/orders/service-item-entry";
import { useAuth } from "@/context/auth-context";
import usePendingSave from "@/components/orders/use-pending-save";
import PendingSaveNotice from "@/components/orders/pending-save-notice";
import { buildOrderReceiptMessage } from "@/lib/order-receipt";
import { getServiceQuantity } from "@/lib/order-service";
import { formatNairobiDateTime } from "@/lib/format-nairobi";
import {
  clearOrderDraft,
  hasMeaningfulOrderDraft,
  orderDraftScope,
  readOrderDraft,
  saveOrderDraft,
} from "@/lib/order-draft";

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

// Business dates follow the shop's Nairobi calendar, not the device timezone.
function getNairobiToday() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function formatDate(value) {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeZone: "Africa/Nairobi",
  }).format(new Date(`${value}T12:00:00+03:00`));
}

// Keep completion times readable on the form, receipt and WhatsApp message.
// Convert a Date into the local format required by a datetime-local input.
function formatDateTimeInput(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return [
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    `${pad(date.getHours())}:${pad(date.getMinutes())}`,
  ].join("T");
}

// Suggest a completion time from the slowest service on the ticket.
function getSuggestedReadyInput(serviceLines, isPeakTime) {
  if (serviceLines.length === 0) return "";

  const turnaroundMinutes = serviceLines.reduce(
    (longestTime, serviceLine) =>
      Math.max(longestTime, serviceLine.turnaround_minutes),
    0,
  );
  const peakDelayMinutes = isPeakTime ? 60 : 0;
  return formatDateTimeInput(
    new Date(Date.now() + (turnaroundMinutes + peakDelayMinutes) * 60 * 1000),
  );
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
    turnaround_minutes: Number(service.turnaround_minutes) || 180,
    quantity: "1",
    discount_enabled: false,
    discount_amount: "",
    defer_items: false,
    items:
      service.item_recording_mode === "detailed"
        ? [createBlankGarment(1, service.default_item_type_id || "")]
        : [],
  };
}

// Refresh catalogue-controlled values while keeping valid unfinished work.
function restoreDraftServices(savedServices, catalogServices) {
  return savedServices.flatMap((savedService) => {
    const currentService = catalogServices.find(
      (service) => service.id === savedService.service_id,
    );
    if (
      !currentService ||
      currentService.item_recording_mode !== savedService.item_recording_mode
    ) {
      return [];
    }
    return [{
      ...savedService,
      service_code: currentService.code,
      service_name: currentService.name,
      service_unit: currentService.unit,
      unit_price: Number(currentService.unit_price),
      category: currentService.category,
      fixed_item_type_id: currentService.default_item_type_id,
      item_recording_mode: currentService.item_recording_mode,
      turnaround_minutes: Number(currentService.turnaround_minutes) || 180,
      items: Array.isArray(savedService.items) ? savedService.items : [],
    }];
  });
}

// Dry Cleaning is the category, so employees only need the garment wording.
function getServiceDisplayName(service) {
  const serviceName = service.name || service.service_name || "Unnamed service";

  if (service.category === "dry_cleaning") {
    return serviceName.replace(/^Dry Cleaning\s*-\s*/i, "");
  }
  return serviceName;
}

// Calculate only the employee's preview; FastAPI still confirms the final price.
function getServiceSubtotal(serviceLine) {
  const quantity = getServiceQuantity(serviceLine);
  return Number.isFinite(quantity) && quantity > 0
    ? serviceLine.unit_price * quantity
    : 0;
}

function getServiceDiscount(serviceLine) {
  if (!serviceLine.discount_enabled) return 0;
  const discount = Number(serviceLine.discount_amount);
  return Number.isFinite(discount) && discount > 0 ? discount : 0;
}

function getServiceTotal(serviceLine) {
  return Math.max(
    getServiceSubtotal(serviceLine) - getServiceDiscount(serviceLine),
    0,
  );
}

// Check all visible order values before sending them to FastAPI.
function getOrderError(
  customerId,
  serviceLines,
  discountReason,
  orderDate,
  today,
) {
  if (!customerId) {
    return "Select the customer for this order.";
  }

  if (serviceLines.length === 0) {
    return "Add at least one laundry service.";
  }

  if (!orderDate) {
    return "Select the order date.";
  }

  if (orderDate > today) {
    return "The order date cannot be in the future.";
  }

  let hasDiscount = false;

  for (const serviceLine of serviceLines) {
    const quantity = getServiceQuantity(serviceLine);
    const subtotal = getServiceSubtotal(serviceLine);

    if (!Number.isFinite(quantity) || quantity <= 0) {
      return `Enter a quantity greater than zero for ${serviceLine.service_name}.`;
    }

    if (serviceLine.discount_enabled) {
      const discount = Number(serviceLine.discount_amount);
      hasDiscount = true;

      if (!Number.isFinite(discount) || discount <= 0) {
        return `Enter a discount greater than zero for ${serviceLine.service_name}.`;
      }

      if (discount >= subtotal) {
        return `The discount for ${serviceLine.service_name} must be less than its ${formatKes(subtotal)} subtotal.`;
      }
    }

    if (
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

    if (!serviceLine.defer_items && serviceLine.item_recording_mode === "tally") {
      for (const item of serviceLine.items) {
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

    if (
      !serviceLine.defer_items &&
      serviceLine.item_recording_mode === "detailed"
    ) {
      if (serviceLine.items.length < quantity) {
        return `Record at least ${quantity} physical ${quantity === 1 ? "piece" : "pieces"} for ${serviceLine.service_name}.`;
      }

      for (const [index, item] of serviceLine.items.entries()) {
        if (!item.item_type_id) {
          return `Select the clothing type for garment ${index + 1} in ${serviceLine.service_name}.`;
        }

        if (item.is_damaged === "") {
          return `Confirm whether garment ${index + 1} in ${serviceLine.service_name} is already damaged.`;
        }

        if (!item.description.trim()) {
          return `Describe garment ${index + 1} in ${serviceLine.service_name} so it can be identified.`;
        }
      }
    }
  }

  if (hasDiscount && !discountReason.trim()) {
    return "Explain why this order was discounted.";
  }

  return "";
}

// A promised time is required and must still be in the future when submitted.
function getPromisedTimeError(promisedReadyAt) {
  if (!promisedReadyAt) {
    return "Confirm when the order will be ready.";
  }

  const promisedTime = new Date(promisedReadyAt);
  if (Number.isNaN(promisedTime.getTime())) {
    return "Enter a valid promised completion time.";
  }

  if (promisedTime.getTime() <= Date.now()) {
    return "The promised completion time must be in the future.";
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
function getPaymentError(
  paymentChoice,
  paymentAmountType,
  depositAmount,
  total,
  receivedDate,
  orderDate,
  today,
) {
  if (paymentChoice === "unpaid") {
    return "";
  }

  if (!receivedDate) {
    return "Select the date the payment was received.";
  }

  if (receivedDate < orderDate) {
    return "The payment date cannot be before the order date.";
  }

  if (receivedDate > today) {
    return "The payment date cannot be in the future.";
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

  const message = buildOrderReceiptMessage(order, order.customerName);

  window.open(
    `https://wa.me/${phone}?text=${encodeURIComponent(message)}`,
    "_blank",
    "noopener,noreferrer",
  );
  return "";
}

export default function OrderEntryPage() {
  const { authenticatedRequest, userId } = useAuth();
  const today = getNairobiToday();
  const draftScope = orderDraftScope(userId);

  // Load the three lists needed to create a catalogue-based order.
  const [customers, setCustomers] = useState([]);
  const [catalogServices, setCatalogServices] = useState([]);
  const [itemTypes, setItemTypes] = useState([]);
  const [isLoadingSetup, setIsLoadingSetup] = useState(true);

  // Store the customer choice and the services added to this ticket.
  const [customerSearch, setCustomerSearch] = useState("");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [showAddCustomer, setShowAddCustomer] = useState(false);
  const [customerFeedback, setCustomerFeedback] = useState("");
  const [serviceCategoryToAdd, setServiceCategoryToAdd] = useState("general");
  const [serviceSearch, setServiceSearch] = useState("");
  const [selectedServices, setSelectedServices] = useState([]);
  const [isEarlierOrder, setIsEarlierOrder] = useState(false);
  const [orderDate, setOrderDate] = useState(getNairobiToday);
  const [discountReason, setDiscountReason] = useState("");

  // Start from the slowest selected service, with an optional busy-period hour.
  const [promisedReadyAt, setPromisedReadyAt] = useState("");
  const [isPeakTime, setIsPeakTime] = useState(false);

  // Payment can be left unpaid, recorded in full, or recorded as a deposit.
  const [paymentChoice, setPaymentChoice] = useState("unpaid");
  const [paymentAmountType, setPaymentAmountType] = useState("full");
  const [depositAmount, setDepositAmount] = useState("");
  const [paymentReceivedDate, setPaymentReceivedDate] =
    useState(getNairobiToday);
  const [paymentConfirmed, setPaymentConfirmed] = useState(false);

  // Track form feedback and the final backend-created ticket.
  const orderSave = usePendingSave("/orders/detailed");
  const isSubmitting = orderSave.isSaving;
  const [error, setError] = useState("");
  const [receiptShareError, setReceiptShareError] = useState("");
  const [createdOrder, setCreatedOrder] = useState(null);
  const [draftReady, setDraftReady] = useState(false);
  const [draftFeedback, setDraftFeedback] = useState("");

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

        let restoredDraft = null;
        if (userId) {
          try {
            restoredDraft = readOrderDraft(window.sessionStorage, draftScope);
          } catch (draftError) {
            setDraftFeedback(draftError.message);
          }
        }

        if (restoredDraft) {
          const restoredCustomerExists = customerResponse.some(
            (customer) => String(customer.id) === restoredDraft.selectedCustomerId,
          );
          const restoredServices = restoreDraftServices(
            restoredDraft.selectedServices,
            serviceResponse,
          );
          setSelectedCustomerId(
            restoredCustomerExists ? restoredDraft.selectedCustomerId : "",
          );
          setSelectedServices(restoredServices);
          setIsEarlierOrder(Boolean(restoredDraft.isEarlierOrder));
          setOrderDate(restoredDraft.orderDate || today);
          setDiscountReason(restoredDraft.discountReason || "");
          setPromisedReadyAt(restoredDraft.promisedReadyAt || "");
          setIsPeakTime(Boolean(restoredDraft.isPeakTime));
          setPaymentChoice(restoredDraft.paymentChoice || "unpaid");
          setPaymentAmountType(restoredDraft.paymentAmountType || "full");
          setDepositAmount(restoredDraft.depositAmount || "");
          setPaymentReceivedDate(restoredDraft.paymentReceivedDate || today);
          setPaymentConfirmed(Boolean(restoredDraft.paymentConfirmed));
          setDraftFeedback("Your unfinished order was restored.");
          if (restoredServices.length !== restoredDraft.selectedServices.length) {
            setDraftFeedback("Your unfinished order was restored. A service changed in Shop setup, so add that service again.");
          }
        }

        if (customerExists) {
          setSelectedCustomerId(requestedCustomerId);
        }
        setDraftReady(true);
      } catch (loadError) {
        setError(getUserMessage(loadError, "Order setup could not be loaded."));
      } finally {
        setIsLoadingSetup(false);
      }
    }

    loadOrderSetup();
  }, [authenticatedRequest, draftScope, today, userId]);

  const hasUnfinishedOrder = hasMeaningfulOrderDraft({
    selectedCustomerId,
    selectedServices,
    isEarlierOrder,
    orderDate,
    discountReason,
    promisedReadyAt,
    isPeakTime,
    paymentChoice,
    paymentAmountType,
    depositAmount,
    paymentReceivedDate,
    paymentConfirmed,
  });

  // Keep unfinished counter work through refresh or password re-entry.
  useEffect(() => {
    if (!draftReady || createdOrder || !userId) return undefined;
    const timer = window.setTimeout(() => {
      try {
        saveOrderDraft(window.sessionStorage, draftScope, {
          selectedCustomerId,
          selectedServices,
          isEarlierOrder,
          orderDate,
          discountReason,
          promisedReadyAt,
          isPeakTime,
          paymentChoice,
          paymentAmountType,
          depositAmount,
          paymentReceivedDate,
          paymentConfirmed,
        });
      } catch (draftError) {
        setDraftFeedback(draftError.message);
      }
    }, 150);
    return () => window.clearTimeout(timer);
  }, [
    createdOrder,
    depositAmount,
    discountReason,
    draftReady,
    draftScope,
    isEarlierOrder,
    isPeakTime,
    orderDate,
    paymentAmountType,
    paymentChoice,
    paymentConfirmed,
    paymentReceivedDate,
    promisedReadyAt,
    selectedCustomerId,
    selectedServices,
    userId,
  ]);

  useEffect(() => {
    if (!hasUnfinishedOrder || createdOrder) return undefined;
    const warnBeforeLeaving = (event) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeLeaving);
    return () => window.removeEventListener("beforeunload", warnBeforeLeaving);
  }, [createdOrder, hasUnfinishedOrder]);

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
  const normalizedServiceSearch = serviceSearch.trim().toLowerCase();
  const availableCategoryServices = availableServices.filter((service) => {
    const matchesCategory =
      service.category === serviceCategoryToAdd &&
      service.code !== SUIT_BAG_CODE;
    const matchesSearch =
      !normalizedServiceSearch ||
      getServiceDisplayName(service)
        .toLowerCase()
        .includes(normalizedServiceSearch);

    return matchesCategory && matchesSearch;
  });
  const suitBagService = catalogServices.find(
    (service) => service.code === SUIT_BAG_CODE,
  );
  const shouldOfferSuitBag =
    suitBagService &&
    !selectedServiceIds.has(suitBagService.id) &&
    selectedServices.some((service) =>
      SUIT_BAG_PROMPT_CODES.has(service.service_code),
    );
  const estimatedSubtotal = selectedServices.reduce(
    (total, serviceLine) => total + getServiceSubtotal(serviceLine),
    0,
  );
  const estimatedDiscount = selectedServices.reduce(
    (total, serviceLine) => total + getServiceDiscount(serviceLine),
    0,
  );
  const estimatedTotal = selectedServices.reduce(
    (total, serviceLine) => total + getServiceTotal(serviceLine),
    0,
  );

  // Add one active catalogue service to the current ticket.
  function addService(serviceId) {
    const service = catalogServices.find((item) => item.id === serviceId);

    if (!service) {
      return;
    }

    const nextServices = [...selectedServices, createServiceLine(service)];
    setSelectedServices(nextServices);
    setPromisedReadyAt(getSuggestedReadyInput(nextServices, isPeakTime));
  }

  // Add the optional suit bag from its prompt without making staff find it again.
  function addSuitBag() {
    if (!suitBagService) {
      return;
    }

    const nextServices = [
      ...selectedServices,
      createServiceLine(suitBagService),
    ];
    setSelectedServices(nextServices);
    setPromisedReadyAt(getSuggestedReadyInput(nextServices, isPeakTime));
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

  // Let staff add a missing Laundry choice without leaving the current order.
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

  // Remove a service that was selected by mistake.
  function removeService(serviceId) {
    const nextServices = selectedServices.filter(
      (serviceLine) => serviceLine.service_id !== serviceId,
    );
    setSelectedServices(nextServices);
    setPromisedReadyAt(getSuggestedReadyInput(nextServices, isPeakTime));
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
      initial_payment: paymentChoice === "unpaid" ? null : {
        payment_method: paymentChoice,
        amount: paymentAmountType === "full" ? null : Number(depositAmount),
        confirmed: paymentConfirmed,
        received_date: paymentReceivedDate,
      },
      order_date: orderDate,
      discount_reason:
        estimatedDiscount > 0 ? cleanOptionalText(discountReason) : null,
      promised_ready_at: new Date(promisedReadyAt).toISOString(),
      peak_delay_minutes: isPeakTime ? 60 : 0,
      services: selectedServices.map((serviceLine) => ({
        service_id: serviceLine.service_id,
        quantity: getServiceQuantity(serviceLine),
        discount_amount: getServiceDiscount(serviceLine),
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
                exceptions: (item.exceptions || []).map((exception) => ({
                  description: cleanOptionalText(exception.description),
                  is_damaged: exception.is_damaged,
                  damage_note: exception.is_damaged
                    ? cleanOptionalText(exception.damage_note)
                    : null,
                  stain_note: cleanOptionalText(exception.stain_note),
                })),
              })),
      })),
    };
  }

  // Validate and create one ticket containing all selected services.
  async function handleSubmit(event) {
    event.preventDefault();
    const customerId = Number(selectedCustomerId);
    const orderError = getOrderError(
      customerId,
      selectedServices,
      discountReason,
      orderDate,
      today,
    );
    const promisedTimeError = getPromisedTimeError(promisedReadyAt);
    const paymentError = getPaymentError(
      paymentChoice,
      paymentAmountType,
      depositAmount,
      estimatedTotal,
      paymentReceivedDate,
      orderDate,
      today,
    );
    const validationError =
      orderError ||
      promisedTimeError ||
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

    setError("");
    setCreatedOrder(null);

    try {
      finishCreatedOrder(await orderSave.save(buildOrderPayload(customerId)));
    } catch (orderError) {
      setError(getUserMessage(orderError, "QLMS could not confirm the save. Use Retry previous save."));
    }
  }

  async function retryOrder() {
    setError("");
    try {
      finishCreatedOrder(await orderSave.retry());
    } catch (orderError) {
      setError(getUserMessage(orderError));
    }
  }

  function selectNewCustomer(customer, message) {
    setCustomers((currentCustomers) => [
      customer,
      ...currentCustomers.filter((item) => item.id !== customer.id),
    ]);
    setSelectedCustomerId(String(customer.id));
    setCustomerSearch("");
    setShowAddCustomer(false);
    setCustomerFeedback(message);
    setError("");
  }

  function startNextOrder() {
    setCreatedOrder(null);
    setReceiptShareError("");
    setDraftFeedback("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // The order and any initial payment are now saved together.
  function finishCreatedOrder(finalOrder) {
      const customer = customers.find((item) => item.id === finalOrder.customer_id);
      setCreatedOrder({
        ...finalOrder,
        customerName: customer?.name || `Customer ${finalOrder.customer_id}`,
        customerPhone: customer?.phone || "",
      });
      setCustomerSearch("");
      setSelectedCustomerId("");
      setServiceCategoryToAdd("general");
      setServiceSearch("");
      setSelectedServices([]);
      setIsEarlierOrder(false);
      setOrderDate(today);
      setDiscountReason("");
      setPromisedReadyAt("");
      setIsPeakTime(false);
      setPaymentChoice("unpaid");
      setPaymentAmountType("full");
      setDepositAmount("");
      setPaymentReceivedDate(today);
      setPaymentConfirmed(false);
      setReceiptShareError("");
      setShowAddCustomer(false);
      setCustomerFeedback("");
      try {
        clearOrderDraft(window.sessionStorage, draftScope);
        setDraftFeedback("");
      } catch (draftError) {
        setDraftFeedback(draftError.message);
      }
  }

  return (
    <section className="mx-auto max-w-6xl pb-20 lg:pb-0">
      <div className="mb-7">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Orders / New order
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          New order
        </h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">
          Select the customer, add their services and record the clothing
          received. QLMS calculates the final price when you save the order.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
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

      {draftFeedback ? (
        <p
          className={`mb-5 rounded-xl border px-4 py-3 text-sm ${
            /could not|contact support/i.test(draftFeedback)
              ? "border-red-300 bg-red-50 text-red-800"
              : "border-blue-200 bg-blue-50 text-blue-900"
          }`}
          role={/could not|contact support/i.test(draftFeedback) ? "alert" : "status"}
        >
          {draftFeedback}
        </p>
      ) : null}

      {!createdOrder ? (
        <>
      <PendingSaveNotice {...orderSave} onRetry={retryOrder} />
      {showAddCustomer ? (
        <div className="mb-6">
          <CustomerForm
            compact
            onCancel={() => setShowAddCustomer(false)}
            onSaved={(customer, warning) =>
              selectNewCustomer(
                customer,
                warning
                  ? "Separate customer saved and selected."
                  : `${customer.name} was saved and selected.`,
              )
            }
            onUseExisting={(customer) =>
              selectNewCustomer(
                customer,
                `${customer.name} was selected. No duplicate was created.`,
              )
            }
          />
        </div>
      ) : null}
      <form
        id="order-entry-form"
        className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]"
        onSubmit={handleSubmit}
        noValidate
      >
        <fieldset className="contents" disabled={isSubmitting || Boolean(orderSave.pending) || !orderSave.ready}>
        <div className="space-y-6">
          <section
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
            id="order-customer-step"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold text-slate-900">1. Customer</h2>
              <button
                className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[#005AAB] px-4 text-sm font-bold text-[#005AAB] no-underline hover:bg-blue-50"
                type="button"
                onClick={() => {
                  setShowAddCustomer((isOpen) => !isOpen);
                  setCustomerFeedback("");
                }}
              >
                <span aria-hidden="true">+</span>
                {showAddCustomer ? "Close customer form" : "Add customer"}
              </button>
            </div>

            {customerFeedback ? (
              <p
                className="mt-4 rounded-xl border border-green-300 bg-green-50 px-4 py-3 text-sm font-semibold text-green-900"
                role="status"
              >
                {customerFeedback}
              </p>
            ) : null}

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

            <label className="mt-5 flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 font-semibold text-slate-800">
              <input
                className="mt-1"
                type="checkbox"
                checked={isEarlierOrder}
                disabled={isSubmitting}
                onChange={(event) => {
                  const shouldUseEarlierDate = event.target.checked;
                  setIsEarlierOrder(shouldUseEarlierDate);
                  setOrderDate(today);
                  setPaymentReceivedDate(today);
                  setError("");
                }}
              />
              <span>
                This order was received on an earlier date.
                <span className="mt-1 block text-sm font-normal text-slate-600">
                  Leave this off for customers bringing laundry today.
                </span>
              </span>
            </label>

            {isEarlierOrder ? (
              <div className="mt-4">
                <label
                  className="block font-semibold text-slate-800"
                  htmlFor="order_date"
                >
                  Order received date
                </label>
                <input
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 sm:max-w-xs"
                  id="order_date"
                  type="date"
                  max={today}
                  value={orderDate}
                  disabled={isSubmitting}
                  onChange={(event) => {
                    setOrderDate(event.target.value);
                    setPaymentReceivedDate(event.target.value);
                    setError("");
                  }}
                />
                <p className="mt-2 text-sm text-slate-600">
                  The receipt will keep this business date. QLMS still records
                  when the entry was actually created.
                </p>
              </div>
            ) : null}
          </section>

          <section
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
            id="order-services-step"
          >
            <h2 className="text-xl font-bold text-slate-900">2. Services</h2>
            <p className="mt-2 text-slate-600">
              Search the shop catalogue and tap each service to add it to this
              ticket.
            </p>

            <div
              className="mt-5 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1.5 sm:max-w-md"
              aria-label="Service category"
            >
              {[
                { value: "general", label: "Laundry" },
                { value: "dry_cleaning", label: "Dry Cleaning" },
              ].map((category) => (
                <button
                  className={`min-h-11 rounded-lg px-4 font-bold ${
                    serviceCategoryToAdd === category.value
                      ? "bg-[#005AAB] text-white shadow-sm"
                      : "bg-transparent text-slate-700 hover:bg-white"
                  }`}
                  type="button"
                  aria-pressed={serviceCategoryToAdd === category.value}
                  disabled={isLoadingSetup || isSubmitting}
                  key={category.value}
                  onClick={() => {
                    setServiceCategoryToAdd(category.value);
                    setServiceSearch("");
                  }}
                >
                  {category.label}
                </button>
              ))}
            </div>

            <label
              className="mt-4 block font-semibold text-slate-800"
              htmlFor="service_search"
            >
              {serviceCategoryToAdd === "dry_cleaning"
                ? "Find a Dry Cleaning garment"
                : "Find a laundry service"}
            </label>
            <input
              className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="service_search"
              key={serviceCategoryToAdd}
              type="search"
              value={serviceSearch}
              disabled={isLoadingSetup || isSubmitting}
              placeholder={
                serviceCategoryToAdd === "dry_cleaning"
                  ? "Example: suit, shirt or dress"
                  : "Example: wash, duvet or iron"
              }
              onChange={(event) => setServiceSearch(event.target.value)}
            />

            {isLoadingSetup ? (
              <p className="mt-4 rounded-xl bg-slate-50 px-4 py-5 text-center text-sm text-slate-600">
                Loading services…
              </p>
            ) : availableCategoryServices.length > 0 ? (
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {availableCategoryServices.map((service) => (
                  <button
                    className="group flex min-h-24 items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 text-left hover:border-[#005AAB] hover:bg-blue-50 disabled:opacity-50"
                    type="button"
                    disabled={isSubmitting}
                    key={service.id}
                    onClick={() => addService(service.id)}
                  >
                    <span>
                      <span className="block font-bold text-slate-900 group-hover:text-[#005AAB]">
                        {getServiceDisplayName(service)}
                      </span>
                      <span className="mt-1 block text-sm text-slate-600">
                        {formatKes(service.unit_price)} per {service.unit}
                      </span>
                    </span>
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-blue-50 text-xl font-bold text-[#005AAB] group-hover:bg-[#005AAB] group-hover:text-white">
                      +
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center text-sm text-slate-600">
                {serviceSearch
                  ? "No available service matches this search."
                  : "Every service in this category is already on the ticket."}
              </p>
            )}

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
                  const discount = getServiceDiscount(serviceLine);
                  const serviceTotal = getServiceTotal(serviceLine);

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

                      <label
                        className="mt-4 block font-semibold text-slate-800"
                        htmlFor={`service-quantity-${serviceLine.service_id}`}
                      >
                        {serviceLine.item_recording_mode === "detailed"
                          ? `Charged quantity (${serviceLine.service_unit})`
                          : `Quantity (${serviceLine.service_unit})`}
                      </label>
                      <input
                        className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
                        id={`service-quantity-${serviceLine.service_id}`}
                        type="number"
                        min={serviceLine.service_unit === "kg" ? "0.1" : "1"}
                        step={serviceLine.service_unit === "kg" ? "0.1" : "1"}
                        value={serviceLine.quantity}
                        disabled={isSubmitting}
                        onChange={(event) =>
                          updateServiceLine(serviceLine.service_id, {
                            quantity: event.target.value,
                          })
                        }
                      />
                      {serviceLine.item_recording_mode === "detailed" &&
                      !serviceLine.defer_items ? (
                        <p className="mt-2 text-sm text-slate-600">
                          Price uses the charged quantity. Record every physical piece below.
                        </p>
                      ) : null}

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
                        onAddMissingItem={addMissingTallyItem}
                        onItemsChange={(items) =>
                          updateServiceLine(serviceLine.service_id, { items })
                        }
                      />

                      <div className="mt-4 border-t border-slate-200 pt-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <span className="font-semibold text-slate-600">
                            Service subtotal
                          </span>
                          <span className="text-lg font-bold text-slate-900">
                            {formatKes(subtotal)}
                          </span>
                        </div>

                        <button
                          className={`mt-3 min-h-10 rounded-lg border px-4 text-sm font-bold ${
                            serviceLine.discount_enabled
                              ? "border-amber-500 bg-amber-100 text-amber-950"
                              : "border-[#005AAB] bg-white text-[#005AAB] hover:bg-blue-50"
                          }`}
                          type="button"
                          aria-pressed={serviceLine.discount_enabled}
                          disabled={isSubmitting}
                          onClick={() => {
                            updateServiceLine(serviceLine.service_id, {
                              discount_enabled:
                                !serviceLine.discount_enabled,
                              discount_amount: "",
                            });
                            setError("");
                          }}
                        >
                          {serviceLine.discount_enabled
                            ? "Remove discount"
                            : "Add discount"}
                        </button>

                        {serviceLine.discount_enabled ? (
                          <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                            <label
                              className="block font-semibold text-slate-800"
                              htmlFor={`discount-${serviceLine.service_id}`}
                            >
                              Discount for this service (KES)
                            </label>
                            <input
                              className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 sm:max-w-xs"
                              id={`discount-${serviceLine.service_id}`}
                              type="number"
                              min="1"
                              max={Math.max(subtotal - 0.01, 0)}
                              step="1"
                              value={serviceLine.discount_amount}
                              disabled={isSubmitting}
                              onChange={(event) => {
                                updateServiceLine(serviceLine.service_id, {
                                  discount_amount: event.target.value,
                                });
                                setError("");
                              }}
                              placeholder="Example: 100"
                            />
                            <div className="mt-3 flex flex-wrap justify-between gap-2 text-sm">
                              <span className="text-amber-900">
                                Discount: {formatKes(discount)}
                              </span>
                              <span className="font-bold text-slate-900">
                                Final: {formatKes(serviceTotal)}
                              </span>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    </article>
                  );
                })}

                {estimatedDiscount > 0 ? (
                  <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
                    <label
                      className="block font-semibold text-slate-900"
                      htmlFor="discount_reason"
                    >
                      Why was this discount given?
                    </label>
                    <input
                      className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                      id="discount_reason"
                      type="text"
                      maxLength="120"
                      value={discountReason}
                      disabled={isSubmitting}
                      onChange={(event) => {
                        setDiscountReason(event.target.value);
                        setError("");
                      }}
                      placeholder="Example: Regular customer offer"
                    />
                    <p className="mt-2 text-sm text-amber-900">
                      The reason and staff username are kept with the order.
                    </p>
                  </div>
                ) : null}
              </div>
            )}
          </section>

          <section
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
            id="order-completion-step"
          >
            <h2 className="text-xl font-bold text-slate-900">
              3. Promised completion
            </h2>
            <p className="mt-2 text-slate-600">
              The system suggests a time from the slowest selected service.
              Confirm it with the customer or adjust it if needed.
            </p>

            <label className="mt-4 flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 font-semibold text-slate-800">
              <input
                className="mt-1"
                type="checkbox"
                checked={isPeakTime}
                disabled={isSubmitting}
                onChange={(event) => {
                  const nextIsPeakTime = event.target.checked;
                  setIsPeakTime(nextIsPeakTime);
                  setPromisedReadyAt(
                    getSuggestedReadyInput(selectedServices, nextIsPeakTime),
                  );
                  setError("");
                }}
              />
              <span>
                The shop is busy; add one hour to the suggested time.
                <span className="mt-1 block text-sm font-normal text-slate-600">
                  Use this only when the current workload needs extra time.
                </span>
              </span>
            </label>

            <label
              className="mt-4 block font-semibold text-slate-800"
              htmlFor="promised_ready_at"
            >
              Ready by
            </label>
            <input
              className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100 sm:max-w-md"
              id="promised_ready_at"
              type="datetime-local"
              value={promisedReadyAt}
              disabled={isSubmitting || selectedServices.length === 0}
              onChange={(event) => {
                setPromisedReadyAt(event.target.value);
                setError("");
              }}
            />
            {selectedServices.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">
                Add a service first so the system can suggest a time.
              </p>
            ) : null}
          </section>

          <section
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
            id="order-payment-step"
          >
            <h2 className="text-xl font-bold text-slate-900">4. Payment</h2>
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

                <div className="mt-4">
                  <label
                    className="block font-semibold text-slate-800"
                    htmlFor="payment_received_date"
                  >
                    Date payment was received
                  </label>
                  <input
                    className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 sm:max-w-xs"
                    id="payment_received_date"
                    type="date"
                    min={orderDate}
                    max={today}
                    value={paymentReceivedDate}
                    disabled={isSubmitting}
                    onChange={(event) => {
                      setPaymentReceivedDate(event.target.value);
                      setError("");
                    }}
                  />
                  <p className="mt-2 text-sm text-slate-600">
                    Finance reports use this date for cash and M-PESA received.
                  </p>
                </div>

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

        </div>

        <aside
          className="h-fit rounded-2xl border border-blue-200 bg-blue-50 p-5 lg:sticky lg:top-24"
          id="order-review-step"
        >
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
                    {formatKes(getServiceTotal(serviceLine))}
                  </span>
                </div>
              ))}
              {estimatedDiscount > 0 ? (
                <div className="space-y-2 border-t border-blue-200 pt-3 text-sm">
                  <div className="flex justify-between gap-3 text-slate-700">
                    <span>Catalogue subtotal</span>
                    <span className="font-semibold">
                      {formatKes(estimatedSubtotal)}
                    </span>
                  </div>
                  <div className="flex justify-between gap-3 font-semibold text-amber-900">
                    <span>Discount</span>
                    <span>-{formatKes(estimatedDiscount)}</span>
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Add services to see the estimated total.
            </p>
          )}

          <p className="mt-5 text-sm leading-6 text-slate-600">
            This is an estimate. QLMS uses the prices in Shop setup to calculate
            the final amount when you save.
          </p>

          <div className="mt-5 border-t border-blue-200 pt-4 text-sm">
            <p className="font-semibold text-slate-700">Order date</p>
            <p className="mt-1 font-bold text-slate-900">
              {formatDate(orderDate)}
            </p>
          </div>

          <div className="mt-5 border-t border-blue-200 pt-4 text-sm">
            <p className="font-semibold text-slate-700">Promised ready</p>
            <p className="mt-1 font-bold text-slate-900">
              {formatNairobiDateTime(promisedReadyAt, "Not set")}
            </p>
          </div>

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

          <button
            className="mt-6 inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
            type="submit"
            disabled={isSubmitting || isLoadingSetup || Boolean(orderSave.pending) || !orderSave.ready}
          >
            {isSubmitting ? "Creating order…" : "Create order"}
          </button>
          <p className="mt-3 text-center text-xs leading-5 text-slate-600">
            Check the details above before you create the order.
          </p>
        </aside>
        </fieldset>
      </form>

        <div className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-between gap-4 border-t border-slate-200 bg-white px-4 py-3 shadow-[0_-8px_25px_rgba(15,23,42,0.12)] lg:hidden">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Order estimate
            </p>
            <p className="mt-0.5 text-lg font-bold text-slate-900">
              {formatKes(estimatedTotal)}
            </p>
          </div>
          <button
            className="min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white disabled:cursor-wait disabled:opacity-60"
            type="submit"
            form="order-entry-form"
            disabled={isSubmitting || isLoadingSetup || Boolean(orderSave.pending) || !orderSave.ready}
          >
            {isSubmitting ? "Creating…" : "Create order"}
          </button>
        </div>
        </>
      ) : null}

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
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
            <div>
              <p className="text-sm text-slate-600">Customer</p>
              <p className="mt-1 font-bold text-slate-900">
                {createdOrder.customerName}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Order date</p>
              <p className="mt-1 font-bold text-slate-900">
                {formatDate(createdOrder.order_date)}
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
              <p className="text-sm text-slate-600">Promised ready</p>
              <p className="mt-1 font-bold text-slate-900">
                {formatNairobiDateTime(createdOrder.promised_ready_at, "Not set")}
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

          {Number(createdOrder.discount_amount) > 0 ? (
            <div className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4">
              <div className="flex flex-wrap justify-between gap-3">
                <span className="font-semibold text-slate-700">
                  Catalogue subtotal: {formatKes(createdOrder.subtotal_before_discount)}
                </span>
                <span className="font-bold text-amber-900">
                  Discount: -{formatKes(createdOrder.discount_amount)}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-700">
                Reason: {createdOrder.discount_reason} · Recorded by {" "}
                {createdOrder.discounted_by_username}
              </p>
            </div>
          ) : null}

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
                      <p className="text-xs font-semibold text-amber-900">
                        Saved {formatKes(serviceLine.discount_amount)}
                      </p>
                    ) : null}
                  </div>
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
                  {formatKes(payment.amount)} · Received {" "}
                  {formatDate(payment.received_date)}
                </p>
              ))}
            </div>
          ) : null}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button
              className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782]"
              type="button"
              onClick={startNextOrder}
            >
              Start next order
            </button>
            <button
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#005AAB] bg-white px-5 font-bold text-[#005AAB] hover:bg-blue-50"
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
