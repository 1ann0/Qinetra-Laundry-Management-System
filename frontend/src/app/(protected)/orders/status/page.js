"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SERVICES_BY_CODE } from "@/constants/pricing";
import { useAuth } from "@/context/auth-context";

// Keep the four backend status values in their correct working order.
const ORDER_STAGES = [
  { value: "received", label: "Received" },
  { value: "in_progress", label: "In Progress" },
  { value: "ready", label: "Ready for Collection" },
  { value: "collected", label: "Collected" },
];

// Display money in the same KES format used on the order-entry screen.
function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

// Make backend timestamps easier for staff to read during daily work.
function formatDateTime(value) {
  if (!value) {
    return "Not recorded";
  }

  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

// Find a friendly label without changing the status value sent to the API.
function getStatusLabel(status) {
  return ORDER_STAGES.find((stage) => stage.value === status)?.label || status;
}

// Allow only the next normal stage instead of offering status jumps or reversals.
function getNextStatus(status) {
  if (status === "received") return "in_progress";
  if (status === "in_progress") return "ready";
  if (status === "ready") return "collected";
  return null;
}

// Use action wording that makes the result of each button clear.
function getActionLabel(status) {
  if (status === "received") return "Mark in progress";
  if (status === "in_progress") return "Mark ready for collection";
  if (status === "ready") return "Mark collected";
  return "";
}

export default function OrderStatusPage() {
  const { authenticatedRequest } = useAuth();

  // Store the records needed to show orders with customer names.
  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [overdueCount, setOverdueCount] = useState(0);
  const [overdueOrderIds, setOverdueOrderIds] = useState([]);

  // Track the selected list and rerun loading after a successful update.
  const [filter, setFilter] = useState("all");
  const [refreshNumber, setRefreshNumber] = useState(0);

  // Keep loading and feedback states separate so the page explains what is happening.
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(true);
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [updatingOrderId, setUpdatingOrderId] = useState(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Load customers once because order responses only contain a customer ID.
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

  // Load the selected order list and the current overdue total from the backend.
  useEffect(() => {
    async function loadOrders() {
      setIsLoadingOrders(true);
      setError("");

      const orderPath =
        filter === "overdue"
          ? "/orders/overdue"
          : filter === "all"
            ? "/orders"
            : `/orders?status=${filter}`;

      try {
        const [orderResponse, overdueResponse] = await Promise.all([
          authenticatedRequest(orderPath),
          authenticatedRequest("/orders/overdue"),
        ]);

        setOrders(orderResponse);
        setOverdueCount(overdueResponse.length);
        setOverdueOrderIds(overdueResponse.map((order) => order.id));
      } catch (loadError) {
        setError(loadError.message || "Orders could not be loaded.");
        setOrders([]);
      } finally {
        setIsLoadingOrders(false);
      }
    }

    loadOrders();
  }, [authenticatedRequest, filter, refreshNumber]);

  // Match each customer ID to a name while keeping the displayed order data simple.
  const customerNames = Object.fromEntries(
    customers.map((customer) => [customer.id, customer.name]),
  );

  // Send the next stage to FastAPI, then refresh the visible records and overdue count.
  async function updateStatus(order) {
    const nextStatus = getNextStatus(order.status);

    if (!nextStatus) {
      return;
    }

    setUpdatingOrderId(order.id);
    setError("");
    setSuccessMessage("");

    try {
      await authenticatedRequest(`/orders/${order.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });

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
    <section className="mx-auto max-w-6xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
            Status and overdue module
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Track laundry orders
          </h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            Follow each ticket through the laundry process and find orders that
            have waited too long for collection.
          </p>
        </div>

        <Link
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
          href="/orders"
        >
          Create new order
        </Link>
      </div>

      <section
        className="mb-8 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-4 sm:p-5"
        aria-label="Order status stages"
      >
        {ORDER_STAGES.map((stage, index) => (
          <div className="flex items-center gap-3" key={stage.value}>
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#005AAB] font-bold text-white">
              {index + 1}
            </span>
            <span className="font-semibold text-slate-800">{stage.label}</span>
          </div>
        ))}
      </section>

      <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="w-full sm:max-w-xs">
            <label className="mb-2 block font-semibold text-slate-800" htmlFor="status-filter">
              Show orders
            </label>
            <select
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
              id="status-filter"
              value={filter}
              onChange={(event) => {
                setFilter(event.target.value);
                setSuccessMessage("");
              }}
            >
              <option value="all">All statuses</option>
              {ORDER_STAGES.map((stage) => (
                <option key={stage.value} value={stage.value}>
                  {stage.label}
                </option>
              ))}
              <option value="overdue">Overdue collection</option>
            </select>
          </div>

          <button
            className="inline-flex min-h-12 items-center justify-center rounded-xl border border-amber-300 bg-amber-50 px-5 font-bold text-amber-900 hover:bg-amber-100"
            type="button"
            onClick={() => {
              setFilter("overdue");
              setSuccessMessage("");
            }}
          >
            Overdue orders: {overdueCount}
          </button>
        </div>
      </section>

      {error ? (
        <p
          className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {successMessage ? (
        <p
          className="mb-6 rounded-xl border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800"
          role="status"
        >
          {successMessage}
        </p>
      ) : null}

      {isLoadingOrders || isLoadingCustomers ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-600">
          Loading orders…
        </p>
      ) : orders.length === 0 ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
          <h2 className="text-xl font-bold text-slate-900">No orders found</h2>
          <p className="mt-2 text-slate-600">
            There are no orders in the selected group at the moment.
          </p>
        </section>
      ) : (
        <div className="space-y-5">
          {orders.map((order) => {
            const currentStage = ORDER_STAGES.findIndex(
              (stage) => stage.value === order.status,
            );
            const nextStatus = getNextStatus(order.status);
            const service = SERVICES_BY_CODE[order.service_type];
            const isUpdating = updatingOrderId === order.id;

            return (
              <article
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
                key={order.id}
              >
                <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-500">Ticket number</p>
                    <h2 className="mt-1 text-2xl font-bold text-slate-900">
                      {order.ticket_number}
                    </h2>
                    <p className="mt-1 text-slate-600">
                      {customerNames[order.customer_id] || `Customer ${order.customer_id}`}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {overdueOrderIds.includes(order.id) ? (
                      <span className="w-fit rounded-full bg-amber-100 px-4 py-2 text-sm font-bold text-amber-900">
                        Overdue
                      </span>
                    ) : null}
                    <span className="w-fit rounded-full bg-blue-100 px-4 py-2 text-sm font-bold text-[#005AAB]">
                      {getStatusLabel(order.status)}
                    </span>
                  </div>
                </div>

                <div className="my-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
                  <div>
                    <p className="text-sm text-slate-500">Service</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {service?.label || order.service_type}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Quantity</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {order.quantity} {service?.unit || "units"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Total price</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {formatKes(order.total_price)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Created</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {formatDateTime(order.created_at)}
                    </p>
                  </div>
                </div>

                <div className="mb-5 grid gap-2 sm:grid-cols-4" aria-label="Ticket progress">
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
                </div>

                {order.ready_at || order.collected_at ? (
                  <div className="mb-5 grid gap-3 rounded-xl bg-slate-50 p-4 text-sm sm:grid-cols-2">
                    {order.ready_at ? (
                      <p>
                        <span className="font-semibold text-slate-700">Ready since:</span>{" "}
                        {formatDateTime(order.ready_at)}
                      </p>
                    ) : null}
                    {order.collected_at ? (
                      <p>
                        <span className="font-semibold text-slate-700">Collected:</span>{" "}
                        {formatDateTime(order.collected_at)}
                      </p>
                    ) : null}
                  </div>
                ) : null}

                {nextStatus ? (
                  <button
                    className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
                    type="button"
                    disabled={updatingOrderId !== null}
                    onClick={() => updateStatus(order)}
                  >
                    {isUpdating ? "Updating…" : getActionLabel(order.status)}
                  </button>
                ) : (
                  <p className="font-semibold text-green-700">Order completed and collected.</p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
