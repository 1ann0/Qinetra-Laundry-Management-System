"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";
import { getUserMessage } from "@/lib/user-messages";
import { formatNairobiDateTime } from "@/lib/format-nairobi";
import { REPORT_TYPES, ATTENTION_LABELS, SUMMARY_LABELS, nairobiToday, reportQuery, formatKes, saveReportFile } from "@/lib/report-tools";

const INPUT = "min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-base text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100";
const STATUS = { received: "Received", in_progress: "In progress", ready: "Ready for collection", collected: "Collected", cancelled: "Cancelled" };

function SearchChoice({ label, choices, value, onChange, required }) {
  const [search, setSearch] = useState("");
  const selected = choices.find(choice => String(choice.id) === value);
  const matching = choices.filter(choice => `${choice.name} ${choice.phone || choice.code || ""}`.toLowerCase().includes(search.trim().toLowerCase()));
  const visible = matching.slice(0, 50);
  if (selected && !visible.some(choice => choice.id === selected.id)) visible.unshift(selected);
  return <div>
    <label className="mb-2 block font-bold text-slate-800" htmlFor={`find-${label}`}>Find {label.toLowerCase()}</label>
    <input className={INPUT} id={`find-${label}`} type="search" value={search} placeholder={label === "Customer" ? "Name or phone" : "Service name or code"} onChange={event => setSearch(event.target.value)} />
    <label className="mb-2 mt-3 block text-sm font-bold text-slate-700" htmlFor={`choose-${label}`}>{required ? `Choose one ${label.toLowerCase()}` : `${label} filter`}</label>
    <select className={INPUT} id={`choose-${label}`} value={value} required={required} onChange={event => onChange(event.target.value)}>
      <option value="">{required ? `Select ${label.toLowerCase()}` : `All ${label.toLowerCase()}s`}</option>
      {visible.map(choice => <option key={choice.id} value={choice.id}>{choice.name}{choice.phone ? ` · ${choice.phone}` : ""}{choice.is_active === false ? " (inactive)" : ""}</option>)}
    </select>
    {matching.length > 50 ? <p className="mt-2 text-sm text-slate-600">Showing 50 matches. Type more to find a specific {label.toLowerCase()}.</p> : null}
    {!matching.length && search ? <p className="mt-2 text-sm text-slate-600">No matches. Try another name{label === "Customer" ? " or phone" : ""}.</p> : null}
  </div>;
}

function ReportValue({ row, column }) {
  const value = row[column.key];
  let text = column.type === "money" ? formatKes(value) : column.key === "status" ? STATUS[value] || value : value;
  if (column.key === "attention") text = String(value || "").split(", ").map(flag => ATTENTION_LABELS[flag] || flag).join(", ");
  if (["method", "purpose"].includes(column.key)) text = { cash: "Cash", mpesa: "M-Pesa", service_refund: "Service refund", excess_payment: "Excess payment" }[value] || value;
  return column.key === "ticket" && row.order_id ? <Link className="inline-flex min-h-12 items-center font-bold text-[#005AAB] underline" href={`/orders/receipt?id=${row.order_id}`}>{text}</Link> : String(text ?? "");
}

const MOBILE_FIELDS = {
  orders: ["ticket", "customer_name", "status", "balance_due"], balances: ["ticket", "customer_name", "balance_due", "refund_due"],
  related_orders: ["ticket", "customer_name", "status", "balance_due"], attention: ["ticket", "customer_name", "attention", "balance_due"],
  receipts: ["ticket", "date", "method", "amount"], refunds: ["ticket", "date", "method", "amount"], corrections: ["ticket", "date", "amount", "purpose"],
  service_lines: ["ticket", "service", "quantity", "unit", "booked_value"], services: ["name", "unit", "price", "active"], clothing: ["name", "group", "active"],
};

