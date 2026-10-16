"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";
import usePendingSave from "@/components/orders/use-pending-save";
import PendingSaveNotice from "@/components/orders/pending-save-notice";
import { readRecordId } from "@/lib/record-id";
import { getUserMessage } from "@/lib/user-messages";
import { formatNairobiDateTime } from "@/lib/format-nairobi";
import { formatKes, nairobiToday } from "@/lib/report-tools";
import { EXPENSE_CATEGORIES, EXPENSE_FIELDS, EXPENSE_FUNDING_SOURCES, expenseBody, pendingExpenseValues } from "@/lib/expense-tools";

const INPUT = "mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-base text-slate-900 focus:border-[#005AAB] focus:outline-none focus:ring-4 focus:ring-blue-100";
const LABELS = { paid_date: "Paid date", category: "Category", amount: "Amount in KES", payment_method: "Paid using", funding_source: "Paid from", reference: "Receipt or transaction reference (optional)", note: "What was paid for? (optional)", reason: "Why are you changing this entry?" };
const SELECT_OPTIONS = { category: EXPENSE_CATEGORIES, payment_method: { cash: "Cash", mpesa: "M-Pesa" }, funding_source: { "": "Choose who paid", ...EXPENSE_FUNDING_SOURCES } };

function ExpenseDetails({ details }) {
  if (!details) return null;
  return <dl className="grid gap-3 sm:grid-cols-2">
    <div><dt className="text-sm text-slate-600">Paid date</dt><dd className="font-semibold">{details.paid_date}</dd></div>
    <div><dt className="text-sm text-slate-600">Amount and method</dt><dd className="font-semibold">{formatKes(details.amount)} · {details.payment_method === "cash" ? "Cash" : "M-Pesa"}</dd></div>
    <div><dt className="text-sm text-slate-600">Category</dt><dd>{EXPENSE_CATEGORIES[details.category]}</dd></div>
    <div><dt className="text-sm text-slate-600">Paid from</dt><dd>{EXPENSE_FUNDING_SOURCES[details.funding_source] || "Not confirmed"}</dd></div>
    <div><dt className="text-sm text-slate-600">Entry state</dt><dd>{details.is_voided ? "Reversed — excluded from totals" : "Recorded"}</dd></div>
    {details.reference ? <div><dt className="text-sm text-slate-600">Reference</dt><dd className="break-words">{details.reference}</dd></div> : null}
    {details.note ? <div><dt className="text-sm text-slate-600">Note</dt><dd className="whitespace-pre-wrap break-words">{details.note}</dd></div> : null}
  </dl>;
}

