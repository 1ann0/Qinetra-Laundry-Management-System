"use client";

// Contact changes keep the same customer and orders; history explains each edit.
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { readRecordId } from "@/lib/record-id";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";
import usePendingSave from "@/components/orders/use-pending-save";
import PendingSaveNotice from "@/components/orders/pending-save-notice";
import { getUserMessage } from "@/lib/user-messages";

const inputClass = "mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3";
const buttonClass = "min-h-11 rounded-lg bg-[#005AAB] px-5 font-bold text-white disabled:opacity-60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB]";

function ContactDetails({ customerId }) {
  const { authenticatedRequest } = useAuth();
  const path = `/customers/${customerId}`;
  const save = usePendingSave(`${path}/corrections`);
  const [customer, setCustomer] = useState(null);
  const [history, setHistory] = useState([]);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [sharedPhone, setSharedPhone] = useState(false);
  const [matches, setMatches] = useState([]);
  const [stale, setStale] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const [details, corrections] = await Promise.all([
          authenticatedRequest(path), authenticatedRequest(`${path}/corrections`),
        ]);
        if (ignore) return;
        setCustomer(details);
        setName(details.name);
        setPhone(details.phone);
        setHistory(corrections);
        setStale(false);
        setConfirmed(false);
        setSharedPhone(false);
        setMatches([]);
        setReason("");
      } catch (loadError) {
        if (!ignore) setError(getUserMessage(loadError));
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
    return () => { ignore = true; };
  }, [authenticatedRequest, path, reload]);

  function reloadDetails() {
    setLoading(true);
    setError("");
    setMessage("");
    setReload((value) => value + 1);
  }

  function editDetails(setter, value) {
    setter(value);
    setConfirmed(false);
    setSharedPhone(false);
    setMatches([]);
    setError("");
    setMessage("");
  }

  async function submit(event, retry = false) {
    event?.preventDefault();
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      const updated = retry ? await save.retry() : await save.save({
        expected_name: customer.name, expected_phone: customer.phone,
        new_name: name, new_phone: phone, reason,
        allow_shared_phone: sharedPhone, confirmed,
      });
      setCustomer(updated);
      setName(updated.name);
      setPhone(updated.phone);
      setReason("");
      setConfirmed(false);
      setSharedPhone(false);
      setMatches([]);
      setStale(false);
      setMessage("Contact details saved. This customer's orders remain linked to the same record.");
    } catch (saveError) {
      setError(getUserMessage(saveError));
      if (saveError.code === "QLMS-STALE-RECORD") setStale(true);
      if (saveError.code === "QLMS-PHONE-SHARED") {
        try {
          const found = await authenticatedRequest(`/customers/phone-match?phone=${encodeURIComponent(phone)}`);
          setMatches(found.filter((match) => match.id !== customer.id));
        } catch (matchError) {
          setError(getUserMessage(matchError, "Matching customers could not be loaded."));
        }
      }
      setSubmitting(false);
      return;
    }
    // A history-read failure must never turn an accepted correction into a new save.
    try {
      setHistory(await authenticatedRequest(`${path}/corrections`));
    } catch (historyError) {
      setHistory([]);
      setError(getUserMessage(historyError, "Saved, but history could not be loaded. Reload saved details."));
    }
    setSubmitting(false);
  }

  return <section className="mx-auto max-w-3xl space-y-5">
    <Link className="font-bold text-[#005AAB] underline" href="/customers/search">Back to customer search</Link>
    <h1 className="text-3xl font-bold text-slate-900">Customer contact details</h1>
    <p className="text-slate-600">Owner only. Correct a name or phone for this person. Orders stay with this customer; records are never merged here.</p>
    <PendingSaveNotice {...save} onRetry={() => submit(null, true)} />
    {error ? <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-800">{error}</p> : null}
    {message ? <p role="status" className="rounded-xl bg-green-50 p-4 text-green-800">{message}</p> : null}
    <button className="min-h-11 font-bold text-[#005AAB] underline disabled:opacity-60" type="button" onClick={reloadDetails} disabled={loading || submitting || save.isSaving || Boolean(save.pending) || !save.ready}>Reload saved details</button>
    {loading ? <p role="status">Loading contact details…</p> : customer ? <>
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-bold">Saved customer #{customer.id}</h2>
        <p>{customer.name} · {customer.phone}</p>
        <p className="mt-2 text-sm text-slate-600">Changes appear wherever these customer details are shown, including older order screens. Previous details stay in the history below.</p>
      </div>
      <form className="rounded-xl border border-slate-200 bg-white p-5" onSubmit={submit}>
        <fieldset className="space-y-4" disabled={stale || submitting || save.isSaving || Boolean(save.pending) || !save.ready}>
          <legend className="mb-4 text-lg font-bold">Correct contact details</legend>
          <label className="block font-semibold">Customer name
            <input className={inputClass} value={name} onChange={(event) => editDetails(setName, event.target.value)} minLength={2} maxLength={100} autoComplete="off" required />
          </label>
          <label className="block font-semibold">Phone number
            <input className={inputClass} type="tel" value={phone} onChange={(event) => editDetails(setPhone, event.target.value)} maxLength={40} autoComplete="off" required />
          </label>
          {matches.length ? <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
            <p className="font-bold">This number is already saved for:</p>
            <ul className="mt-2">{matches.map((match) => <li key={match.id}>{match.name} · {match.phone} · Customer #{match.id}</li>)}</ul>
            <label className="mt-3 flex items-start gap-2"><input type="checkbox" className="mt-1" checked={sharedPhone} onChange={(event) => { setSharedPhone(event.target.checked); setConfirmed(false); }} />I checked that these are different people who share this phone. Keep their records separate.</label>
          </div> : null}
          <label className="block font-semibold">Reason for correction
            <textarea className={`${inputClass} min-h-20 py-2`} value={reason} onChange={(event) => { setReason(event.target.value); setConfirmed(false); }} maxLength={300} required />
          </label>
          <label className="flex items-start gap-2 font-semibold"><input type="checkbox" className="mt-1" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />I checked these details belong to this customer.</label>
          <button className={buttonClass} type="submit" disabled={!confirmed || !reason.trim() || Boolean(matches.length && !sharedPhone)}>{save.isSaving ? "Saving…" : "Save contact correction"}</button>
        </fieldset>
      </form>
      <section aria-label="Contact correction history" className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-bold">Contact correction history</h2>
        {history.length ? <ul className="mt-3 space-y-4">{history.map((item) => <li className="border-t border-slate-200 pt-3" key={item.id}>
          <p><strong>Before:</strong> {item.before_state.name} · {item.before_state.phone}</p>
          <p><strong>After:</strong> {item.after_state.name} · {item.after_state.phone}</p>
          <p>Reason: {item.reason}</p>
          <p className="text-sm text-slate-600">{item.confirmed_by_username} · {new Date(item.created_at).toLocaleString("en-KE", { timeZone: "Africa/Nairobi" })}</p>
          {item.shared_phone_confirmed ? <p className="text-sm">Shared phone confirmed; customer records kept separate.</p> : null}
        </li>)}</ul> : <p className="mt-2 text-slate-600">No contact corrections loaded.</p>}
      </section>
    </> : null}
  </section>;
}

function SelectedCustomerContact() {
  const customerId = readRecordId(useSearchParams());
  if (customerId === null) {
    return <section className="mx-auto max-w-3xl space-y-5">
      <h1 className="text-3xl font-bold text-slate-900">Customer contact details</h1>
      <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-800">This customer link is not valid. Find the customer again.</p>
      <Link className="inline-flex min-h-11 items-center font-bold text-[#005AAB] underline" href="/customers/search">Back to customer search</Link>
    </section>;
  }
  return <ContactDetails key={customerId} customerId={customerId} />;
}

export default function CustomerContactPage() {
  return <OwnerGuard><Suspense fallback={<p role="status">Loading contact details…</p>}><SelectedCustomerContact /></Suspense></OwnerGuard>;
}
