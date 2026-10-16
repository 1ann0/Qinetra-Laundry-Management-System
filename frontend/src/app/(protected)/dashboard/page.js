"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";
import { getUserMessage } from "@/lib/user-messages";
import { formatNairobiDateTime } from "@/lib/format-nairobi";
import { ATTENTION_LABELS, SUMMARY_LABELS, dashboardWork, formatKes, nairobiToday, reportQuery } from "@/lib/report-tools";
import { differenceFromKes } from "@/lib/daily-close-tools";

const WORK_QUEUES = ["due_today", "production_late", "ready", "overdue", "holds", "outsourcing"];
const INPUT = "min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-base text-slate-900 focus:border-[#005AAB] focus:outline-none focus:ring-4 focus:ring-blue-100";

function DashboardContent() {
  const { authenticatedRequest } = useAuth();
  const [period, setPeriod] = useState(() => ({ start_date: nairobiToday(), end_date: nairobiToday() }));
  const [displayedPeriod, setDisplayedPeriod] = useState(null);
  const [work, setWork] = useState(null);
  const [money, setMoney] = useState(null);
  const [expenses, setExpenses] = useState(null);
  const [expensesPeriod, setExpensesPeriod] = useState(null);
  const [expensesError, setExpensesError] = useState("");
  const [closing, setClosing] = useState(null);
  const [closingError, setClosingError] = useState("");
  const [loading, setLoading] = useState(true);
  const [workError, setWorkError] = useState("");
  const [moneyError, setMoneyError] = useState("");
  const requestRef = useRef(null);

  const requestDashboard = useCallback((dates, signal) => Promise.allSettled([
    authenticatedRequest("/dashboard/reports/attention", { signal, cache: "no-store" }),
    authenticatedRequest(`/dashboard/reports/money?${reportQuery("money", dates)}`, { signal, cache: "no-store" }),
    authenticatedRequest(`/dashboard/reports/expenses?${reportQuery("expenses", dates)}`, { signal, cache: "no-store" }),
    authenticatedRequest(`/daily-close?date=${nairobiToday()}`, { signal, cache: "no-store" }),
  ]), [authenticatedRequest]);

  const applyResults = useCallback((results, dates) => {
    // Current work and period money remain separate, including when one refresh fails.
    if (results[0].status === "fulfilled") setWork(results[0].value);
    else setWorkError(getUserMessage(results[0].reason, "Current work could not be refreshed."));
    if (results[1].status === "fulfilled") { setMoney(results[1].value); setDisplayedPeriod({ ...dates }); }
    else setMoneyError(getUserMessage(results[1].reason, "Money figures could not be refreshed."));
    if (results[2].status === "fulfilled") { setExpenses(results[2].value); setExpensesPeriod({ ...dates }); }
    else setExpensesError(getUserMessage(results[2].reason, "Expense figures could not be refreshed."));
    if (results[3].status === "fulfilled") setClosing(results[3].value);
    else setClosingError(getUserMessage(results[3].reason, "The daily money check could not be refreshed."));
    setLoading(false);
  }, []);

  const loadDashboard = useCallback(async (dates) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    const results = await requestDashboard(dates, controller.signal);
    if (!controller.signal.aborted && requestRef.current === controller) applyResults(results, dates);
  }, [requestDashboard, applyResults]);

  function refreshDashboard() {
    if (period.start_date && period.end_date && period.end_date < period.start_date) {
      setMoneyError("Choose an end date on or after the start date."); return;
    }
    setLoading(true); setWorkError(""); setMoneyError(""); setExpensesError(""); setClosingError("");
    void loadDashboard(period);
  }

  useEffect(() => {
    const today = nairobiToday();
    const dates = { start_date: today, end_date: today };
    const controller = new AbortController();
    requestRef.current = controller;
    void requestDashboard(dates, controller.signal).then(results => {
      if (!controller.signal.aborted && requestRef.current === controller) applyResults(results, dates);
    });
    return () => controller.abort();
  }, [requestDashboard, applyResults]);

  const current = dashboardWork(work);
  const periodChanged = displayedPeriod && (period.start_date !== displayedPeriod.start_date || period.end_date !== displayedPeriod.end_date);
  const todayLabel = new Intl.DateTimeFormat("en-KE", { dateStyle: "full", timeZone: "Africa/Nairobi" }).format(new Date());

  return <section className="mx-auto max-w-6xl">
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-sm font-bold uppercase tracking-widest text-[#005AAB]">Owner dashboard</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Today at Qinetra</h1><p className="mt-2 text-slate-600">{todayLabel} · Nairobi</p></div>
      <div className="flex flex-wrap gap-3"><Link className="secondary-button min-h-12" href="/orders">New order</Link><Link className="secondary-button min-h-12" href="/reports">Reports</Link><button className="secondary-button min-h-12" type="button" disabled={loading} onClick={refreshDashboard}>{loading ? "Refreshing…" : "Refresh dashboard"}</button></div>
    </header>
    <section id="dashboard-returns-step" className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6"><h2 className="text-xl font-bold text-slate-900">Customer returns</h2><p className="mt-2 text-slate-600">See who is new and who has not visited recently.</p><Link className="secondary-button mt-4 min-h-12" href="/reports?report=returns">View customer returns</Link></section>
    <section id="dashboard-attention-step" aria-busy={loading}>
      <div className="mb-4"><h2 className="text-xl font-bold text-slate-900">What needs attention?</h2><p className="mt-1 text-sm text-slate-600">{work ? `Current work as of ${formatNairobiDateTime(work.generated_at)}. Choose a list to open its tickets.` : "Loading the shop's current work…"}</p></div>
      {workError ? <p className="mb-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-800" role="alert">{workError} {work ? "The last successful snapshot is still shown below." : ""}</p> : null}
      {work ? <>
        <div id="dashboard-summary-step" className="grid grid-cols-2 gap-3 lg:grid-cols-3">
          {WORK_QUEUES.map(queue => <Link key={queue} href={`/reports?report=attention&attention=${queue}`} className={`rounded-xl border p-4 no-underline transition-colors motion-reduce:transition-none hover:border-[#005AAB] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB] ${work.summary[queue] && ["production_late", "overdue", "outsourcing"].includes(queue) ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-white"}`}><p className="min-h-12 text-sm font-semibold text-slate-700">{ATTENTION_LABELS[queue]}</p><p className="mt-2 text-3xl font-bold text-slate-900">{work.summary[queue] || 0}</p><p className="mt-2 text-sm font-semibold text-[#005AAB]">View tickets →</p></Link>)}
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Link className="rounded-xl border border-blue-200 bg-blue-50 p-5 no-underline" href="/reports?report=attention&attention=outstanding"><p className="font-semibold text-slate-700">Money currently owed to the shop</p><p className="mt-2 text-2xl font-bold text-slate-900">{formatKes(current.totalOwed)}</p><p className="mt-2 text-sm text-[#005AAB]">{work.summary.outstanding || 0} tickets · View balances →</p></Link>
          <Link className="rounded-xl border border-slate-200 bg-white p-5 no-underline" href="/reports?report=attention&attention=refund_due"><p className="font-semibold text-slate-700">Money currently owed back</p><p className="mt-2 text-2xl font-bold text-slate-900">{formatKes(current.totalRefundDue)}</p><p className="mt-2 text-sm text-[#005AAB]">{work.summary.refund_due || 0} tickets · Review returns →</p></Link>
        </div>
        <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4"><h3 className="font-bold text-slate-900">Tickets to check first</h3><Link className="secondary-button" href="/reports?report=attention">View all {current.rows.length}</Link></div>
          {current.rows.length ? <ul className="divide-y divide-slate-200">{current.rows.slice(0, 5).map(row => <li key={row.order_id} className="flex flex-wrap items-start justify-between gap-3 p-4"><div className="min-w-0"><Link className="inline-flex min-h-12 items-center font-bold text-[#005AAB] underline" href={`/orders/receipt?id=${row.order_id}`}>{row.ticket}</Link><p className="break-words text-slate-800">{row.customer_name}</p><p className="mt-1 text-sm text-slate-600">{String(row.attention).split(", ").map(flag => ATTENTION_LABELS[flag] || flag).join(" · ")}</p></div><Link className="secondary-button" href={`/customers/search?customerId=${row.customer_id}`}>Customer history</Link></li>)}</ul> : <p className="p-5 text-slate-600">No tickets need attention right now. Saved work will appear here when it needs action.</p>}
        </div>
      </> : null}
    </section>
    <section id="dashboard-close-step" className="mt-7 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6" aria-busy={loading}>
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-bold">Daily money check</h2><p className="mt-1 text-sm text-slate-600">Count cash and compare M-Pesa statement totals. This is a manual Owner check, not profit.</p></div><Link className="secondary-button" href={`/daily-close?date=${closing?.date || nairobiToday()}`}>Close the day</Link></div>
      {closingError ? <p role="alert" className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-800">{closingError} {closing ? "The last loaded day remains below; reload before relying on its review state." : ""}</p> : null}
      {closing ? <div className="mt-4 space-y-2"><p className="text-sm text-slate-600">Displayed day: {closing.date} · Nairobi</p><p className="font-bold">{!closing.latest ? "No Owner confirmation yet" : closing.needs_review ? "Needs review — records changed after confirmation" : "Owner confirmation saved"}</p>{closing.latest ? <><p>Signed cash result: <strong>{differenceFromKes(closing.latest.snapshot.figures.cash_difference)}</strong></p><p className="text-sm text-slate-600">{closing.latest.confirmed_by_username} · {formatNairobiDateTime(closing.latest.created_at)}. Later activity never rewrites the signed snapshot.</p></> : <p>Open Close the day when the shop is ready to count its money.</p>}</div> : <p role="status" className="mt-4 text-slate-600">{loading ? "Loading the daily check…" : "Daily check unavailable. Refresh to try again."}</p>}
    </section>
    <section id="dashboard-money-step" className="mt-7 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6" aria-busy={loading}>
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-bold text-slate-900">Money received and returned</h2><p className="mt-1 text-sm text-slate-600">These are recorded payments. Profit also needs the shop&apos;s costs.</p></div><Link className="secondary-button" href="/finance">Open Finance</Link></div>
      <form className="mt-5 grid items-end gap-4 sm:grid-cols-3" onSubmit={event => { event.preventDefault(); refreshDashboard(); }}>
        <div><label className="mb-2 block font-bold text-slate-700" htmlFor="dashboard-from">From date</label><input className={INPUT} id="dashboard-from" type="date" value={period.start_date} required onChange={event => setPeriod({ ...period, start_date: event.target.value })} /></div>
        <div><label className="mb-2 block font-bold text-slate-700" htmlFor="dashboard-to">To date</label><input className={INPUT} id="dashboard-to" type="date" min={period.start_date} value={period.end_date} required onChange={event => setPeriod({ ...period, end_date: event.target.value })} /></div>
        <button className="primary-button min-h-12" disabled={loading} type="submit">{loading ? "Updating…" : "Apply dates"}</button>
      </form>
      {moneyError ? <p className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-800" role="alert">{moneyError} {money ? "The last successful snapshot is still shown below." : ""}</p> : null}
      {money ? <>
        <p className="mt-5 text-sm text-slate-600">Displayed period: {displayedPeriod.start_date} to {displayedPeriod.end_date} · Nairobi. Updated {formatNairobiDateTime(money.generated_at)}.</p>
        {periodChanged ? <p className="mt-2 font-semibold text-amber-900" role="status">Dates changed. Select Apply dates to update the figures.</p> : null}
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{Object.entries(money.summary).map(([key, value]) => <div className="rounded-xl bg-slate-50 p-4" key={key}><dt className="text-sm font-semibold text-slate-600">{SUMMARY_LABELS[key] || key}</dt><dd className="mt-2 text-xl font-bold text-slate-900">{formatKes(value)}</dd></div>)}</dl>
        {!money.sections.some(section => section.rows.length) ? <p className="mt-4 text-slate-600">No payment or return activity in this period.</p> : null}
        <div id="dashboard-export-step" className="mt-5"><Link className="secondary-button min-h-12" href={`/reports?report=money&${reportQuery("money", displayedPeriod)}`}>View this report and download Excel or CSV</Link></div>
      </> : <p className="mt-5 text-slate-600">{loading ? "Loading money figures…" : "Money figures are unavailable. Refresh to try again."}</p>}
    </section>
    <section id="dashboard-expenses-step" className="mt-7 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6" aria-busy={loading}>
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-bold text-slate-900">Shop expenses</h2><p className="mt-1 text-sm text-slate-600">Money paid for running the shop, using corrected paid dates. Reversed entries are excluded. These totals do not establish profit.</p></div><Link className="secondary-button" href="/expenses">Record an expense</Link></div>
      {expensesError ? <p className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-800" role="alert">{expensesError} {expenses ? "The last successful expense snapshot remains below." : ""}</p> : null}
      {expenses ? <><p className="mt-5 text-sm text-slate-600">Displayed expense period: {expensesPeriod.start_date} to {expensesPeriod.end_date} · Nairobi. Updated {formatNairobiDateTime(expenses.generated_at)}.</p>
        {period.start_date !== expensesPeriod.start_date || period.end_date !== expensesPeriod.end_date ? <p className="mt-2 font-semibold text-amber-900" role="status">Select Apply dates above to update expenses.</p> : null}
        <dl className="mt-4 grid gap-3 sm:grid-cols-3">{Object.entries(expenses.summary).map(([key, value]) => <div className="rounded-xl bg-slate-50 p-4" key={key}><dt className="text-sm font-semibold text-slate-600">{SUMMARY_LABELS[key]}</dt><dd className="mt-2 text-xl font-bold text-slate-900">{formatKes(value)}</dd></div>)}</dl>
        {!expenses.sections[0].rows.length ? <p className="mt-4 text-slate-600">No expenses recorded in this period.</p> : null}
        <Link className="secondary-button mt-5" href={`/reports?report=expenses&${reportQuery("expenses", expensesPeriod)}`}>Expense history and downloads</Link>
      </> : <p className="mt-5 text-slate-600">{loading ? "Loading expenses…" : "Expenses are unavailable. Refresh to try again."}</p>}
    </section>
  </section>;
}

export default function DashboardPage() { return <OwnerGuard><DashboardContent /></OwnerGuard>; }