function ReportSection({ section }) {
  const [page, setPage] = useState(0);
  const pageSize = 25;
  const rows = section.rows.slice(page * pageSize, (page + 1) * pageSize);
  const mainFields = MOBILE_FIELDS[section.key] || section.columns.slice(0, 4).map(column => column.key);
  const primaryColumns = section.columns.filter(column => mainFields.includes(column.key));
  const extraColumns = section.columns.filter(column => !mainFields.includes(column.key));
  return <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
    <h3 className="text-lg font-bold text-slate-900">{section.title}</h3>
    <p className="mb-3 mt-1 text-sm text-slate-600">{section.rows.length} records. Downloads include every matching record.</p>
    {!section.rows.length ? <p className="rounded-xl bg-slate-50 p-4 text-slate-600">No matching activity or balances.</p> : <>
      <ul className="space-y-3 sm:hidden" aria-label={`${section.title} records`}>{rows.map((row, index) => <li className="rounded-xl border border-slate-200 p-4" key={index}>
        <dl className="space-y-3">{primaryColumns.map(column => <div key={column.key}><dt className="text-sm text-slate-600">{column.label}</dt><dd className="break-words font-semibold text-slate-900"><ReportValue row={row} column={column} /></dd></div>)}</dl>
        {extraColumns.length ? <details className="mt-3 border-t border-slate-200"><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">More details</summary><dl className="space-y-3">{extraColumns.map(column => <div key={column.key}><dt className="text-sm text-slate-600">{column.label}</dt><dd className="break-words text-slate-800"><ReportValue row={row} column={column} /></dd></div>)}</dl></details> : null}
      </li>)}</ul>
      <div className="hidden overflow-x-auto rounded-lg border border-slate-200 sm:block" tabIndex={0} role="region" aria-label={`${section.title} table; scroll sideways for more columns`}>
        <table className="w-full text-left text-sm"><thead className="bg-slate-50"><tr>{section.columns.map(column => <th scope="col" className="whitespace-nowrap px-4 py-3 font-bold text-slate-700" key={column.key}>{column.label}</th>)}</tr></thead>
          <tbody>{rows.map((row, index) => <tr className="border-t border-slate-200" key={index}>{section.columns.map(column => <td className="min-w-28 px-4 py-3 align-top text-slate-700" key={column.key}><ReportValue row={row} column={column} /></td>)}</tr>)}</tbody>
        </table>
      </div>
      {section.rows.length > pageSize ? <div className="mt-3 flex items-center gap-3">
        <button className="secondary-button" type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
        <span className="text-sm text-slate-600" aria-live="polite">Page {page + 1} of {Math.ceil(section.rows.length / pageSize)}</span>
        <button className="secondary-button" type="button" disabled={(page + 1) * pageSize >= section.rows.length} onClick={() => setPage(page + 1)}>Next</button>
      </div> : null}
    </>}
  </section>;
}

function ReportsContent() {
  const { authenticatedRequest } = useAuth();
  const today = nairobiToday();
  const [kind, setKind] = useState("orders");
  const [filters, setFilters] = useState({ start_date: `${today.slice(0, 8)}01`, end_date: today });
  const [customers, setCustomers] = useState([]);
  const [services, setServices] = useState([]);
  const [report, setReport] = useState(null);
  const [loadedQuery, setLoadedQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const requestRef = useRef(null);
  const displayedRef = useRef("");
  const type = REPORT_TYPES.find(type => type.value === kind);
  const query = `${kind}?${reportQuery(kind, filters)}`;
  const changed = report && query !== loadedQuery;

  const loadReport = useCallback(async (reportKind, values) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true); setError(""); setMessage("");
    try {
      const selectedQuery = `${reportKind}?${reportQuery(reportKind, values)}`;
      const response = await authenticatedRequest(`/dashboard/reports/${selectedQuery}`, { cache: "no-store", signal: controller.signal });
      if (requestRef.current !== controller) return;
      setReport(response); setLoadedQuery(selectedQuery); displayedRef.current = selectedQuery;
    } catch (loadError) {
      if (!controller.signal.aborted) setError(getUserMessage(loadError, "The report could not be loaded."));
    } finally {
      if (requestRef.current === controller) setLoading(false);
    }
  }, [authenticatedRequest]);

  useEffect(() => {
    const controller = new AbortController();
    async function initialize() {
      try {
        const [customerRecords, serviceRecords] = await Promise.all([
          authenticatedRequest("/customers", { signal: controller.signal }),
          authenticatedRequest("/catalog/services?include_inactive=true", { signal: controller.signal }),
        ]);
        if (controller.signal.aborted) return;
        setCustomers(customerRecords); setServices(serviceRecords);
        const parameters = new URLSearchParams(window.location.search);
        const selectedKind = REPORT_TYPES.some(type => type.value === parameters.get("report")) ? parameters.get("report") : "orders";
        const date = nairobiToday();
        const values = { start_date: `${date.slice(0, 8)}01`, end_date: date };
        for (const field of REPORT_TYPES.find(type => type.value === selectedKind).filters) if (parameters.has(field)) values[field] = parameters.get(field);
        setKind(selectedKind); setFilters(values);
        if ((selectedKind === "customer" && !values.customer_id) || (selectedKind === "service" && !values.service_id)) setLoading(false);
        else await loadReport(selectedKind, values);
      } catch (loadError) {
        if (!controller.signal.aborted) { setLoading(false); setError(getUserMessage(loadError, "Report choices could not be loaded.")); }
      }
    }
    void initialize();
    return () => { controller.abort(); requestRef.current?.abort(); };
  }, [authenticatedRequest, loadReport]);

  function update(field, value) { setFilters(current => ({ ...current, [field]: value })); }
  async function download(format) {
    setDownloading(format); setError(""); setMessage("");
    const selectedQuery = loadedQuery;
    const [selectedKind, filterQuery] = selectedQuery.split("?");
    try {
      const response = await authenticatedRequest(`/dashboard/reports/${selectedKind}/download?${filterQuery}&format=${format}`, { responseType: "blob", cache: "no-store" });
      if (displayedRef.current !== selectedQuery) { setMessage("The displayed report changed. Download the current report again."); return; }
      saveReportFile(response);
      setMessage(`Download started: ${response.filename}. On your phone, open Files → Downloads, then choose Excel or a spreadsheet app.`);
    } catch (downloadError) { setError(getUserMessage(downloadError, "The report could not be downloaded.")); }
    finally { setDownloading(""); }
  }

  return <section className="mx-auto max-w-6xl">
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p className="text-sm font-bold uppercase tracking-widest text-[#005AAB]">Owner records</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Reports and downloads</h1><p className="mt-2 text-slate-600">Find the records you need, check them, then save an Excel or CSV copy.</p></div><Link className="secondary-button" href="/dashboard">Dashboard</Link></div>
    {error ? <p className="mb-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-800" role="alert">{error}</p> : null}
    <form id="reports-filters-step" className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6" onSubmit={event => { event.preventDefault(); void loadReport(kind, filters); }}>
      <label className="mb-2 block font-bold text-slate-800" htmlFor="report-type">What do you want to see?</label>
      <select className={INPUT} id="report-type" value={kind} onChange={event => { setKind(event.target.value); setMessage(""); }}>
        {REPORT_TYPES.map(type => <option key={type.value} value={type.value}>{type.label}</option>)}
      </select>
      <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {type.filters.includes("start_date") ? <div><label className="mb-2 block font-bold text-slate-800" htmlFor="report-start">From date</label><input className={INPUT} id="report-start" type="date" value={filters.start_date || ""} onChange={event => update("start_date", event.target.value)} /></div> : null}
        {type.filters.includes("end_date") ? <div><label className="mb-2 block font-bold text-slate-800" htmlFor="report-end">To date</label><input className={INPUT} id="report-end" type="date" min={filters.start_date || undefined} value={filters.end_date || ""} onChange={event => update("end_date", event.target.value)} /></div> : null}
        {type.filters.includes("customer_id") ? <SearchChoice label="Customer" choices={customers} value={filters.customer_id || ""} required={kind === "customer"} onChange={value => update("customer_id", value)} /> : null}
        {type.filters.includes("service_id") ? <SearchChoice label="Service" choices={services} value={filters.service_id || ""} required={kind === "service"} onChange={value => update("service_id", value)} /> : null}
        {type.filters.includes("status") ? <div><label className="mb-2 block font-bold text-slate-800" htmlFor="report-status">Current order stage</label><select className={INPUT} id="report-status" value={filters.status || ""} onChange={event => update("status", event.target.value)}><option value="">All stages</option>{Object.entries(STATUS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></div> : null}
        {type.filters.includes("payment_method") ? <div><label className="mb-2 block font-bold text-slate-800" htmlFor="report-method">Payment method</label><select className={INPUT} id="report-method" value={filters.payment_method || ""} onChange={event => update("payment_method", event.target.value)}><option value="">Cash and M-Pesa</option><option value="cash">Cash</option><option value="mpesa">M-Pesa</option></select></div> : null}
        {type.filters.includes("attention") ? <div><label className="mb-2 block font-bold text-slate-800" htmlFor="report-attention">What needs attention?</label><select className={INPUT} id="report-attention" value={filters.attention || ""} onChange={event => update("attention", event.target.value)}><option value="">Everything needing attention</option>{Object.entries(ATTENTION_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></div> : null}
      </div>
      <button className="primary-button mt-5 min-h-12" disabled={loading} type="submit">{loading ? "Preparing report…" : "View report"}</button>
      {kind === "attention" ? <p className="mt-3 text-sm text-slate-600">Attention shows the shop now. It is not a historical date report.</p> : null}
    </form>
    {message ? <p className="mt-4 break-words rounded-xl border border-green-300 bg-green-50 p-4 text-green-900" role="status">{message}</p> : null}
    {report ? <div id="reports-preview-step" className="mt-6" aria-busy={loading}>
      <div id="reports-download-step" className="rounded-2xl border border-blue-200 bg-blue-50 p-4 sm:p-6">
        <h2 className="text-xl font-bold text-slate-900">Displayed report: {REPORT_TYPES.find(type => type.value === report.report)?.label}</h2>
        <p className="mt-2 text-sm text-slate-700">Generated {formatNairobiDateTime(report.generated_at)}. {Object.entries(report.filters).map(([key, value]) => `${key.replaceAll("_", " ")}: ${value}`).join(" · ") || "All applicable records"}</p>
        {changed ? <p className="mt-3 font-semibold text-amber-900" role="status">Filters changed. Select View report before downloading.</p> : null}
        <div className="mt-4 flex flex-wrap gap-3"><button className="primary-button min-h-12" type="button" disabled={Boolean(downloading) || loading || changed} onClick={() => download("xlsx")}>{downloading === "xlsx" ? "Preparing Excel…" : "Download Excel (.xlsx)"}</button><button className="secondary-button min-h-12" type="button" disabled={Boolean(downloading) || loading || changed} onClick={() => download("csv")}>{downloading === "csv" ? "Preparing CSV…" : "Download CSV"}</button></div>
        <p className="mt-3 text-sm text-slate-600">Downloads use exactly these displayed filters. Editing a file does not change QLMS.</p>
      </div>
      {Object.keys(report.summary).length ? <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{Object.entries(report.summary).map(([key, value]) => <div className="rounded-xl border border-slate-200 bg-white p-4" key={key}><dt className="text-sm text-slate-600">{ATTENTION_LABELS[key] || SUMMARY_LABELS[key] || key.replaceAll("_", " ")}</dt><dd className="mt-1 text-xl font-bold text-slate-900">{report.report === "attention" || key.startsWith("quantity_") ? Number(value).toLocaleString("en-KE") : formatKes(value)}</dd></div>)}</dl> : null}
      {report.sections.map(section => <ReportSection key={`${loadedQuery}:${report.generated_at}:${section.key}`} section={section} />)}
      <details className="mt-5 rounded-xl border border-slate-200 bg-white p-4"><summary className="cursor-pointer font-bold text-slate-800">How to read these figures</summary><ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">{report.definitions.map(definition => <li key={definition}>{definition}</li>)}</ul></details>
    </div> : loading ? <p className="mt-5 text-slate-600" role="status">Loading report choices…</p> : <p className="mt-5 rounded-xl bg-slate-50 p-4 text-slate-600">Choose a customer or service where required, then select View report.</p>}
  </section>;
}

export default function ReportsPage() { return <OwnerGuard><ReportsContent /></OwnerGuard>; }
