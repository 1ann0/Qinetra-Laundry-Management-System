"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { searchWorkspace } from "@/lib/workspace-search";
import { getUserMessage } from "@/lib/user-messages";

const linkClass = "flex min-h-11 flex-col justify-center rounded-lg px-3 py-2 font-bold text-[#005AAB] no-underline hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2";

export default function QuickFind() {
  const { authenticatedRequest } = useAuth();
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const requestNumber = useRef(0);
  useEffect(() => () => { requestNumber.current++; }, []);

  async function find(event) {
    event.preventDefault();
    const query = String(new FormData(event.currentTarget).get("query") || "");
    const number = ++requestNumber.current;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const response = await searchWorkspace(authenticatedRequest, query);
      if (number === requestNumber.current) setResult(response);
    } catch (failure) {
      if (number === requestNumber.current) setError(getUserMessage(failure));
    } finally {
      if (number === requestNumber.current) setBusy(false);
    }
  }

  const groups = result ? [
    {key: "customers", title: "Customers", all: `/customers/search?search=${encodeURIComponent(result.query)}`,
      label: item => item.name, detail: item => item.phone, href: item => `/customers/search?customerId=${item.id}`},
    {key: "orders", title: "Orders", all: `/orders/status?search=${encodeURIComponent(result.query)}`,
      label: item => item.ticket_number, detail: () => "Open order and receipt", href: item => `/orders/receipt?id=${item.id}`},
    {key: "services", title: "Services", label: item => item.name,
      detail: item => item.is_active ? "View order history" : "Inactive · View order history",
      href: item => `/customers/search?serviceId=${item.id}`},
  ] : [];

  return <section id="quick-find" className="mt-5 scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6" aria-labelledby="quick-find-heading">
    <h2 id="quick-find-heading" className="text-xl font-bold text-slate-900">Find in QLMS</h2>
    <p id="quick-find-help" className="mt-2 text-sm leading-6 text-slate-600">Search for a customer, phone number, ticket or laundry service.</p>
    <form onSubmit={find} className="mt-4 flex flex-col gap-3 sm:flex-row" role="search">
      <label className="min-w-0 flex-1 font-semibold text-slate-800">What are you looking for?
        <input name="query" type="search" maxLength={100} required aria-describedby="quick-find-help" className="mt-2 min-h-12 w-full rounded-xl border border-slate-400 bg-white px-3 font-normal focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB]" placeholder="Name, phone, ticket or service" />
      </label>
      <button type="submit" disabled={busy} aria-busy={busy} className="min-h-12 rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:opacity-60 sm:self-end">{busy ? "Searching…" : "Search QLMS"}</button>
    </form>
    {busy ? <p className="mt-3 text-sm text-slate-600" role="status">Looking for matching customers, orders and services…</p> : null}
    {error ? <p className="mt-3 text-red-800" role="alert">{error}</p> : null}
    {result ? <>
      <p className="mt-5 text-sm font-semibold text-slate-700" role="status">Results for “{result.query}”</p>
      <div className="mt-3 grid gap-4 lg:grid-cols-3">
        {groups.map(group => {
          const section = result[group.key];
          const items = section.status === "fulfilled" ? section.value : null;
          const shown = items && group.all ? items.slice(0, 6) : items;
          return <section key={group.key} className="min-w-0 rounded-xl border border-slate-200 p-3" aria-labelledby={`find-${group.key}`}>
            <h3 id={`find-${group.key}`} className="text-lg font-bold text-slate-900">{group.title}</h3>
            {items ? <>
              <p className="mt-1 text-sm text-slate-600">{items.length === 0 ? "No matches. Try another name, number or service." : `${items.length} match${items.length === 1 ? "" : "es"}${shown.length < items.length ? ` · Showing first ${shown.length}` : ""}`}</p>
              <ul className="mt-2 space-y-1">
                {shown.map(item => <li key={item.id}><Link className={linkClass} href={group.href(item)}>
                  <span className="break-words">{group.label(item)}</span><span className="text-sm font-normal text-slate-600">{group.detail(item)}</span>
                </Link></li>)}
              </ul>
              {group.all && items.length > 0 ? <Link href={group.all} className={linkClass}>View all {group.title.toLowerCase()} matches</Link> : null}
            </> : <p className="mt-2 text-sm text-red-800" role="alert">{getUserMessage(section.reason, `${group.title} could not be searched. Try again.`)}</p>}
          </section>;
        })}
      </div>
    </> : null}
  </section>;
}
