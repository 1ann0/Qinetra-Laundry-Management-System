"use client";

import { getUserMessage } from "@/lib/user-messages";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "received", label: "Received" },
  { value: "in_progress", label: "In Progress" },
  { value: "ready", label: "Ready for Collection" },
  { value: "collected", label: "Collected" },
];

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
  }).format(new Date(`${value}T00:00:00+03:00`));
}

function getStatusLabel(status) {
  return STATUS_OPTIONS.find((option) => option.value === status)?.label || status;
}

function getServiceSummary(order, services) {
  if ((order.service_lines || []).length > 0) {
    return order.service_lines.map((line) => line.service_name).join(", ");
  }

  return (
    services.find((service) => service.code === order.service_type)?.name ||
    order.service_type.replaceAll("_", " ")
  );
}

export default function CustomerSearchPage() {
  const { authenticatedRequest, role } = useAuth();
  const historySectionRef = useRef(null);

  const [customers, setCustomers] = useState([]);
  const [allCustomers, setAllCustomers] = useState([]);
  const [services, setServices] = useState([]);
  const [lastSearch, setLastSearch] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [serviceBrowseId, setServiceBrowseId] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [historyServiceId, setHistoryServiceId] = useState("");
  const [historyStatus, setHistoryStatus] = useState("");
  const [historyStartDate, setHistoryStartDate] = useState("");
  const [historyEndDate, setHistoryEndDate] = useState("");
  const [historyOrders, setHistoryOrders] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [hasLoadedHistory, setHasLoadedHistory] = useState(false);

  // Customer names and inactive services are still needed for old order history.
  useEffect(() => {
    async function loadReferenceData() {
      try {
        const [customerResponse, serviceResponse] = await Promise.all([
          authenticatedRequest("/customers"),
          authenticatedRequest("/catalog/services?include_inactive=true"),
        ]);
        setAllCustomers(customerResponse);
        setServices(serviceResponse);

        const requestedServiceId = new URLSearchParams(
          window.location.search,
        ).get("serviceId");
        const requestedService = serviceResponse.find(
          (service) => String(service.id) === requestedServiceId,
        );

        if (requestedService) {
          setServiceBrowseId(String(requestedService.id));
          setHistoryServiceId(String(requestedService.id));
          setIsHistoryLoading(true);
          setHasLoadedHistory(false);
          const orderResponse = await authenticatedRequest(
            `/orders?service_id=${requestedService.id}`,
          );
          setHistoryOrders(orderResponse);
          setHasLoadedHistory(true);
        }
      } catch (loadError) {
        setError(
          getUserMessage(loadError, "Customer and service history could not be loaded."),
        );
      } finally {
        setIsHistoryLoading(false);
      }
    }

    loadReferenceData();
  }, [authenticatedRequest]);

  async function handleSearch(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const search = String(formData.get("search") || "").trim();
    const path = search
      ? `/customers?search=${encodeURIComponent(search)}`
      : "/customers";

    setError("");
    setHasSearched(false);
    setIsLoading(true);

    try {
      const response = await authenticatedRequest(path);
      setCustomers(response);
      setLastSearch(search);
      setHasSearched(true);
    } catch (searchError) {
      setCustomers([]);
      setError(getUserMessage(searchError, "QLMS could not find customers."));
    } finally {
      setIsLoading(false);
    }
  }

  async function loadHistory({
    customer = selectedCustomer,
    serviceId = historyServiceId,
    status = historyStatus,
    startDate = historyStartDate,
    endDate = historyEndDate,
  } = {}) {
    if (!customer && !serviceId) {
      setHistoryError("Choose a customer or service first.");
      return;
    }
    if (startDate && endDate && endDate < startDate) {
      setHistoryError("End date cannot be before start date.");
      return;
    }

    const parameters = new URLSearchParams();
    if (customer) parameters.set("customer_id", String(customer.id));
    if (serviceId) parameters.set("service_id", String(serviceId));
    if (status) parameters.set("status", status);
    if (startDate) parameters.set("start_date", startDate);
    if (endDate) parameters.set("end_date", endDate);

    setHistoryError("");
    setIsHistoryLoading(true);
    setHasLoadedHistory(false);

    try {
      const response = await authenticatedRequest(
        `/orders?${parameters.toString()}`,
      );
      setHistoryOrders(response);
      setHasLoadedHistory(true);
    } catch (loadError) {
      setHistoryOrders([]);
      setHistoryError(getUserMessage(loadError, "Order history could not be loaded."));
    } finally {
      setIsHistoryLoading(false);
    }
  }

  async function viewCustomerHistory(customer) {
    setSelectedCustomer(customer);
    setHistoryServiceId("");
    setHistoryStatus("");
    setHistoryStartDate("");
    setHistoryEndDate("");
    await loadHistory({
      customer,
      serviceId: "",
      status: "",
      startDate: "",
      endDate: "",
    });
    window.setTimeout(() => {
      historySectionRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 0);
  }

  async function handleServiceHistory(event) {
    event.preventDefault();
    if (!serviceBrowseId) {
      setHistoryError("Choose a service first.");
      return;
    }

    setSelectedCustomer(null);
    setHistoryServiceId(serviceBrowseId);
    setHistoryStatus("");
    setHistoryStartDate("");
    setHistoryEndDate("");
    await loadHistory({
      customer: null,
      serviceId: serviceBrowseId,
      status: "",
      startDate: "",
      endDate: "",
    });
    window.setTimeout(() => {
      historySectionRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 0);
  }

  function closeHistory() {
    setSelectedCustomer(null);
    setHistoryServiceId("");
    setHistoryStatus("");
    setHistoryStartDate("");
    setHistoryEndDate("");
    setHistoryOrders([]);
    setHistoryError("");
    setHasLoadedHistory(false);
  }

  const customerById = Object.fromEntries(
    allCustomers.map((customer) => [customer.id, customer]),
  );
  const selectedService = services.find(
    (service) => String(service.id) === historyServiceId,
  );
  const historyIsOpen = Boolean(selectedCustomer || historyServiceId);
  const historyTitle = selectedCustomer
    ? `Order history for ${selectedCustomer.name}`
    : selectedService
      ? `${selectedService.name} order history`
      : "Order history";

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Customers
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Find customer
        </h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Search customers by name or phone, review everything they brought to
          Qinetra, or find customers who used a particular service.
        </p>
        <Link
          className="mt-4 inline-flex items-center gap-2 font-bold text-[#005AAB] no-underline hover:underline"
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
          Add customer
        </Link>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <form
          className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          onSubmit={handleSearch}
        >
          <label className="mb-2 block text-lg font-bold text-slate-800" htmlFor="search">
            Customer name or phone
          </label>
          <p className="mb-4 text-sm text-slate-600">
            Leave this blank to see every customer.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              className="min-h-12 flex-1 rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="search"
              name="search"
              type="search"
              maxLength={100}
              autoFocus
              disabled={isLoading}
              placeholder="Example: Jane or 0712"
            />
            <button
              className="inline-flex min-h-12 items-center justify-center rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? "Searching…" : "Search customers"}
            </button>
          </div>
        </form>

        <form
          className="rounded-2xl border border-blue-200 bg-blue-50/50 p-6 shadow-sm"
          onSubmit={handleServiceHistory}
        >
          <label
            className="mb-2 block text-lg font-bold text-slate-800"
            htmlFor="service-history"
          >
            Find orders by service
          </label>
          <p className="mb-4 text-sm text-slate-600">
            See who ordered a particular laundry service.
          </p>
          <select
            className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
            id="service-history"
            value={serviceBrowseId}
            onChange={(event) => setServiceBrowseId(event.target.value)}
          >
            <option value="">Choose a service</option>
            {services.map((service) => (
              <option key={service.id} value={service.id}>
                {service.name}{service.is_active ? "" : " (Inactive)"}
              </option>
            ))}
          </select>
          <button
            className="mt-3 min-h-12 w-full rounded-xl border border-[#005AAB] bg-white px-5 font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-60"
            type="submit"
            disabled={!serviceBrowseId || isHistoryLoading}
          >
            View service history
          </button>
        </form>
      </div>

      {error ? (
        <p
          className="mt-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {hasSearched ? (
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <h2 className="text-xl font-bold text-slate-900">
              {lastSearch ? `Results for “${lastSearch}”` : "All customers"}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {customers.length} {customers.length === 1 ? "record" : "records"} found
            </p>
          </div>

          {customers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead className="bg-slate-50 text-sm text-slate-600">
                  <tr>
                    <th className="px-6 py-3 font-semibold" scope="col">
                      Customer name
                    </th>
                    <th className="px-6 py-3 font-semibold" scope="col">
                      Phone number
                    </th>
                    <th className="px-6 py-3 font-semibold" scope="col">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {customers.map((customer) => (
                    <tr className="text-slate-800" key={customer.id}>
                      <td className="px-6 py-4 font-semibold">{customer.name}</td>
                      <td className="whitespace-nowrap px-6 py-4">{customer.phone}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-2">
                          <button
                            className="inline-flex min-h-10 items-center justify-center rounded-lg bg-[#005AAB] px-4 font-bold text-white hover:bg-[#004782]"
                            type="button"
                            onClick={() => viewCustomerHistory(customer)}
                          >
                            View history
                          </button>
                          <Link
                            className="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#005AAB] px-4 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
                            href={`/orders?customerId=${customer.id}`}
                          >
                            Create order
                          </Link>
                          {role === "owner" ? <Link
                            className="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#005AAB] px-4 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
                            href={`/customers/${customer.id}`}
                          >Contact details</Link> : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-6 py-10 text-center text-slate-600">
              No customers matched this search.
            </p>
          )}
        </div>
      ) : null}

      {historyIsOpen ? (
        <section
          className="mt-8 scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
          ref={historySectionRef}
        >
          <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-bold uppercase tracking-wide text-[#005AAB]">
                Saved order records
              </p>
              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                {historyTitle}
              </h2>
              {selectedCustomer ? (
                <p className="mt-1 text-slate-600">{selectedCustomer.phone}</p>
              ) : null}
            </div>
            <button
              className="min-h-10 rounded-lg border border-slate-300 px-4 font-bold text-slate-700 hover:bg-slate-50"
              type="button"
              onClick={closeHistory}
            >
              Close history
            </button>
          </div>

          <form
            className="my-5 grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2 lg:grid-cols-4"
            onSubmit={(event) => {
              event.preventDefault();
              loadHistory();
            }}
          >
            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700" htmlFor="history-service">
                Service
              </label>
              <select
                className="min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-900"
                id="history-service"
                value={historyServiceId}
                onChange={(event) => setHistoryServiceId(event.target.value)}
              >
                {selectedCustomer ? <option value="">All services</option> : null}
                {!selectedCustomer && !historyServiceId ? (
                  <option value="">Choose a service</option>
                ) : null}
                {services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name}{service.is_active ? "" : " (Inactive)"}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700" htmlFor="history-status">
                Status
              </label>
              <select
                className="min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-900"
                id="history-status"
                value={historyStatus}
                onChange={(event) => setHistoryStatus(event.target.value)}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700" htmlFor="history-start-date">
                From date
              </label>
              <input
                className="min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-900"
                id="history-start-date"
                type="date"
                value={historyStartDate}
                onChange={(event) => setHistoryStartDate(event.target.value)}
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700" htmlFor="history-end-date">
                To date
              </label>
              <input
                className="min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-slate-900"
                id="history-end-date"
                type="date"
                value={historyEndDate}
                onChange={(event) => setHistoryEndDate(event.target.value)}
              />
            </div>
            <button
              className="min-h-11 rounded-lg bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:opacity-60 sm:col-span-2 lg:col-span-4 lg:justify-self-end"
              type="submit"
              disabled={isHistoryLoading}
            >
              {isHistoryLoading ? "Loading…" : "Apply history filters"}
            </button>
          </form>

          {historyError ? (
            <p
              className="mb-5 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              {historyError}
            </p>
          ) : null}

          {isHistoryLoading ? (
            <p className="py-10 text-center text-slate-600">Loading order history…</p>
          ) : hasLoadedHistory && historyOrders.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 px-5 py-10 text-center text-slate-600">
              No orders match these history filters.
            </p>
          ) : hasLoadedHistory ? (
            <div>
              <p className="mb-4 text-sm font-bold text-slate-700">
                {historyOrders.length} {historyOrders.length === 1 ? "order" : "orders"} found
              </p>
              <div className="space-y-3">
                {historyOrders.map((order) => {
                  const customer = customerById[order.customer_id];
                  return (
                    <article
                      className="grid gap-4 rounded-xl border border-slate-200 p-4 md:grid-cols-[1.1fr_1fr_1.4fr_0.8fr_auto] md:items-center"
                      key={order.id}
                    >
                      <div>
                        <p className="break-words font-bold text-[#005AAB]">
                          {order.ticket_number}
                        </p>
                        <p className="mt-1 break-words text-sm font-semibold text-slate-800">
                          {customer?.name || `Customer ${order.customer_id}`}
                        </p>
                        {customer?.phone ? (
                          <p className="mt-1 text-sm text-slate-500">{customer.phone}</p>
                        ) : null}
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Order date
                        </p>
                        <p className="mt-1 font-semibold text-slate-800">
                          {formatDate(order.order_date)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Service
                        </p>
                        <p className="mt-1 break-words font-semibold text-slate-800">
                          {getServiceSummary(order, services)}
                        </p>
                      </div>
                      <div>
                        <span className="inline-flex rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-[#005AAB]">
                          {getStatusLabel(order.status)}
                        </span>
                        <p className="mt-2 font-bold text-slate-900">
                          {formatKes(order.net_charge)}
                        </p>
                      </div>
                      <Link
                        className="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#005AAB] px-4 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
                        href={`/orders/${order.id}`}
                      >
                        Open order
                      </Link>
                    </article>
                  );
                })}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}
    </section>
  );
}
