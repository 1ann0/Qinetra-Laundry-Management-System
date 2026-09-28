"use client";

import { useState } from "react";
import usePendingSave from "./use-pending-save";
import PendingSaveNotice from "./pending-save-notice";
import { getUserMessage } from "@/lib/user-messages";

function money(value) {
  return `KES ${Number(value).toLocaleString("en-KE", { maximumFractionDigits: 2 })}`;
}

function todayInNairobi() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date());
}

export default function PaymentCorrections({ order, isOwner, onUpdated }) {
  const [paymentId, setPaymentId] = useState(
    order.payments.find((payment) => payment.payment_method !== "legacy")?.id || 0,
  );
  const [kind, setKind] = useState("entry_error");
  const [refundMethod, setRefundMethod] = useState("cash");
  const [refundPurpose, setRefundPurpose] = useState("service_refund");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [effectiveDate, setEffectiveDate] = useState(todayInNairobi);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const save = usePendingSave(`/orders/${order.id}/payments/${paymentId}/adjustments`);
  // Keep the old endpoint available for replay of an accepted pre-upgrade save.
  const refundSave = usePendingSave(`/orders/${order.id}/refunds`);
  const selectedPayment = order.payments.find((payment) => payment.id === Number(paymentId));
  const paymentRemaining = selectedPayment
    ? Number(selectedPayment.amount) - (order.payment_adjustments || [])
      .filter((item) => item.payment_id === selectedPayment.id)
      .reduce((total, item) => total + Number(item.amount), 0)
    : 0;
  const remaining = kind === "refund" ? Math.min(paymentRemaining,
    Number(refundPurpose === "service_refund" ? order.net_charge : order.refund_due)) : paymentRemaining;

  if (!isOwner && !(order.payment_adjustments || []).length) return null;

  function finish(updatedOrder) {
    onUpdated(updatedOrder);
    setAmount("");
    setReason("");
    setConfirmed(false);
    setMessage("Correction saved. Check the history and new balance.");
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!selectedPayment || !Number.isFinite(Number(amount)) || Number(amount) <= 0 || Number(amount) > remaining) {
      setError(`Enter an amount greater than zero and no more than ${money(remaining)}.`);
      return;
    }
    if (!reason.trim() || !confirmed) {
      setError("Enter the reason and tick the confirmation box.");
      return;
    }
    try {
      finish(await (kind === "refund" ? refundSave.save({
        payment_id: selectedPayment.id,
        refund_purpose: refundPurpose,
        refund_method: refundMethod,
        amount: Number(amount), reason: reason.trim(), confirmed: true,
        effective_date: effectiveDate,
      }) : save.save({
        kind,
        refund_method: null,
        amount: Number(amount),
        reason: reason.trim(),
        confirmed: true,
        effective_date: selectedPayment.received_date,
      })));
    } catch (saveError) {
      setError(getUserMessage(saveError, "QLMS could not confirm the correction. Use Retry previous save."));
    }
  }

  async function retry(pendingSave) {
    setError("");
    try {
      finish(await pendingSave.retry());
    } catch (saveError) {
      setError(getUserMessage(saveError));
    }
  }

  return (
    <section className="mt-6 border-t border-slate-200 pt-6" aria-label="Payment corrections">
      <h3 className="text-lg font-bold text-slate-900">Payment corrections and refunds</h3>
      {(order.payment_adjustments || []).length ? (
        <ul className="mt-3 space-y-2 text-sm text-slate-800">
          {order.payment_adjustments.map((item) => (
            <li className="rounded-xl border border-slate-200 bg-slate-50 p-3" key={item.id}>
              <strong>{item.kind === "refund" ? "Money returned" : "Entry corrected"}: {money(item.amount)}</strong>
              {item.kind === "refund" ? ` via ${item.refund_method === "mpesa" ? "M-PESA" : "cash"}` : ""}
              {item.kind === "refund" ? <p>{item.refund_purpose === "service_refund" ? "Service refund — charge reduced" : item.refund_purpose === "excess_payment" ? "Excess payment returned — charge unchanged" : "Purpose not recorded on this older refund. Owner review needed."}</p> : null}
              {` · ${item.effective_date} · Payment #${item.payment_id} · ${item.confirmed_by_username}`}
              {isOwner ? <p className="mt-1">Reason: {item.reason}</p> : null}
            </li>
          ))}
        </ul>
      ) : <p className="mt-2 text-sm text-slate-600">No corrections or refunds recorded.</p>}

      {isOwner ? <>
        <PendingSaveNotice {...save} onRetry={() => retry(save)} />
        <PendingSaveNotice {...refundSave} onRetry={() => retry(refundSave)} />
      </> : null}
      {isOwner && order.payments.some((payment) => payment.payment_method !== "legacy") && order.status !== "cancelled" ? (
        <form className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4" onSubmit={submit}>
          <h4 className="font-bold text-slate-900">Owner: correct a payment</h4>
          <p className="mt-1 text-sm text-slate-700">Use Entry mistake when the recorded amount was wrong. Use Money returned only after the customer receives a refund. The original payment and clothing stage stay in history.</p>
          <fieldset disabled={save.isSaving || refundSave.isSaving || Boolean(save.pending) || Boolean(refundSave.pending) || !save.ready || !refundSave.ready} className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="font-semibold text-slate-800">Payment
              <select className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" value={paymentId} onChange={(event) => { setPaymentId(Number(event.target.value)); setAmount(""); }}>
                {order.payments.filter((payment) => payment.payment_method !== "legacy").map((payment) => (
                  <option key={payment.id} value={payment.id}>#{payment.id} · {payment.payment_method === "mpesa" ? "M-PESA" : "Cash"} · {money(payment.amount)} · {payment.received_date}</option>
                ))}
              </select>
            </label>
            <label className="font-semibold text-slate-800">What happened?
              <select className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" value={kind} onChange={(event) => { setKind(event.target.value); setConfirmed(false); }}>
                <option value="entry_error">Entry mistake (no money returned)</option>
                <option value="refund">Money returned to customer</option>
              </select>
            </label>
            {kind === "refund" ? <label className="font-semibold text-slate-800 sm:col-span-2">Refund purpose
              <select className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" value={refundPurpose} onChange={(event) => { setRefundPurpose(event.target.value); setConfirmed(false); }}>
                <option value="service_refund">Service refund — reduce the charge</option>
                <option value="excess_payment">Return excess payment — keep the corrected charge</option>
              </select>
              <span className="mt-1 block text-sm font-normal">Charge: {money(order.net_charge)}. Excess payment due back: {money(order.refund_due)}.</span>
            </label> : null}
            <label className="font-semibold text-slate-800">Amount (up to {money(remaining)})
              <input className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" type="number" min="0.01" max={remaining} step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required />
            </label>
            {kind === "refund" ? <>
              <label className="font-semibold text-slate-800">How was it returned?
                <select className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" value={refundMethod} onChange={(event) => setRefundMethod(event.target.value)}><option value="cash">Cash</option><option value="mpesa">M-PESA</option></select>
              </label>
              <label className="font-semibold text-slate-800">Date money was returned
                <input className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" type="date" min={selectedPayment?.received_date} max={todayInNairobi()} value={effectiveDate} onChange={(event) => setEffectiveDate(event.target.value)} required />
              </label>
            </> : null}
            <label className="font-semibold text-slate-800 sm:col-span-2">Reason
              <textarea className="mt-1 min-h-20 w-full rounded-lg border border-slate-400 bg-white p-3" maxLength={300} value={reason} onChange={(event) => setReason(event.target.value)} required />
            </label>
            <label className="flex items-start gap-2 font-semibold text-slate-800 sm:col-span-2"><input className="mt-1" type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />{kind === "refund" ? "I confirm the customer received this refund." : "I confirm this was a recording mistake and no money was returned."}</label>
            <button className="min-h-11 rounded-lg bg-[#005AAB] px-5 font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB] disabled:opacity-60" type="submit">{save.isSaving || refundSave.isSaving ? "Saving…" : kind === "refund" ? "Save refund" : "Save correction"}</button>
          </fieldset>
          {error ? <p role="alert" className="mt-3 text-sm font-semibold text-red-800">{error}</p> : null}
          {message ? <p role="status" className="mt-3 text-sm font-semibold text-green-800">{message}</p> : null}
        </form>
      ) : null}
    </section>
  );
}
