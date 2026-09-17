"use client";

import { useState } from "react";
import Link from "next/link";
import usePendingSave from "./use-pending-save";
import PendingSaveNotice from "./pending-save-notice";
import { getUserMessage } from "@/lib/user-messages";

export default function CustomerReassignment({ order, customers, onUpdated }) {
  const [search, setSearch] = useState("");
  const [newCustomerId, setNewCustomerId] = useState("");
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const save = usePendingSave(`/orders/${order.id}/customer-corrections`);
  const candidates = customers.filter((customer) =>
    customer.id !== order.customer_id &&
    `${customer.name} ${customer.phone} ${customer.id}`.toLowerCase().includes(search.toLowerCase().trim()),
  ).slice(0, 25);
  const selected = customers.find((customer) => customer.id === Number(newCustomerId));

  function finish(updatedOrder) {
    onUpdated(updatedOrder);
    setSearch("");
    setNewCustomerId("");
    setReason("");
    setConfirmed(false);
    setMessage("Ticket linked to the corrected customer. Check the name above and the history below.");
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!selected || !reason.trim() || !confirmed) {
      setError("Choose the correct customer, enter a reason and tick the confirmation box.");
      return;
    }
    try {
      finish(await save.save({
        expected_customer_id: order.customer_id,
        new_customer_id: selected.id,
        reason: reason.trim(), confirmed: true,
      }));
    } catch (saveError) {
      setError(getUserMessage(saveError, "QLMS could not confirm the customer correction. Use Retry previous save."));
    }
  }

  async function retry() {
    setError("");
    try {
      finish(await save.retry());
    } catch (saveError) {
      setError(getUserMessage(saveError));
    }
  }

  return (<>
    <PendingSaveNotice {...save} onRetry={retry} />
    <details className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-4">
      <summary className="cursor-pointer font-bold text-[#005AAB]">Owner: correct customer on this ticket</summary>
      <form className="mt-4 space-y-4" onSubmit={submit}>
        <p className="text-sm text-slate-700">Choose an existing customer. This moves this ticket and its payments to that person’s history. The original link stays in correction history. If a receipt was sent to the wrong person, contact them directly.</p>
        <fieldset disabled={save.isSaving || Boolean(save.pending) || !save.ready} className="space-y-4">
          <label className="block font-semibold text-slate-800">Find the correct customer
            <input className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" type="search" value={search} onChange={(event) => { setSearch(event.target.value); setNewCustomerId(""); }} placeholder="Name, phone or customer number" />
          </label>
          <label className="block font-semibold text-slate-800">Correct customer
            <select className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" value={newCustomerId} onChange={(event) => { setNewCustomerId(event.target.value); setConfirmed(false); }} required>
              <option value="">Select a customer</option>
              {candidates.map((customer) => <option key={customer.id} value={customer.id}>{customer.name} · {customer.phone} · #{customer.id}</option>)}
            </select>
          </label>
          <p className="text-sm text-slate-700">Can’t find the person? <Link className="font-bold text-[#005AAB] underline" href="/customers">Add customer</Link>, then return to this ticket.</p>
          <label className="block font-semibold text-slate-800">Reason
            <textarea className="mt-1 min-h-20 w-full rounded-lg border border-slate-400 bg-white p-3" maxLength={300} value={reason} onChange={(event) => setReason(event.target.value)} required />
          </label>
          <label className="flex items-start gap-2 font-semibold text-slate-800"><input className="mt-1" type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />I checked this is the right customer for this ticket.</label>
          <button className="min-h-11 rounded-lg bg-[#005AAB] px-5 font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB] disabled:opacity-60" type="submit">{save.isSaving ? "Saving…" : "Save customer correction"}</button>
        </fieldset>
      </form>
      {error ? <p role="alert" className="mt-3 text-sm font-semibold text-red-800">{error}</p> : null}
      {message ? <p role="status" className="mt-3 text-sm font-semibold text-green-800">{message}</p> : null}
    </details>
  </>);
}