function ExpenseEditor({ expenseId }) {
  const { authenticatedRequest } = useAuth();
  const save = usePendingSave(expenseId ? `/expenses/${expenseId}/corrections` : "/expenses");
  const [record, setRecord] = useState(null);
  const [form, setForm] = useState(() => ({ paid_date: nairobiToday(), category: "supplies", amount: "", payment_method: "cash", funding_source: "", reference: "", note: "", reason: "", is_voided: false }));
  const [loading, setLoading] = useState(Boolean(expenseId));
  const [reload, setReload] = useState(0);
  const [stale, setStale] = useState(false);
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const feedback = useRef(null);
  const values = pendingExpenseValues(save.pending) || form;
  const locked = loading || stale || save.isSaving || Boolean(save.pending) || !save.ready || (!expenseId && Boolean(record));

  useEffect(() => {
    if (!expenseId) return;
    const controller = new AbortController();
    void authenticatedRequest(`/expenses/${expenseId}`, { signal: controller.signal, cache: "no-store" }).then(saved => {
      if (controller.signal.aborted) return;
      setRecord(saved); setForm({ ...saved, reason: "" }); setStale(false);
    }).catch(loadError => { if (!controller.signal.aborted) setError(getUserMessage(loadError, "The expense could not be loaded.")); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [authenticatedRequest, expenseId, reload]);

  function edit(field, value) { setForm(current => ({ ...current, [field]: value })); setErrors(current => ({ ...current, [field]: "" })); setMessage(""); }
  async function submit(event, retry = false) {
    event?.preventDefault(); setError(""); setMessage("");
    const prepared = expenseBody(form, expenseId ? record : null);
    if (!retry && Object.keys(prepared.errors).length) { setErrors(prepared.errors); feedback.current?.focus(); return; }
    setErrors({});
    try {
      const saved = retry ? await save.retry() : await save.save(prepared.body);
      setRecord(saved); setForm({ ...saved, reason: "" });
      setMessage(expenseId ? "Correction saved. The original entry and previous changes remain below." : `Expense #${saved.id} saved once. It is included in the expense report.`);
    } catch (saveError) {
      setError(getUserMessage(saveError, "The expense could not be confirmed."));
      if (saveError.code === "QLMS-STALE-RECORD") setStale(true);
    }
  }

  function reloadRecord() { setLoading(true); setError(""); setMessage(""); setErrors({}); setReload(value => value + 1); }
  return <section className="mx-auto max-w-3xl space-y-5">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-bold uppercase tracking-widest text-[#005AAB]">Owner money control</p><h1 className="mt-2 text-3xl font-bold text-slate-900">{expenseId ? `Expense #${expenseId}` : "Record an expense"}</h1></div><Link className="secondary-button" href="/reports?report=expenses">Expense history and downloads</Link></header>
    <p className="text-slate-600">Record purchases and wages on the day they are paid. Choose shop money or the Owner&apos;s own money; both are business costs. A bulk purchase is one entry; each later top-up is another. Personal withdrawals and till additions belong in separate records.</p>
    <PendingSaveNotice {...save} onRetry={() => submit(null, true)} />
    {save.pending && !values.funding_source ? <p role="status" className="rounded-xl bg-amber-50 p-4 text-amber-950">This previous save does not include who paid. Retry it unchanged, then check the saved details and confirm Paid from through a correction.</p> : null}
    <div ref={feedback} tabIndex={-1} role={error || Object.values(errors).some(Boolean) ? "alert" : undefined} className={error || Object.values(errors).some(Boolean) ? "rounded-xl border border-red-300 bg-red-50 p-4 text-red-800" : ""}>
      {error || (Object.values(errors).some(Boolean) ? "Check the marked fields before saving." : "")}
    </div>
    {message ? <p role="status" className="rounded-xl border border-green-300 bg-green-50 p-4 text-green-900">{message}</p> : null}
    {loading ? <p role="status">Loading saved expense…</p> : expenseId && !record ? <button className="secondary-button" onClick={reloadRecord} type="button">Try loading again</button> : <>
      {record ? <section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="mb-4 text-lg font-bold">Saved details</h2><ExpenseDetails details={record} /><p className="mt-4 text-sm text-slate-600">Recorded by {record.confirmed_by_username} · {formatNairobiDateTime(record.created_at)} · {record.revision} corrections</p>
        {!record.funding_source && !record.is_voided ? <p className="mt-4 rounded-xl bg-amber-50 p-4 text-amber-950">Who paid has not been confirmed. This still counts as a business cost. Confirm Paid from with a correction when you know; do not guess.</p> : null}
        {!expenseId ? <div className="mt-4 flex flex-wrap gap-3"><Link className="secondary-button" href={`/expenses?id=${record.id}`}>Open correction history</Link><a className="secondary-button" href="/expenses">Record another expense</a></div> : null}
      </section> : null}
      {(!record || expenseId) ? <form id="expense-entry-step" className="rounded-2xl border border-slate-200 bg-white p-5" onSubmit={submit} noValidate>
        <fieldset disabled={locked} className="space-y-5"><legend className="mb-4 text-xl font-bold">{expenseId ? "Correct this expense" : "Expense details"}</legend>
          <div className="grid gap-5 sm:grid-cols-2">{[...EXPENSE_FIELDS, ...(expenseId ? ["reason"] : [])].map(field => <div key={field} className={field === "note" || field === "reason" ? "sm:col-span-2" : ""}>
            <label htmlFor={`expense-${field}`} className="block font-bold text-slate-800">{field === "note" && values.category === "wages" ? "Who was paid, which period and any deduction? (optional)" : field === "note" && values.category === "outsourcing" ? "Transport or dry-cleaner charge; related ticket (optional)" : field === "funding_source" && !expenseId ? "Paid from (required)" : LABELS[field]}</label>
            {Object.hasOwn(SELECT_OPTIONS,field) ? <select id={`expense-${field}`} className={INPUT} value={values[field] ?? ""} onChange={event => edit(field, event.target.value)} aria-required={field === "funding_source" && (!expenseId || Boolean(record?.funding_source))} aria-invalid={Boolean(errors[field])} aria-describedby={errors[field] ? `expense-error-${field}` : undefined}>
              {Object.entries(SELECT_OPTIONS[field]).map(([value, label]) => <option key={value} value={value}>{field === "funding_source" && !value && expenseId && !record?.funding_source ? "Not confirmed" : label}</option>)}
            </select> : field === "note" ? <textarea id={`expense-${field}`} className={`${INPUT} min-h-24 py-3`} value={values[field]} maxLength={1000} onChange={event => edit(field, event.target.value)} aria-invalid={Boolean(errors[field])} aria-describedby={errors[field] ? `expense-error-${field}` : undefined} /> : <input id={`expense-${field}`} className={INPUT} type={field === "paid_date" ? "date" : "text"} max={field === "paid_date" ? nairobiToday() : undefined} inputMode={field === "amount" ? "decimal" : undefined} maxLength={field === "reference" ? 100 : field === "reason" ? 200 : undefined} value={values[field]} onChange={event => edit(field, event.target.value)} aria-invalid={Boolean(errors[field])} aria-describedby={errors[field] ? `expense-error-${field}` : undefined} autoComplete="off" />}
            {errors[field] ? <p id={`expense-error-${field}`} className="mt-2 text-sm font-semibold text-red-800">{errors[field]}</p> : null}
          </div>)}</div>
          {expenseId ? <label className="flex min-h-12 items-start gap-3 rounded-xl bg-amber-50 p-4"><input className="mt-1 size-5" type="checkbox" checked={Boolean(values.is_voided)} onChange={event => edit("is_voided", event.target.checked)} /><span><strong>Reverse this expense</strong><br />Keep its history but exclude it from cost totals. Clear this choice to restore it, explaining why above.</span></label> : null}
          <button className="primary-button min-h-12" type="submit">{save.isSaving ? "Saving…" : expenseId ? "Save correction" : "Save expense"}</button>
        </fieldset>
      </form> : null}
      {expenseId ? <><button className="secondary-button" type="button" disabled={loading || save.isSaving || Boolean(save.pending) || !save.ready} onClick={reloadRecord}>Reload saved details</button><section id="expense-history-step" className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-xl font-bold">Original entry and corrections</h2><div className="mt-4 rounded-xl bg-slate-50 p-4"><h3 className="mb-3 font-bold">Original entry</h3><ExpenseDetails details={record.original_details} /></div>
        {record.corrections.length ? <ol className="mt-4 space-y-4">{record.corrections.map(change => <li className="rounded-xl border border-slate-200 p-4" key={change.id}><h3 className="font-bold">Correction {change.revision}</h3><p className="mt-1 break-words">{change.reason}</p><p className="mb-4 mt-2 text-sm text-slate-600">{change.confirmed_by_username} · {formatNairobiDateTime(change.created_at)}</p><details><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">Before this change</summary><ExpenseDetails details={change.before_details} /></details><h4 className="mb-3 mt-3 font-semibold">After this change</h4><ExpenseDetails details={change.after_details} /></li>)}</ol> : <p className="mt-4 text-slate-600">No corrections. The original entry is still current.</p>}
      </section></> : null}
    </>}
  </section>;
}

function ExpenseSelection() {
  const parameters = useSearchParams();
  const id = parameters.has("id") ? readRecordId(parameters) : null;
  if (parameters.has("id") && id === null) return <p role="alert">This expense link is not valid. Open Expense history in Reports and select the entry again.</p>;
  return <ExpenseEditor key={id || "new"} expenseId={id} />;
}

export default function ExpensesPage() { return <OwnerGuard><Suspense fallback={<p role="status">Opening expenses…</p>}><ExpenseSelection /></Suspense></OwnerGuard>; }
