"use client";

import { getUserMessage } from "@/lib/user-messages";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SERVICES_BY_CODE } from "@/constants/pricing";
import { useAuth } from "@/context/auth-context";
import { formatNairobiDateTime } from "@/lib/format-nairobi";

const ORDER_STAGES = [
  {
    value: "received",
    label: "Received",
    help: "Laundry has arrived",
  },
  {
    value: "in_progress",
    label: "In Progress",
    help: "Being washed or cleaned",
  },
  {
    value: "ready",
    label: "Ready for Collection",
    help: "Waiting for the customer",
  },
  {
    value: "collected",
    label: "Collected",
    help: "Finished and handed over",
  },
];

function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
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
  if (status === "cancelled") return "Cancelled";
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
  const activeHold = (order.holds || []).find((hold) => !hold.resolved_at);
  const hasOutstandingBalance = Number(order.balance_due) > 0;
  const nextStatus = getNextStatus(order.status);
  const itemCheckBlocksNextStage =
    ["received", "in_progress"].includes(order.status) && hasPendingItemCheck;
  const holdBlocksNextStage =
    ["received", "in_progress"].includes(order.status) && Boolean(activeHold);
  const paymentBlocksCollection =
    order.status === "ready" && hasOutstandingBalance;

  return {
    hasPendingItemCheck,
    hasOutstandingBalance,
    activeHold,
    nextStatus,
    itemCheckBlocksNextStage,
    holdBlocksNextStage,
    paymentBlocksCollection,
    canMoveForward:
      Boolean(nextStatus) &&
      !itemCheckBlocksNextStage &&
      !holdBlocksNextStage &&
      !paymentBlocksCollection,
  };
}

