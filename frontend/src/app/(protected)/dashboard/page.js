"use client";

import { getUserMessage } from "@/lib/user-messages";

import Link from "next/link";
import { useEffect, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";

// Turn the CSV text returned by FastAPI into a normal browser download.
function downloadCsvFile(csvText) {
  const csvBlob = new Blob([csvText], { type: "text/csv;charset=utf-8" });
  const downloadUrl = URL.createObjectURL(csvBlob);
  const downloadLink = document.createElement("a");

  downloadLink.href = downloadUrl;
  downloadLink.download = "qlms_orders_export.csv";
  document.body.appendChild(downloadLink);
  downloadLink.click();
  downloadLink.remove();
  URL.revokeObjectURL(downloadUrl);
}

function formatKes(amount) {
  return `KES ${Number(amount).toLocaleString("en-KE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function DashboardContent() {
  const { authenticatedRequest } = useAuth();

  // Store the status, overdue and payment values from the owner-only endpoint.
  const [summary, setSummary] = useState(null);

  // Keep page loading separate from CSV downloading so each action has clear feedback.
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState("");
  const [downloadMessage, setDownloadMessage] = useState("");

  // Load the current counts when the owner opens the dashboard.
  useEffect(() => {
    async function loadSummary() {
      try {
        const response = await authenticatedRequest("/dashboard/summary");
        setSummary(response);
      } catch (loadError) {
        setError(getUserMessage(loadError, "The dashboard summary could not be loaded."));
      } finally {
        setIsLoading(false);
      }
    }

    loadSummary();
  }, [authenticatedRequest]);

  // Ask FastAPI for the report, then save the returned CSV on the owner's device.
  async function handleCsvDownload() {
    setIsDownloading(true);
    setError("");
    setDownloadMessage("");

    try {
      const csvText = await authenticatedRequest("/dashboard/export");
      downloadCsvFile(csvText);
      setDownloadMessage("Order report downloaded as qlms_orders_export.csv.");
    } catch (downloadError) {
      setError(getUserMessage(downloadError, "The order report could not be downloaded."));
    } finally {
      setIsDownloading(false);
    }
  }

  // Overdue orders are already part of Ready, so only the four statuses form the total.
  const totalOrders = summary
    ? summary.received + summary.in_progress + summary.ready + summary.collected
    : 0;

  // Keep card labels beside their matching backend values for an easy-to-read layout.
  const summaryCards = summary
    ? [
        {
          label: "Total orders",
          value: totalOrders,
          description: "All order records",
        },
        {
          label: "Received",
          value: summary.received,
          description: "Waiting to be started",
        },
        {
          label: "In Progress",
          value: summary.in_progress,
          description: "Laundry work underway",
        },
        {
          label: "Ready for Collection",
          value: summary.ready,
          description: "Waiting for customers",
        },
        {
          label: "Collected",
          value: summary.collected,
          description: "Completed orders",
        },
        {
          label: "Overdue",
          value: summary.overdue,
          description: "Ready for more than 7 days",
          isWarning: true,
        },
      ]
    : [];

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
            Owner dashboard
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Laundry overview
          </h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">
            View the current order workload and download a full order report.
          </p>
        </div>

        <Link
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#005AAB] px-5 font-bold text-[#005AAB] no-underline hover:bg-blue-50"
          href="/orders/status"
        >
          Open status tracking
        </Link>
      </div>

      {error ? (
        <p
          className="mb-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {isLoading ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-600">
          Loading dashboard…
        </p>
      ) : summary ? (
        <>
          <section id="dashboard-attention-step" className="mb-6 rounded-2xl border-2 border-red-300 bg-red-50 p-5 shadow-sm sm:flex sm:items-center sm:justify-between sm:p-6">
            <div>
              <p className="text-sm font-bold uppercase tracking-wide text-red-800">
                Payments needing attention
              </p>
              <p className="mt-2 text-3xl font-bold text-slate-900">
                {formatKes(summary.outstanding_balance)}
              </p>
              <p className="mt-2 text-sm text-slate-700">
                {summary.unpaid}{" "}
                {summary.unpaid === 1 ? "order has" : "orders have"} a balance
                remaining.
              </p>
            </div>
            <Link
              className="mt-4 inline-flex min-h-11 items-center justify-center rounded-xl bg-red-700 px-5 font-bold text-white no-underline hover:bg-red-800 sm:mt-0"
              href="/orders/status?filter=outstanding"
            >
              View outstanding orders
            </Link>
          </section>

          <section
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            id="dashboard-summary-step"
            aria-label="Order summary"
          >
            {summaryCards.map((card) => (
              <article
                className={`rounded-2xl border p-6 shadow-sm ${
                  card.isWarning
                    ? "border-amber-300 bg-amber-50"
                    : "border-slate-200 bg-white"
                }`}
                key={card.label}
              >
                <p
                  className={`text-sm font-bold uppercase tracking-wide ${
                    card.isWarning ? "text-amber-900" : "text-slate-500"
                  }`}
                >
                  {card.label}
                </p>
                <p className="mt-3 text-4xl font-bold text-slate-900">
                  {card.value}
                </p>
                <p className="mt-2 text-sm text-slate-600">
                  {card.description}
                </p>
              </article>
            ))}
          </section>
        </>
      ) : null}

      <section id="dashboard-export-step" className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <h2 className="text-2xl font-bold text-slate-900">Order report</h2>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Download all orders as a CSV file for record keeping or opening in a
          spreadsheet program.
        </p>

        <button
          className="mt-5 inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
          type="button"
          disabled={isDownloading}
          onClick={handleCsvDownload}
        >
          {isDownloading ? "Preparing report…" : "Download order CSV"}
        </button>

        {downloadMessage ? (
          <p
            className="mt-5 rounded-xl border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800"
            role="status"
          >
            {downloadMessage}
          </p>
        ) : null}
      </section>
    </section>
  );
}

export default function DashboardPage() {
  return (
    <OwnerGuard>
      <DashboardContent />
    </OwnerGuard>
  );
}
