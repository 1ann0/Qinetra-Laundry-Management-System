"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SERVICES_BY_CODE } from "@/constants/pricing";
import { useAuth } from "@/context/auth-context";

const ORDER_STAGES = [
  {
    value: "received",
    label: "Received",
    number: "1",
    help: "Laundry has arrived",
    columnClass: "border-blue-200 bg-blue-50/70",
    headingClass: "bg-blue-600 text-white",
    cardBorderClass: "border-l-blue-600",
    bubbleClass: "border-blue-300 bg-blue-50 text-blue-900",
  },
  {
    value: "in_progress",
    label: "In Progress",
    number: "2",
    help: "Being washed or cleaned",
    columnClass: "border-amber-200 bg-amber-50/70",
    headingClass: "bg-amber-500 text-slate-950",
    cardBorderClass: "border-l-amber-500",
    bubbleClass: "border-amber-300 bg-amber-50 text-amber-950",
  },
  {
    value: "ready",
    label: "Ready for Collection",
    number: "3",
    help: "Waiting for the customer",
    columnClass: "border-emerald-200 bg-emerald-50/70",
    headingClass: "bg-emerald-600 text-white",
    cardBorderClass: "border-l-emerald-600",
    bubbleClass: "border-emerald-300 bg-emerald-50 text-emerald-950",
  },
  {
    value: "collected",
    label: "Collected",
    number: "4",
    help: "Finished and handed over",
    columnClass: "border-slate-300 bg-slate-100/80",
    headingClass: "bg-slate-700 text-white",
    cardBorderClass: "border-l-slate-600",
    bubbleClass: "border-slate-300 bg-slate-100 text-slate-900",
  },
];

function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function formatDateTime(value) {
  if (!value) {
    return "Not recorded";
  }

  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatDate(value) {
  if (!value) {
    return "Not recorded";
  }

  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeZone: "Africa/Nairobi",
  }).format(new Date(`${value}T00:00:00+03:00`));
}

function getStatusLabel(status) {
  return ORDER_STAGES.find((stage) => stage.value === status)?.label || status;
}

function getNextStatus(status) {
  if (status === "received") return "in_progress";
  if (status === "in_progress") return "ready";
  if (status === "ready") return "collected";
  return null;
}

function getActionLabel(status) {
  if (status === "received") return "Start this order";
  if (status === "in_progress") return "Mark ready for collection";
  if (status === "ready") return "Mark as collected";
  return "";
}

function getPaymentLabel(status) {
  if (status === "part_paid") return "Part paid";
  if (status === "paid") return "Paid";
  return "Not paid";
}

function getServiceSummary(order) {
  const serviceLines = order.service_lines || [];
  if (serviceLines.length > 0) {
    return serviceLines.map((line) => line.service_name).join(", ");
  }

  return SERVICES_BY_CODE[order.service_type]?.label || order.service_type;
}

function getOrderMoveState(order) {
  const hasPendingItemCheck = (order.service_lines || []).some(
    (line) => line.item_check_status === "pending",
  );
  const hasOutstandingBalance = Number(order.balance_due) > 0;
  const nextStatus = getNextStatus(order.status);
  const itemCheckBlocksNextStage =
    order.status === "in_progress" && hasPendingItemCheck;
  const paymentBlocksCollection =
    order.status === "ready" && hasOutstandingBalance;

  return {
    hasPendingItemCheck,
    hasOutstandingBalance,
    nextStatus,
    itemCheckBlocksNextStage,
    paymentBlocksCollection,
    canMoveForward:
      Boolean(nextStatus) &&
      !itemCheckBlocksNextStage &&
      !paymentBlocksCollection,
  };
}

