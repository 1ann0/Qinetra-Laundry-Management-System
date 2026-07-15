"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SERVICES, SERVICES_BY_CODE } from "@/constants/pricing";
import { useAuth } from "@/context/auth-context";

// Display prices in the same KES format throughout this screen.
function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

// Check the order values before sending them to the backend.
function getOrderError(customerId, serviceCode, quantity) {
  if (!customerId) {
    return "Select the customer for this order.";
  }

  if (!SERVICES_BY_CODE[serviceCode]) {
    return "Select a valid laundry service.";
  }

  if (!Number.isFinite(quantity) || quantity <= 0) {
    return "Enter a quantity greater than zero.";
  }

  if (serviceCode !== "wash_fold" && !Number.isInteger(quantity)) {
    return "Use a whole number for piece-based services.";
  }

  return "";
}

export default function OrderEntryPage() {
  const { authenticatedRequest } = useAuth();

  // Store the customer list and the two values used for the live price estimate.
  const [customers, setCustomers] = useState([]);
  const [serviceCode, setServiceCode] = useState(SERVICES[0].code);
  const [quantity, setQuantity] = useState("1");

  // Track loading, form errors and the ticket returned after a successful order.
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [createdOrder, setCreatedOrder] = useState(null);

  // Load customers once so staff can select one without typing a database ID.
  useEffect(() => {
    async function loadCustomers() {
      try {
        const response = await authenticatedRequest("/customers");
        setCustomers(response);
      } catch (loadError) {
        setError(loadError.message || "Customers could not be loaded.");
      } finally {
        setIsLoadingCustomers(false);
      }
    }

    loadCustomers();
  }, [authenticatedRequest]);

  // Calculate only a preview for the employee; FastAPI calculates the final total.
  const selectedService = SERVICES_BY_CODE[serviceCode];
  const numericQuantity = Number(quantity);
  const estimatedTotal =
    Number.isFinite(numericQuantity) && numericQuantity > 0
      ? selectedService.unitPrice * numericQuantity
      : 0;

  // Validate and create the order, then keep the returned ticket visible on screen.
  async function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const customerId = Number(formData.get("customer_id"));
    const orderQuantity = Number(quantity);
    const validationError = getOrderError(
      customerId,
      serviceCode,
      orderQuantity,
    );

    if (validationError) {
      setError(validationError);
      return;
    }

    const customer = customers.find((item) => item.id === customerId);
    setError("");
    setCreatedOrder(null);
    setIsSubmitting(true);

    try {
      // Send only the order inputs. Price and ticket generation belong to the backend.
      const response = await authenticatedRequest("/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          service_type: serviceCode,
          quantity: orderQuantity,
        }),
      });

      setCreatedOrder({
        ...response,
        customerName: customer?.name || `Customer ${customerId}`,
        serviceLabel: selectedService.label,
        unit: selectedService.unit,
      });

      form.reset();
      setServiceCode(SERVICES[0].code);
      setQuantity("1");
    } catch (orderError) {
      setError(orderError.message || "The order could not be created.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-5xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Order and pricing module
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Create a laundry order
        </h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Select the customer and laundry service. The backend will confirm the
          price and generate the ticket number.
        </p>
        <Link
          className="mt-4 inline-flex font-bold text-[#005AAB] no-underline hover:underline"
          href="/customers"
        >
          Register a customer first
        </Link>
        <span className="mx-3 text-slate-300">|</span>
        <Link
          className="mt-4 inline-flex font-bold text-[#005AAB] no-underline hover:underline"
          href="/orders/status"
        >
          Track order status
        </Link>
      </div>

      <form
        className="grid gap-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:grid-cols-[1fr_280px] lg:p-8"
        onSubmit={handleSubmit}
        noValidate
      >
        <div>
          <div className="mb-5">
            <label className="mb-2 block font-semibold text-slate-800" htmlFor="customer_id">
              Customer
            </label>
            <select
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="customer_id"
              name="customer_id"
              defaultValue=""
              disabled={isLoadingCustomers || isSubmitting}
            >
              <option value="">
                {isLoadingCustomers ? "Loading customers…" : "Select a customer"}
              </option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} — {customer.phone}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-5">
            <label className="mb-2 block font-semibold text-slate-800" htmlFor="service_type">
              Laundry service
            </label>
            <select
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="service_type"
              name="service_type"
              value={serviceCode}
              onChange={(event) => setServiceCode(event.target.value)}
              disabled={isSubmitting}
            >
              {SERVICES.map((service) => (
                <option key={service.code} value={service.code}>
                  {service.label} — {formatKes(service.unitPrice)} per {service.unit}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="mb-2 block font-semibold text-slate-800" htmlFor="quantity">
              Quantity ({selectedService.unit})
            </label>
            <input
              className="min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
              id="quantity"
              name="quantity"
              type="number"
              min={serviceCode === "wash_fold" ? "0.1" : "1"}
              step={serviceCode === "wash_fold" ? "0.1" : "1"}
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {error ? (
            <p
              className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              {error}
            </p>
          ) : null}

          <button
            className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
            type="submit"
            disabled={isSubmitting || isLoadingCustomers || customers.length === 0}
          >
            {isSubmitting ? "Creating order…" : "Create order"}
          </button>
        </div>

        <aside className="rounded-xl border border-blue-200 bg-blue-50 p-5">
          <p className="text-sm font-bold uppercase tracking-wide text-[#005AAB]">
            Price estimate
          </p>
          <p className="mt-3 text-3xl font-bold text-slate-900">
            {formatKes(estimatedTotal)}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {formatKes(selectedService.unitPrice)} per {selectedService.unit}. The
            backend confirms the final amount when the order is saved.
          </p>
        </aside>
      </form>

      {createdOrder ? (
        <section className="mt-8 rounded-2xl border border-green-300 bg-green-50 p-6 sm:p-8">
          <p className="text-sm font-bold uppercase tracking-wide text-green-800">
            Order created
          </p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Ticket {createdOrder.ticket_number}
          </h2>
          <dl className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-sm text-slate-600">Customer</dt>
              <dd className="mt-1 font-bold text-slate-900">{createdOrder.customerName}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Service</dt>
              <dd className="mt-1 font-bold text-slate-900">{createdOrder.serviceLabel}</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Quantity</dt>
              <dd className="mt-1 font-bold text-slate-900">
                {createdOrder.quantity} {createdOrder.unit}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Unit price</dt>
              <dd className="mt-1 font-bold text-slate-900">
                {formatKes(createdOrder.unit_price)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Final total</dt>
              <dd className="mt-1 font-bold text-slate-900">
                {formatKes(createdOrder.total_price)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-slate-600">Status</dt>
              <dd className="mt-1 font-bold capitalize text-slate-900">
                {createdOrder.status}
              </dd>
            </div>
          </dl>
        </section>
      ) : null}
    </section>
  );
}
