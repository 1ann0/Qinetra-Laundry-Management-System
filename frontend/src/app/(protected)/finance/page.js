"use client";

import { getUserMessage } from "@/lib/user-messages";
import Link from "next/link";

import { useCallback, useEffect, useMemo, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";

const NAIROBI_DATE_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Africa/Nairobi",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

function getNairobiToday() {
  const dateParts = Object.fromEntries(
    NAIROBI_DATE_FORMATTER.formatToParts(new Date())
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );

  return `${dateParts.year}-${dateParts.month}-${dateParts.day}`;
}

function changeDate(dateValue, numberOfDays) {
  const [year, month, day] = dateValue.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + numberOfDays);
  return date.toISOString().slice(0, 10);
}

function getWeekStart(dateValue) {
  const [year, month, day] = dateValue.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const daysSinceMonday = (date.getUTCDay() + 6) % 7;
  return changeDate(dateValue, -daysSinceMonday);
}

function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function formatCompactKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    notation: "compact",
    maximumFractionDigits: 1,
  })}`;
}

function formatDate(dateValue) {
  return new Date(`${dateValue}T00:00:00Z`).toLocaleDateString("en-KE", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function formatQuantity(amount) {
  return Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

function formatServiceUnit(unit, quantity) {
  if (unit === "item") {
    return Number(quantity) === 1 ? "item" : "items";
  }
  return unit;
}

function DailyIncomeChart({ dailyReceived }) {
  const [activeIndex, setActiveIndex] = useState(null);
  const chartWidth = 900;
  const chartHeight = 320;
  const leftPadding = 90;
  const rightPadding = 30;
  const topPadding = 35;
  const bottomPadding = 55;
  const plotWidth = chartWidth - leftPadding - rightPadding;
  const plotHeight = chartHeight - topPadding - bottomPadding;
  const highestAmount = Math.max(
    ...dailyReceived.map((point) => Number(point.amount)),
    1,
  );

  const chartPoints = dailyReceived.map((point, index) => {
    const x =
      dailyReceived.length === 1
        ? leftPadding + plotWidth / 2
        : leftPadding + (index / (dailyReceived.length - 1)) * plotWidth;
    const y =
      topPadding + (1 - Number(point.amount) / highestAmount) * plotHeight;
    return { ...point, x, y };
  });
  const activePoint =
    activeIndex === null ? null : chartPoints[activeIndex];
  const xLabelIndexes = [
    0,
    Math.floor((dailyReceived.length - 1) / 2),
    dailyReceived.length - 1,
  ].filter((value, index, values) => values.indexOf(value) === index);

  const tooltipWidth = 190;
  const tooltipX = activePoint
    ? Math.min(
        Math.max(activePoint.x - tooltipWidth / 2, 5),
        chartWidth - tooltipWidth - 5,
      )
    : 0;
  const tooltipY = activePoint ? Math.max(activePoint.y - 78, 5) : 0;

  return (
    <div className="mt-5 overflow-x-auto">
      <svg
        className="min-w-[680px]"
        role="img"
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        aria-labelledby="daily-income-title daily-income-description"
      >
        <title id="daily-income-title">Daily payments received</title>
        <desc id="daily-income-description">
          A line graph of confirmed Cash and M-PESA payments for every day in
          the selected period. Focus or hover on a point for its exact value.
        </desc>

        {[0, 0.5, 1].map((position) => {
          const y = topPadding + position * plotHeight;
          const amount = highestAmount * (1 - position);
          return (
            <g key={position}>
              <line
                x1={leftPadding}
                x2={chartWidth - rightPadding}
                y1={y}
                y2={y}
                stroke="#cbd5e1"
                strokeDasharray="5 6"
              />
              <text
                x={leftPadding - 12}
                y={y + 4}
                fill="#64748b"
                fontSize="12"
                textAnchor="end"
              >
                {formatCompactKes(amount)}
              </text>
            </g>
          );
        })}

        {chartPoints.length > 1 ? (
          <polyline
            fill="none"
            points={chartPoints.map((point) => `${point.x},${point.y}`).join(" ")}
            stroke="#005AAB"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="4"
          />
        ) : null}

        {chartPoints.map((point, index) => (
          <circle
            aria-label={`${formatDate(point.date)}: ${formatKes(point.amount)}`}
            className="cursor-pointer outline-none focus:stroke-[#00B7F1] focus:stroke-[5px]"
            cx={point.x}
            cy={point.y}
            fill="#ffffff"
            key={point.date}
            r={activeIndex === index ? 7 : 5}
            role="button"
            stroke="#005AAB"
            strokeWidth="3"
            tabIndex={0}
            onBlur={() => setActiveIndex(null)}
            onFocus={() => setActiveIndex(index)}
            onMouseEnter={() => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(null)}
          />
        ))}

        {xLabelIndexes.map((index) => (
          <text
            fill="#64748b"
            fontSize="12"
            key={chartPoints[index].date}
            textAnchor="middle"
            x={chartPoints[index].x}
            y={chartHeight - 18}
          >
            {formatDate(chartPoints[index].date)}
          </text>
        ))}

        {activePoint ? (
          <g pointerEvents="none">
            <line
              x1={activePoint.x}
              x2={activePoint.x}
              y1={activePoint.y}
              y2={topPadding + plotHeight}
              stroke="#00B7F1"
              strokeDasharray="4 4"
              strokeWidth="2"
            />
            <rect
              fill="#0f172a"
              height="58"
              rx="10"
              width={tooltipWidth}
              x={tooltipX}
              y={tooltipY}
            />
            <text
              fill="#cbd5e1"
              fontSize="12"
              x={tooltipX + 12}
              y={tooltipY + 21}
            >
              {formatDate(activePoint.date)}
            </text>
            <text
              fill="#ffffff"
              fontSize="15"
              fontWeight="700"
              x={tooltipX + 12}
              y={tooltipY + 44}
            >
              {formatKes(activePoint.amount)}
            </text>
          </g>
        ) : null}
      </svg>
    </div>
  );
}

function TopServicesChart({ services }) {
  const visibleServices = services.slice(0, 5);
  const highestBookedValue = Math.max(
    ...visibleServices.map((service) => Number(service.booked_value)),
    1,
  );

  return (
    <div className="mt-6 space-y-5">
      {visibleServices.map((service) => {
        const barWidth = Math.max(
          (Number(service.booked_value) / highestBookedValue) * 100,
          3,
        );

        return (
          <article
            key={`${service.service_id || service.service_name}-${service.service_unit}`}
          >
            <div className="flex flex-wrap items-end justify-between gap-2">
              <div>
                <h3 className="font-bold text-slate-900">
                  {service.service_name}
                </h3>
                <p className="mt-1 text-sm text-slate-600">
                  {service.order_count}{" "}
                  {service.order_count === 1 ? "order" : "orders"} ·{" "}
                  {formatQuantity(service.quantity_booked)}{" "}
                  {formatServiceUnit(
                    service.service_unit,
                    service.quantity_booked,
                  )}
                </p>
              </div>
              <p className="font-bold text-[#005AAB]">
                {formatKes(service.booked_value)}
              </p>
            </div>
            <div
              aria-label={`${service.service_name}: ${formatKes(service.booked_value)} booked`}
              aria-valuemax={highestBookedValue}
              aria-valuemin={0}
              aria-valuenow={Number(service.booked_value)}
              className="mt-2 h-3 overflow-hidden rounded-full bg-slate-100"
              role="progressbar"
            >
              <div
                className="h-full rounded-full bg-[#005AAB]"
                style={{ width: `${barWidth}%` }}
              />
            </div>
          </article>
        );
      })}
    </div>
  );
}

function FinancialSnapshotContent() {
  const { authenticatedRequest } = useAuth();
  const today = getNairobiToday();
  const lastThirtyDaysStart = changeDate(today, -29);
  const [startDate, setStartDate] = useState(lastThirtyDaysStart);
  const [endDate, setEndDate] = useState(today);
  const [activePreset, setActivePreset] = useState("last_30_days");
  const [customerSort, setCustomerSort] = useState("highest");
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const requestSummary = useCallback(
    async (rangeStart, rangeEnd) => {
      const query = new URLSearchParams({
        start_date: rangeStart,
        end_date: rangeEnd,
      });
      return authenticatedRequest(
        `/dashboard/financial-summary?${query.toString()}`,
      );
    },
    [authenticatedRequest],
  );

  const loadSummary = useCallback(
    async (rangeStart, rangeEnd) => {
      setIsLoading(true);
      setError("");

      try {
        const response = await requestSummary(rangeStart, rangeEnd);
        setSummary(response);
      } catch (loadError) {
        setError(
          getUserMessage(loadError, "The financial summary could not be loaded."),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [requestSummary],
  );

  useEffect(() => {
    let isCurrentRequest = true;

    async function loadInitialSummary() {
      try {
        const response = await requestSummary(lastThirtyDaysStart, today);
        if (isCurrentRequest) {
          setSummary(response);
        }
      } catch (loadError) {
        if (isCurrentRequest) {
          setError(
            getUserMessage(loadError, "The financial summary could not be loaded."),
          );
        }
      } finally {
        if (isCurrentRequest) {
          setIsLoading(false);
        }
      }
    }

    loadInitialSummary();
    return () => {
      isCurrentRequest = false;
    };
  }, [lastThirtyDaysStart, requestSummary, today]);

  const sortedCustomerRevenue = useMemo(() => {
    const customers = [...(summary?.customer_revenue || [])];

    if (customerSort === "lowest") {
      return customers.sort(
        (first, second) => first.total_received - second.total_received,
      );
    }
    if (customerSort === "name") {
      return customers.sort((first, second) =>
        first.customer_name.localeCompare(second.customer_name),
      );
    }
    return customers.sort(
      (first, second) => second.total_received - first.total_received,
    );
  }, [customerSort, summary]);

  const serviceInsights = useMemo(() => {
    const services = summary?.top_services || [];
    const mostSelected = [...services].sort(
      (first, second) =>
        second.order_count - first.order_count ||
        second.booked_value - first.booked_value ||
        first.service_name.localeCompare(second.service_name),
    )[0];

    return {
      topByValue: services[0] || null,
      mostSelected: mostSelected || null,
    };
  }, [summary]);

  function applyPreset(preset) {
    const nextStart =
      preset === "today"
        ? today
        : preset === "week"
          ? getWeekStart(today)
          : preset === "month"
            ? `${today.slice(0, 7)}-01`
            : changeDate(today, -29);

    setStartDate(nextStart);
    setEndDate(today);
    setActivePreset(preset);
    loadSummary(nextStart, today);
  }

  function applyCustomRange(event) {
    event.preventDefault();

    if (!startDate || !endDate) {
      setError("Choose both a start date and an end date.");
      return;
    }
    if (endDate < startDate) {
      setError("End date cannot be before start date.");
      return;
    }

    setActivePreset("custom");
    loadSummary(startDate, endDate);
  }

  const presetButtons = [
    { value: "last_30_days", label: "Last 30 days" },
    { value: "today", label: "Today" },
    { value: "week", label: "This week" },
    { value: "month", label: "This month" },
  ];

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-6">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Owner finance
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Financial overview
        </h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">
          See the work booked, money received and customer contribution for the
          selected period.
        </p>
        <div className="mt-4 flex flex-wrap gap-3"><Link className="secondary-button" href="/daily-close">Close the day</Link><Link className="secondary-button" href="/expenses">Record an expense</Link><Link className="secondary-button" href="/reports?report=expenses">Expense history and downloads</Link></div>
      </div>

      {error ? (
        <p
          className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {!summary && isLoading ? (
        <p
          className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-600"
          role="status"
        >
          Loading financial overview…
        </p>
      ) : summary ? (
        <section id="finance-figures-step" aria-label="Financial figures">
          <p className="mb-3 text-sm font-semibold text-slate-600">
            {formatDate(summary.start_date)} to {formatDate(summary.end_date)}
          </p>
          <div className="grid gap-4 lg:grid-cols-3">
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-wide text-slate-500">
                Orders booked
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-900">
                {summary.orders_booked}
              </p>
              {summary.cancelled_orders > 0 ? (
                <p className="mt-2 text-sm text-slate-600">
                  {summary.cancelled_orders} cancelled ticket{summary.cancelled_orders === 1 ? "" : "s"} excluded from order value.
                </p>
              ) : null}
              <p className="mt-4 text-sm text-slate-600">Order value before refunds</p>
              <p className="mt-1 text-xl font-bold text-[#005AAB]">
                  {formatKes(summary.order_value)}
              </p>
              <p className="mt-3 text-sm text-slate-700">Current net charge: <strong>{formatKes(summary.net_charge)}</strong></p>
              <p className="mt-1 text-sm text-slate-600">Service refunds: {formatKes(summary.service_refunds)}. Applies to orders booked in this period, including later refunds.</p>
              <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-slate-200 pt-4 text-sm">
                <div>
                  <dt className="text-slate-600">Before discounts</dt>
                  <dd className="mt-1 font-bold text-slate-900">
                    {formatKes(summary.gross_order_value)}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-600">Discounts given</dt>
                  <dd className="mt-1 font-bold text-amber-900">
                    {formatKes(summary.discounts_given)}
                  </dd>
                </div>
              </dl>
            </article>

            <article className="rounded-2xl border-2 border-[#005AAB] bg-blue-50 p-6 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-wide text-[#005AAB]">
                Payments received
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-900">
                {formatKes(summary.total_received)}
              </p>
              <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-slate-600">Cash</dt>
                  <dd className="mt-1 font-bold text-slate-900">
                    {formatKes(summary.cash_received)}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-600">M-PESA</dt>
                  <dd className="mt-1 font-bold text-slate-900">
                    {formatKes(summary.mpesa_received)}
                  </dd>
                </div>
              </dl>
              <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-blue-200 pt-4 text-sm">
                <div><dt className="text-slate-600">Refunds sent</dt><dd className="mt-1 font-bold text-slate-900">{formatKes(summary.refunds_sent)}</dd></div>
                <div><dt className="text-slate-600">After refunds</dt><dd className="mt-1 font-bold text-slate-900">{formatKes(summary.net_cash_movement)}</dd></div>
              </dl>
            </article>

            <article className="rounded-2xl border border-amber-300 bg-amber-50 p-6 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-wide text-amber-900">
                Current outstanding
              </p>
              <p className="mt-3 text-4xl font-bold text-slate-900">
                {formatKes(summary.outstanding_balance)}
              </p>
              <p className="mt-4 text-sm text-slate-700">
                {summary.outstanding_orders}{" "}
                {summary.outstanding_orders === 1 ? "order has" : "orders have"}{" "}
                a balance remaining.
              </p>
              <p className="mt-3 text-sm font-semibold text-amber-900">Refunds still due to these customers: {formatKes(summary.refund_due)}</p>
            </article>
          </div>
        </section>
      ) : null}

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <h2 id="finance-period-step" className="text-xl font-bold text-slate-900">Choose a period</h2>

        <div className="mt-4 flex flex-wrap gap-3" aria-label="Quick date ranges">
          {presetButtons.map((preset) => (
            <button
              className={`min-h-11 rounded-xl border px-5 font-bold ${
                activePreset === preset.value
                  ? "border-[#005AAB] bg-[#005AAB] text-white"
                  : "border-slate-300 bg-white text-slate-700 hover:border-[#005AAB] hover:text-[#005AAB]"
              }`}
              disabled={isLoading}
              key={preset.value}
              type="button"
              onClick={() => applyPreset(preset.value)}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <form
          className="mt-6 grid gap-4 border-t border-slate-200 pt-5 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
          onSubmit={applyCustomRange}
        >
          <label className="font-semibold text-slate-700" htmlFor="finance_start_date">
            Start date
            <input
              className="mt-2 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal text-slate-900 focus:border-[#005AAB] focus:outline-none focus:ring-2 focus:ring-blue-100"
              id="finance_start_date"
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) => {
                setStartDate(event.target.value);
                setActivePreset("custom");
              }}
            />
          </label>

          <label className="font-semibold text-slate-700" htmlFor="finance_end_date">
            End date
            <input
              className="mt-2 min-h-11 w-full rounded-xl border border-slate-300 px-3 font-normal text-slate-900 focus:border-[#005AAB] focus:outline-none focus:ring-2 focus:ring-blue-100"
              id="finance_end_date"
              type="date"
              value={endDate}
              min={startDate || undefined}
              max={today}
              onChange={(event) => {
                setEndDate(event.target.value);
                setActivePreset("custom");
              }}
            />
          </label>

          <button
            className="min-h-11 rounded-xl bg-slate-800 px-5 font-bold text-white hover:bg-slate-900 disabled:cursor-wait disabled:opacity-60"
            type="submit"
            disabled={isLoading}
          >
            Apply dates
          </button>
        </form>

        {isLoading && summary ? (
          <p className="mt-4 text-sm font-semibold text-[#005AAB]" role="status">
            Updating figures…
          </p>
        ) : null}
      </section>

      {summary ? (
        <>
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-2xl font-bold text-slate-900">
              Daily payments received
            </h2>
            <p className="mt-2 text-slate-600">
              Cash and M-PESA combined. Hover over or focus a point to see the
              exact date and amount.
            </p>
            <DailyIncomeChart dailyReceived={summary.daily_received} />
          </section>

          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h2 className="text-2xl font-bold text-slate-900">
              Top services by order value
            </h2>
            <p className="mt-2 max-w-3xl text-slate-600">
              Services booked on the selected order dates, after service-line
              discounts. These figures are work booked, not payments allocated
              to each service.
            </p>

            {summary.top_services?.length > 0 ? (
              <>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <article className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                    <p className="text-sm font-bold uppercase tracking-wide text-[#005AAB]">
                      Highest booked value
                    </p>
                    <p className="mt-2 text-lg font-bold text-slate-900">
                      {serviceInsights.topByValue.service_name}
                    </p>
                    <p className="mt-1 text-slate-700">
                      {formatKes(serviceInsights.topByValue.booked_value)}
                    </p>
                  </article>
                  <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-bold uppercase tracking-wide text-slate-600">
                      Most frequently selected
                    </p>
                    <p className="mt-2 text-lg font-bold text-slate-900">
                      {serviceInsights.mostSelected.service_name}
                    </p>
                    <p className="mt-1 text-slate-700">
                      {serviceInsights.mostSelected.order_count}{" "}
                      {serviceInsights.mostSelected.order_count === 1
                        ? "order"
                        : "orders"}
                    </p>
                  </article>
                </div>
                <TopServicesChart services={summary.top_services} />
              </>
            ) : (
              <p className="mt-5 rounded-xl bg-slate-50 px-4 py-5 text-slate-600">
                No service was booked during this period.
              </p>
            )}
          </section>

          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Payments by customer
                </h2>
                <p className="mt-2 max-w-2xl text-slate-600">
                  Confirmed payments received from each customer during this
                  period, after entry corrections. Refunds are shown separately above.
                </p>
              </div>

              <label className="font-semibold text-slate-700" htmlFor="customer_revenue_sort">
                Sort customers
                <select
                  className="mt-2 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 font-normal text-slate-900 focus:border-[#005AAB] focus:outline-none focus:ring-2 focus:ring-blue-100"
                  id="customer_revenue_sort"
                  value={customerSort}
                  onChange={(event) => setCustomerSort(event.target.value)}
                >
                  <option value="highest">Highest payments first</option>
                  <option value="lowest">Lowest payments first</option>
                  <option value="name">Customer name A–Z</option>
                </select>
              </label>
            </div>

            {sortedCustomerRevenue.length > 0 ? (
              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[620px] border-collapse text-left">
                  <thead>
                    <tr className="border-b-2 border-slate-200 text-sm uppercase tracking-wide text-slate-500">
                      <th className="px-3 py-3">Customer</th>
                      <th className="px-3 py-3">Phone</th>
                      <th className="px-3 py-3 text-right">Payments received</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedCustomerRevenue.map((customer) => (
                      <tr className="border-b border-slate-100" key={customer.customer_id}>
                        <td className="px-3 py-4 font-bold text-slate-900">
                          {customer.customer_name}
                        </td>
                        <td className="px-3 py-4 text-slate-600">
                          {customer.customer_phone}
                        </td>
                        <td className="px-3 py-4 text-right font-bold text-[#005AAB]">
                          {formatKes(customer.total_received)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-5 rounded-xl bg-slate-50 px-4 py-5 text-slate-600">
                No Cash or M-PESA payment was recorded during this period.
              </p>
            )}
          </section>

          <section id="finance-definitions-step" className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm leading-6 text-slate-700">
            <h2 className="font-bold text-slate-900">How these figures work</h2>
            <p className="mt-2">
              Final order value uses order dates and includes discounts.
              Payments received uses the date the shop actually received the
              money, so it can include payment for an older order. Outstanding
              shows today’s remaining balance on orders booked in this period.
            </p>
          </section>
        </>
      ) : null}
    </section>
  );
}

export default function FinancialSnapshotPage() {
  return (
    <OwnerGuard>
      <FinancialSnapshotContent />
    </OwnerGuard>
  );
}