function OrderCard({
  order,
  customerName,
  stage,
  isExpanded,
  isUpdating,
  isAnyOrderUpdating,
  isDueToday,
  isProductionLate,
  isCollectionOverdue,
  onToggleDetails,
  onMoveForward,
}) {
  const moveState = getOrderMoveState(order);
  const detailsId = `order-details-${order.id}`;

  return (
    <article
      className={`rounded-2xl border border-l-4 border-slate-200 bg-white p-4 shadow-sm ${stage.cardBorderClass}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-lg font-black text-slate-950">
            {customerName}
          </p>
          <p className="mt-1 font-mono text-sm font-bold text-[#005AAB]">
            {order.ticket_number}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-black ${
            order.payment_status === "paid"
              ? "bg-emerald-100 text-emerald-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {getPaymentLabel(order.payment_status)}
        </span>
      </div>

      <p className="mt-3 line-clamp-2 text-sm font-semibold leading-6 text-slate-700">
        {getServiceSummary(order)}
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        {isProductionLate ? (
          <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-black text-red-900">
            Production late
          </span>
        ) : null}
        {isDueToday ? (
          <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-black text-blue-900">
            Due today
          </span>
        ) : null}
        {isCollectionOverdue ? (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-black text-amber-950">
            Collection overdue
          </span>
        ) : null}
        {moveState.hasPendingItemCheck ? (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-black text-amber-950">
            Item check pending
          </span>
        ) : null}
      </div>

      <div className="mt-4 rounded-xl bg-slate-50 p-3">
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
          Promised ready
        </p>
        <p
          className={`mt-1 text-sm font-bold ${
            isProductionLate ? "text-red-800" : "text-slate-800"
          }`}
        >
          {order.promised_ready_at
            ? formatDateTime(order.promised_ready_at)
            : "Older order; no promise saved"}
        </p>
      </div>

      <button
        className="mt-3 flex min-h-10 w-full items-center justify-between rounded-xl border border-slate-200 px-3 text-left text-sm font-bold text-slate-700 hover:border-blue-300 hover:bg-blue-50"
        type="button"
        aria-expanded={isExpanded}
        aria-controls={detailsId}
        onClick={onToggleDetails}
      >
        <span>{isExpanded ? "Hide details" : "Show order details"}</span>
        <span aria-hidden="true">{isExpanded ? "−" : "+"}</span>
      </button>

      {isExpanded ? (
        <div className="mt-4 border-t border-slate-200 pt-4" id={detailsId}>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-slate-500">Order date</dt>
              <dd className="mt-1 font-bold text-slate-900">
                {formatDate(order.order_date)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Order value</dt>
              <dd className="mt-1 font-bold text-slate-900">
                {formatKes(order.total_price)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Paid</dt>
              <dd className="mt-1 font-bold text-emerald-800">
                {formatKes(order.amount_paid)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Balance</dt>
              <dd
                className={`mt-1 font-bold ${
                  moveState.hasOutstandingBalance
                    ? "text-red-800"
                    : "text-emerald-800"
                }`}
              >
                {formatKes(order.balance_due)}
              </dd>
            </div>
            {order.ready_at ? (
              <div className="col-span-2">
                <dt className="text-slate-500">Ready since</dt>
                <dd className="mt-1 font-bold text-slate-900">
                  {formatDateTime(order.ready_at)}
                </dd>
              </div>
            ) : null}
            {order.collected_at ? (
              <div className="col-span-2">
                <dt className="text-slate-500">Collected</dt>
                <dd className="mt-1 font-bold text-slate-900">
                  {formatDateTime(order.collected_at)}
                </dd>
              </div>
            ) : null}
          </dl>

          {moveState.itemCheckBlocksNextStage ? (
            <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm font-bold text-amber-950">
              Complete the clothing check before marking this order ready.
            </p>
          ) : null}
          {moveState.paymentBlocksCollection ? (
            <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm font-bold text-red-900">
              Record the {formatKes(order.balance_due)} balance before collection.
            </p>
          ) : null}

          <Link
            className="mt-4 inline-flex min-h-10 w-full items-center justify-center rounded-xl border border-[#005AAB] px-4 text-sm font-bold text-[#005AAB] no-underline hover:bg-blue-50"
            href={`/orders/${order.id}`}
          >
            {moveState.itemCheckBlocksNextStage
              ? "Complete item check"
              : moveState.paymentBlocksCollection
                ? "Record payment"
                : "Open receipt and full details"}
          </Link>
        </div>
      ) : null}

      {moveState.canMoveForward ? (
        <div className="mt-4">
          <button
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#005AAB] px-4 text-sm font-black text-white shadow-sm hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
            type="button"
            disabled={isAnyOrderUpdating}
            onClick={() => onMoveForward(order)}
          >
            {isUpdating ? "Updating…" : getActionLabel(order.status)}
          </button>
        </div>
      ) : order.status === "collected" ? (
        <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-center text-sm font-black text-emerald-800">
          Order complete
        </p>
      ) : null}
    </article>
  );
}

export default function OrderStatusPage() {
  const { authenticatedRequest } = useAuth();

  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [overdueCount, setOverdueCount] = useState(0);
  const [overdueOrderIds, setOverdueOrderIds] = useState([]);
  const [outstandingCount, setOutstandingCount] = useState(0);
  const [outstandingOrderIds, setOutstandingOrderIds] = useState([]);
  const [dueTodayCount, setDueTodayCount] = useState(0);
  const [dueTodayOrderIds, setDueTodayOrderIds] = useState([]);
  const [productionLateCount, setProductionLateCount] = useState(0);
  const [productionLateOrderIds, setProductionLateOrderIds] = useState([]);

  const [filter, setFilter] = useState("all");
  const [mobileStage, setMobileStage] = useState("received");
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedOrderId, setExpandedOrderId] = useState(null);
  const [refreshNumber, setRefreshNumber] = useState(0);

  const [isLoadingCustomers, setIsLoadingCustomers] = useState(true);
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [updatingOrderId, setUpdatingOrderId] = useState(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    const requestedFilter = new URLSearchParams(window.location.search).get(
      "filter",
    );
    const supportedFilters = [
      "received",
      "in_progress",
      "ready",
      "collected",
      "outstanding",
      "due_today",
      "production_late",
      "overdue",
    ];

    const filterTimer = window.setTimeout(() => {
      if (supportedFilters.includes(requestedFilter)) {
        setFilter(requestedFilter);
        if (ORDER_STAGES.some((stage) => stage.value === requestedFilter)) {
          setMobileStage(requestedFilter);
        }
      }
    }, 0);

    return () => window.clearTimeout(filterTimer);
  }, []);

  useEffect(() => {
    async function loadCustomers() {
      try {
        const response = await authenticatedRequest("/customers");
        setCustomers(response);
      } catch (loadError) {
        setError(loadError.message || "Customer names could not be loaded.");
      } finally {
        setIsLoadingCustomers(false);
      }
    }

    loadCustomers();
  }, [authenticatedRequest]);

  useEffect(() => {
    async function loadOrders() {
      setIsLoadingOrders(true);
      setError("");

      const searchQuery = searchTerm
        ? `?search=${encodeURIComponent(searchTerm)}`
        : "";

      try {
        const [
          orderResponse,
          overdueResponse,
          outstandingResponse,
          dueTodayResponse,
          productionLateResponse,
        ] = await Promise.all([
          authenticatedRequest(`/orders${searchQuery}`),
          authenticatedRequest("/orders/overdue"),
          authenticatedRequest("/orders?outstanding=true"),
          authenticatedRequest("/orders?due_today=true"),
          authenticatedRequest("/orders?production_late=true"),
        ]);

        setOrders(orderResponse);
        setMobileStage((currentStage) =>
          orderResponse.some((order) => order.status === currentStage)
            ? currentStage
            : orderResponse[0]?.status || currentStage,
        );
        setOverdueCount(overdueResponse.length);
        setOverdueOrderIds(overdueResponse.map((order) => order.id));
        setOutstandingCount(outstandingResponse.length);
        setOutstandingOrderIds(outstandingResponse.map((order) => order.id));
        setDueTodayCount(dueTodayResponse.length);
        setDueTodayOrderIds(dueTodayResponse.map((order) => order.id));
        setProductionLateCount(productionLateResponse.length);
        setProductionLateOrderIds(
          productionLateResponse.map((order) => order.id),
        );
      } catch (loadError) {
        setError(loadError.message || "Orders could not be loaded.");
        setOrders([]);
      } finally {
        setIsLoadingOrders(false);
      }
    }

    loadOrders();
  }, [authenticatedRequest, refreshNumber, searchTerm]);

  const customerNames = Object.fromEntries(
    customers.map((customer) => [customer.id, customer.name]),
  );

  const visibleOrders = orders.filter((order) => {
    if (filter === "all") return true;
    if (ORDER_STAGES.some((stage) => stage.value === filter)) {
      return order.status === filter;
    }
    if (filter === "overdue") return overdueOrderIds.includes(order.id);
    if (filter === "outstanding") return outstandingOrderIds.includes(order.id);
    if (filter === "due_today") return dueTodayOrderIds.includes(order.id);
    if (filter === "production_late") {
      return productionLateOrderIds.includes(order.id);
    }
    return true;
  });

  const ordersByStage = Object.fromEntries(
    ORDER_STAGES.map((stage) => [
      stage.value,
      visibleOrders.filter((order) => order.status === stage.value),
    ]),
  );
  const searchCountsByStage = Object.fromEntries(
    ORDER_STAGES.map((stage) => [
      stage.value,
      orders.filter((order) => order.status === stage.value).length,
    ]),
  );

  function chooseFilter(nextFilter) {
    setFilter(nextFilter);
    setSuccessMessage("");
    if (ORDER_STAGES.some((stage) => stage.value === nextFilter)) {
      setMobileStage(nextFilter);
      return;
    }

    const riskIds =
      nextFilter === "overdue"
        ? overdueOrderIds
        : nextFilter === "outstanding"
          ? outstandingOrderIds
          : nextFilter === "due_today"
            ? dueTodayOrderIds
            : nextFilter === "production_late"
              ? productionLateOrderIds
              : [];
    const firstMatchingOrder = orders.find((order) =>
      riskIds.includes(order.id),
    );
    if (firstMatchingOrder) {
      setMobileStage(firstMatchingOrder.status);
    }
  }

  function submitSearch(event) {
    event.preventDefault();
    setFilter("all");
    setSearchTerm(searchInput.trim());
    setExpandedOrderId(null);
    setSuccessMessage("");
  }

  function clearSearch() {
    setSearchInput("");
    setSearchTerm("");
    setExpandedOrderId(null);
  }

  async function updateStatus(order) {
    const moveState = getOrderMoveState(order);
    if (!moveState.canMoveForward) {
      return;
    }

    if (
      order.status === "ready" &&
      !window.confirm(
        `Mark ${order.ticket_number} as collected and handed to the customer?`,
      )
    ) {
      return;
    }

    const nextStatus = moveState.nextStatus;
    setUpdatingOrderId(order.id);
    setError("");
    setSuccessMessage("");

    try {
      const updatedOrder = await authenticatedRequest(
        `/orders/${order.id}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus }),
        },
      );

      setOrders((currentOrders) =>
        currentOrders.map((currentOrder) =>
          currentOrder.id === updatedOrder.id ? updatedOrder : currentOrder,
        ),
      );
      if (!ORDER_STAGES.some((stage) => stage.value === filter)) {
        setMobileStage(nextStatus);
      }
      setSuccessMessage(
        `${order.ticket_number} moved to ${getStatusLabel(nextStatus)}.`,
      );
      setRefreshNumber((currentNumber) => currentNumber + 1);
    } catch (updateError) {
      setError(updateError.message || "The order status could not be updated.");
    } finally {
      setUpdatingOrderId(null);
    }
  }

  return (
    <section className="mx-auto max-w-[1600px]">
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
            Daily production board
          </p>
          <h1 className="text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
            Where is each order?
          </h1>
          <p className="mt-3 max-w-3xl leading-7 text-slate-600">
            Find a customer or ticket, open its card, then move it one clear
            step forward using the large action button.
          </p>
        </div>

        <Link
          className="inline-flex min-h-11 items-center justify-center whitespace-nowrap rounded-xl bg-[#005AAB] px-5 font-black text-white no-underline shadow-sm hover:bg-[#004782]"
          href="/orders"
        >
          + Create new order
        </Link>
      </div>

      <form
        className="mb-5 rounded-2xl border border-blue-200 bg-white p-4 shadow-sm sm:p-5"
        id="status-search-step"
        onSubmit={submitSearch}
      >
        <label
          className="mb-2 block text-base font-black text-slate-900"
          htmlFor="order-search"
        >
          Find an order
        </label>
        <p className="mb-3 text-sm text-slate-600">
          Search using a ticket number, customer name, phone number or service.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="min-h-12 flex-1 rounded-xl border border-slate-300 px-4 text-base text-slate-950 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
            id="order-search"
            type="search"
            value={searchInput}
            placeholder="Example: Alice, 0712, QL-2026 or Dry Cleaning"
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <button
            className="min-h-12 rounded-xl bg-[#005AAB] px-6 font-black text-white hover:bg-[#004782]"
            type="submit"
          >
            Search orders
          </button>
          {searchTerm ? (
            <button
              className="min-h-12 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50"
              type="button"
              onClick={clearSearch}
            >
              Clear
            </button>
          ) : null}
        </div>
        {searchTerm ? (
          <p className="mt-3 text-sm font-bold text-[#005AAB]" role="status">
            Showing matches for “{searchTerm}”.
          </p>
        ) : null}
      </form>

      <section
        className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4"
        id="status-stages-step"
        aria-label="Choose a stage on smaller screens"
      >
        {ORDER_STAGES.map((stage) => {
          const count = searchCountsByStage[stage.value];
          const isSelected = mobileStage === stage.value;

          return (
            <button
              className={`rounded-2xl border-2 p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md ${stage.bubbleClass} ${
                isSelected ? "ring-4 ring-blue-100" : ""
              }`}
              type="button"
              key={stage.value}
              aria-pressed={isSelected}
              onClick={() => setMobileStage(stage.value)}
            >
              <span className="flex items-center justify-between gap-2">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-base font-black shadow-sm">
                  {stage.number}
                </span>
                <span className="rounded-full bg-white px-3 py-1 text-sm font-black shadow-sm">
                  {count}
                </span>
              </span>
              <span className="mt-3 block text-base font-black sm:text-lg">
                {stage.label}
              </span>
              <span className="mt-1 block text-xs font-semibold opacity-80 sm:text-sm">
                {stage.help}
              </span>
            </button>
          );
        })}
      </section>

      <section
        className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        id="status-focus-step"
      >
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="w-full xl:max-w-xs">
            <label
              className="mb-2 block font-black text-slate-800"
              htmlFor="status-filter"
            >
              Show me
            </label>
            <select
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
              id="status-filter"
              value={filter}
              onChange={(event) => chooseFilter(event.target.value)}
            >
              <option value="all">All matching orders</option>
              {ORDER_STAGES.map((stage) => (
                <option key={stage.value} value={stage.value}>
                  {stage.label}
                </option>
              ))}
              <option value="due_today">Promised for today</option>
              <option value="production_late">Production late</option>
              <option value="outstanding">Outstanding payment</option>
              <option value="overdue">Collection overdue</option>
            </select>
          </div>

          <div className="grid flex-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
            <button
              className="min-h-12 rounded-xl border border-blue-300 bg-blue-50 px-3 font-black text-blue-900 hover:bg-blue-100"
              type="button"
              onClick={() => chooseFilter("due_today")}
            >
              Due today · {dueTodayCount}
            </button>
            <button
              className="min-h-12 rounded-xl border border-red-300 bg-red-50 px-3 font-black text-red-900 hover:bg-red-100"
              type="button"
              onClick={() => chooseFilter("production_late")}
            >
              Production late · {productionLateCount}
            </button>
            <button
              className="min-h-12 rounded-xl border border-red-300 bg-red-50 px-3 font-black text-red-900 hover:bg-red-100"
              type="button"
              onClick={() => chooseFilter("outstanding")}
            >
              Money outstanding · {outstandingCount}
            </button>
            <button
              className="min-h-12 rounded-xl border border-amber-300 bg-amber-50 px-3 font-black text-amber-950 hover:bg-amber-100"
              type="button"
              onClick={() => chooseFilter("overdue")}
            >
              Collection overdue · {overdueCount}
            </button>
          </div>
        </div>
      </section>

      {error ? (
        <p
          className="mb-5 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {successMessage ? (
        <p
          className="mb-5 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-800"
          role="status"
        >
          {successMessage}
        </p>
      ) : null}

      {isLoadingOrders || isLoadingCustomers ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-10 text-center font-semibold text-slate-600">
          Loading the production board…
        </p>
      ) : visibleOrders.length === 0 ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <h2 className="text-xl font-black text-slate-950">No orders found</h2>
          <p className="mt-2 text-slate-600">
            Try another name, ticket, phone, service or filter.
          </p>
          {searchTerm ? (
            <button
              className="mt-5 min-h-11 rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] hover:bg-blue-50"
              type="button"
              onClick={clearSearch}
            >
              Clear search
            </button>
          ) : null}
        </section>
      ) : (
        <section id="status-board-step" aria-label="Order production board">
          <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-bold text-slate-700">
              Showing {visibleOrders.length} {visibleOrders.length === 1 ? "order" : "orders"}
            </p>
            <p className="hidden text-sm text-slate-500 lg:block">
              Each action moves an order forward by exactly one stage.
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-4">
            {ORDER_STAGES.map((stage) => {
              const stageOrders = ordersByStage[stage.value];
              const isMobileStage = mobileStage === stage.value;

              return (
                <section
                  className={`${
                    isMobileStage ? "block" : "hidden lg:block"
                  } min-h-64 rounded-2xl border-2 p-3 ${stage.columnClass}`}
                  id={`status-column-${stage.value}`}
                  key={stage.value}
                >
                  <div className={`rounded-xl p-4 ${stage.headingClass}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-lg font-black">{stage.label}</p>
                        <p className="mt-1 text-xs font-semibold opacity-90">
                          {stage.help}
                        </p>
                      </div>
                      <span className="flex h-10 min-w-10 items-center justify-center rounded-full bg-white px-3 font-black text-slate-900 shadow-sm">
                        {stageOrders.length}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 space-y-3">
                    {stageOrders.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-slate-300 bg-white/70 p-6 text-center text-sm font-semibold text-slate-500">
                        {`No ${stage.label.toLowerCase()} orders in this view`}
                      </div>
                    ) : (
                      stageOrders.map((order) => (
                        <OrderCard
                          key={order.id}
                          order={order}
                          customerName={
                            customerNames[order.customer_id] ||
                            `Customer ${order.customer_id}`
                          }
                          stage={stage}
                          isExpanded={expandedOrderId === order.id}
                          isUpdating={updatingOrderId === order.id}
                          isAnyOrderUpdating={updatingOrderId !== null}
                          isDueToday={dueTodayOrderIds.includes(order.id)}
                          isProductionLate={productionLateOrderIds.includes(
                            order.id,
                          )}
                          isCollectionOverdue={overdueOrderIds.includes(order.id)}
                          onToggleDetails={() =>
                            setExpandedOrderId((currentId) =>
                              currentId === order.id ? null : order.id,
                            )
                          }
                          onMoveForward={updateStatus}
                        />
                      ))
                    )}
                  </div>
                </section>
              );
            })}
          </div>
        </section>
      )}

    </section>
  );
}