function OrderCard({
  order,
  customerName,
  isUpdating,
  isAnyOrderUpdating,
  isDueToday,
  isProductionLate,
  isCollectionOverdue,
  onMoveForward,
}) {
  const moveState = getOrderMoveState(order);
  const currentStage = ORDER_STAGES.findIndex(
    (stage) => stage.value === order.status,
  );
  const serviceLines = order.service_lines || [];

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-500">Ticket number</p>
          <h2 className="mt-1 break-words text-2xl font-bold text-slate-900">
            {order.ticket_number}
          </h2>
          <p className="mt-2 break-words text-lg font-semibold text-slate-800">
            {customerName}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {isProductionLate ? (
            <span className="w-fit rounded-full bg-red-100 px-4 py-2 text-sm font-bold text-red-900">
              Production late
            </span>
          ) : null}
          {isDueToday ? (
            <span className="w-fit rounded-full bg-blue-100 px-4 py-2 text-sm font-bold text-[#005AAB]">
              Due today
            </span>
          ) : null}
          {isCollectionOverdue ? (
            <span className="w-fit rounded-full bg-amber-100 px-4 py-2 text-sm font-bold text-amber-900">
              Collection overdue
            </span>
          ) : null}
          {moveState.hasPendingItemCheck ? (
            <span className="w-fit rounded-full bg-amber-100 px-4 py-2 text-sm font-bold text-amber-900">
              Item check pending
            </span>
          ) : null}
          <span
            className={`w-fit rounded-full px-4 py-2 text-sm font-bold ${
              order.payment_status === "paid"
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {getPaymentLabel(order.payment_status)}
          </span>
          <span className="w-fit rounded-full bg-blue-100 px-4 py-2 text-sm font-bold text-[#005AAB]">
            {getStatusLabel(order.status)}
          </span>
        </div>
      </div>

      <div className="my-5 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <div>
          <p className="text-sm text-slate-500">Service</p>
          <p className="mt-1 break-words font-semibold text-slate-900">
            {getServiceSummary(order)}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-500">Quantity</p>
          <p className="mt-1 font-semibold text-slate-900">
            {serviceLines.length > 0
              ? `${serviceLines.length} ${serviceLines.length === 1 ? "service" : "services"}`
              : `${order.quantity} ${SERVICES_BY_CODE[order.service_type]?.unit || "units"}`}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-500">{order.status === "cancelled" ? "Original order value" : "Order value"}</p>
          <p className="mt-1 font-semibold text-slate-900">
            {formatKes(order.total_price)}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-500">Balance</p>
          <p
            className={`mt-1 font-semibold ${
              moveState.hasOutstandingBalance ? "text-red-700" : "text-green-700"
            }`}
          >
            {formatKes(order.balance_due)}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-500">Promised ready</p>
          <p className="mt-1 font-semibold text-slate-900">
            {order.promised_ready_at
              ? formatNairobiDateTime(order.promised_ready_at)
              : "Older order; not set"}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-500">Order date</p>
          <p className="mt-1 font-semibold text-slate-900">
            {formatDate(order.order_date)}
          </p>
        </div>
      </div>

      {order.status === "cancelled" ? (
        <p className="mb-5 rounded-xl border border-slate-300 bg-slate-50 p-3 font-semibold text-slate-800">
          This ticket was cancelled. Open the order to see why.
        </p>
      ) : <div className="mb-5 grid gap-2 sm:grid-cols-4" aria-label="Ticket progress">
        {ORDER_STAGES.map((stage, index) => {
          const hasReachedStage = index <= currentStage;

          return (
            <div
              className={`rounded-lg border px-3 py-2 text-center text-xs font-bold ${
                hasReachedStage
                  ? "border-[#005AAB] bg-blue-50 text-[#005AAB]"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
              key={stage.value}
              aria-current={stage.value === order.status ? "step" : undefined}
            >
              {stage.label}
            </div>
          );
        })}
      </div>}

      {order.ready_at || order.collected_at ? (
        <div className="mb-5 grid gap-3 rounded-xl bg-slate-50 p-4 text-sm sm:grid-cols-2">
          {order.ready_at ? (
            <p>
              <span className="font-semibold text-slate-700">Ready since:</span>{" "}
              {formatNairobiDateTime(order.ready_at)}
            </p>
          ) : null}
          {order.collected_at ? (
            <p>
              <span className="font-semibold text-slate-700">Collected:</span>{" "}
              {formatNairobiDateTime(order.collected_at)}
            </p>
          ) : null}
        </div>
      ) : null}

      {moveState.nextStatus ? (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="mb-2 text-sm font-bold text-slate-700">Next action</p>
            {moveState.itemCheckBlocksNextStage ? (
              <p className="text-sm font-semibold text-amber-900">
                Complete the clothing check before washing starts.
              </p>
            ) : moveState.holdBlocksNextStage ? (
              <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2">
                <p className="text-sm font-bold text-amber-950">
                  Waiting for customer reply
                </p>
                <p className="mt-1 text-sm text-amber-900">
                  {moveState.activeHold.reason}
                </p>
              </div>
            ) : moveState.paymentBlocksCollection ? (
              <p className="text-sm font-semibold text-red-800">
                Record the {formatKes(order.balance_due)} balance before collection.
              </p>
            ) : (
              <p className="text-sm text-slate-600">
                {getActionLabel(order.status)}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
              href={`/orders/${order.id}`}
            >
              {moveState.itemCheckBlocksNextStage
                ? "Complete item check"
                : moveState.holdBlocksNextStage
                  ? "Record customer reply"
                : moveState.paymentBlocksCollection
                  ? "Record payment"
                  : "View order and receipt"}
            </Link>
            {moveState.canMoveForward ? (
              <button
                className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white shadow-sm hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
                type="button"
                disabled={isAnyOrderUpdating}
                onClick={() => onMoveForward(order)}
              >
                {isUpdating ? "Updating…" : getActionLabel(order.status)}
              </button>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-semibold text-green-700">
            {order.status === "cancelled" ? "Order cancelled." : "Order completed and collected."}
          </p>
          <Link
            className="font-bold text-[#005AAB] hover:underline"
            href={`/orders/${order.id}`}
          >
            View order and receipt
          </Link>
        </div>
      )}
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
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [refreshNumber, setRefreshNumber] = useState(0);

  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [ordersLoadFailed, setOrdersLoadFailed] = useState(false);
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
      }
    }, 0);

    return () => window.clearTimeout(filterTimer);
  }, []);

  useEffect(() => {
    let ignoreResponse = false;
    async function loadOrders() {
      setIsLoadingOrders(true);
      setOrdersLoadFailed(false);
      setError("");

      const searchQuery = searchTerm
        ? `?search=${encodeURIComponent(searchTerm)}`
        : "";

      try {
        const [
          customerResponse,
          orderResponse,
          overdueResponse,
          outstandingResponse,
          dueTodayResponse,
          productionLateResponse,
        ] = await Promise.all([
          authenticatedRequest("/customers"),
          authenticatedRequest(`/orders${searchQuery}`),
          authenticatedRequest("/orders/overdue"),
          authenticatedRequest("/orders?outstanding=true"),
          authenticatedRequest("/orders?due_today=true"),
          authenticatedRequest("/orders?production_late=true"),
        ]);

        if (ignoreResponse) return;
        setCustomers(customerResponse);
        setOrders(orderResponse);
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
        if (ignoreResponse) return;
        setError(getUserMessage(loadError, "Orders could not be loaded."));
        setOrdersLoadFailed(true);
        setOrders([]);
      } finally {
        if (!ignoreResponse) setIsLoadingOrders(false);
      }
    }

    loadOrders();
    return () => { ignoreResponse = true; };
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

  const searchCountsByStage = Object.fromEntries(
    ORDER_STAGES.map((stage) => [
      stage.value,
      orders.filter((order) => order.status === stage.value).length,
    ]),
  );

  function chooseFilter(nextFilter) {
    setFilter(nextFilter);
    setSuccessMessage("");
  }

  function submitSearch(event) {
    event.preventDefault();
    setFilter("all");
    setSearchTerm(searchInput.trim());
    setSuccessMessage("");
  }

  function clearSearch() {
    setSearchInput("");
    setSearchTerm("");
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
      setSuccessMessage(
        `${order.ticket_number} moved to ${getStatusLabel(nextStatus)}.`,
      );
      setRefreshNumber((currentNumber) => currentNumber + 1);
    } catch (updateError) {
      setError(getUserMessage(updateError, "QLMS could not confirm the new stage. Check Track orders before you move the order again."));
    } finally {
      setUpdatingOrderId(null);
    }
  }

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
            Laundry progress
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Track laundry orders
          </h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            Find a customer or ticket, then follow each order through the
            laundry process one clear step at a time.
          </p>
        </div>

        <Link
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
          href="/orders"
        >
          Create new order
        </Link>
      </div>

      <form
        className="mb-5 rounded-2xl border border-blue-200 bg-white p-4 shadow-sm sm:p-5"
        id="status-search-step"
        onSubmit={submitSearch}
      >
        <label
          className="mb-2 block text-base font-bold text-slate-900"
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
            className="min-h-12 rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782]"
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
        className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        id="status-stages-step"
        aria-label="Filter orders by status stage"
      >
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">View orders by stage</h2>
            <p className="mt-1 text-sm text-slate-600">Select a stage to see its orders below. This does not change an order.</p>
          </div>
          <button
            className="min-h-11 cursor-pointer rounded-xl border border-[#005AAB] px-4 font-semibold text-[#005AAB] hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB]"
            type="button"
            aria-pressed={filter === "all"}
            aria-controls="status-results"
            onClick={() => chooseFilter("all")}
          >
            View all orders
          </button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {ORDER_STAGES.map((stage, index) => {
          const count = searchCountsByStage[stage.value];
          const isSelected = filter === stage.value;

          return (
            <button
              className={`cursor-pointer rounded-xl border-2 px-4 py-3 text-left shadow-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB] disabled:cursor-wait disabled:opacity-60 ${
                isSelected
                  ? "border-[#005AAB] bg-blue-50 text-[#005AAB]"
                  : "border-blue-200 bg-white text-slate-800 hover:border-[#005AAB] hover:bg-blue-50"
              }`}
              type="button"
              key={stage.value}
              aria-pressed={isSelected}
              aria-controls="status-results"
              disabled={isLoadingOrders || ordersLoadFailed}
              onClick={() => chooseFilter(stage.value)}
            >
              <span className="flex items-center justify-between gap-3 text-xs font-bold uppercase tracking-wide">
                <span>
                  Step {index + 1}
                </span>
                <span className="normal-case tracking-normal text-slate-600">
                  {isLoadingOrders || ordersLoadFailed ? "—" : `${count} ${count === 1 ? "order" : "orders"}`}
                </span>
              </span>
              <span className="mt-2 block text-base font-bold">
                {stage.label}
              </span>
              <span className="mt-1 block text-xs text-slate-500">
                {stage.help}
              </span>
              <span className="mt-3 flex items-center justify-between border-t border-blue-200 pt-3 text-sm font-bold text-[#005AAB]">
                {isSelected ? "Showing these orders" : "View orders"}
                <span aria-hidden="true">{isSelected ? "✓" : "→"}</span>
              </span>
            </button>
          );
        })}
        </div>
      </section>

      {!isLoadingOrders && !ordersLoadFailed ? <section
        className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        id="status-focus-step"
      >
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="w-full xl:max-w-xs">
            <label
              className="mb-2 block font-bold text-slate-800"
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
              className="min-h-12 rounded-xl border border-blue-300 bg-blue-50 px-3 font-bold text-blue-900 hover:bg-blue-100"
              type="button"
              onClick={() => chooseFilter("due_today")}
            >
              Due today · {dueTodayCount}
            </button>
            <button
              className="min-h-12 rounded-xl border border-red-300 bg-red-50 px-3 font-bold text-red-900 hover:bg-red-100"
              type="button"
              onClick={() => chooseFilter("production_late")}
            >
              Production late · {productionLateCount}
            </button>
            <button
              className="min-h-12 rounded-xl border border-red-300 bg-red-50 px-3 font-bold text-red-900 hover:bg-red-100"
              type="button"
              onClick={() => chooseFilter("outstanding")}
            >
              Money outstanding · {outstandingCount}
            </button>
            <button
              className="min-h-12 rounded-xl border border-amber-300 bg-amber-50 px-3 font-bold text-amber-950 hover:bg-amber-100"
              type="button"
              onClick={() => chooseFilter("overdue")}
            >
              Collection overdue · {overdueCount}
            </button>
          </div>
        </div>
      </section> : null}

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

      <div id="status-results" aria-busy={isLoadingOrders}>
      {isLoadingOrders ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-10 text-center font-semibold text-slate-600">
          Loading orders…
        </p>
      ) : ordersLoadFailed ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 text-center">
          <h2 className="text-xl font-bold text-slate-900">Orders are not available yet</h2>
          <p className="mt-2 text-slate-600">Use the advice above, then try to load the orders again.</p>
          <button
            className="mt-4 min-h-11 cursor-pointer rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB]"
            type="button"
            onClick={() => setRefreshNumber((number) => number + 1)}
          >
            Try loading orders again
          </button>
        </section>
      ) : visibleOrders.length === 0 ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">No orders found</h2>
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
        <section id="status-board-step" aria-label="Laundry orders">
          <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-bold text-slate-700" role="status">
              Showing {visibleOrders.length} {visibleOrders.length === 1 ? "order" : "orders"}
              {ORDER_STAGES.some((stage) => stage.value === filter) ? ` · ${getStatusLabel(filter)}` : ""}
            </p>
            <p className="hidden text-sm text-slate-500 lg:block">
              Each action moves an order forward by exactly one stage.
            </p>
          </div>

          <div className="space-y-5">
            {visibleOrders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                customerName={
                  customerNames[order.customer_id] ||
                  `Customer ${order.customer_id}`
                }
                isUpdating={updatingOrderId === order.id}
                isAnyOrderUpdating={updatingOrderId !== null}
                isDueToday={dueTodayOrderIds.includes(order.id)}
                isProductionLate={productionLateOrderIds.includes(order.id)}
                isCollectionOverdue={overdueOrderIds.includes(order.id)}
                onMoveForward={updateStatus}
              />
            ))}
          </div>
        </section>
      )}
      </div>

    </section>
  );
}
