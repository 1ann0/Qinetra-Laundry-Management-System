"use client";

import { useState } from "react";
import usePendingSave from "./use-pending-save";
import PendingSaveNotice from "./pending-save-notice";
import { getUserMessage } from "@/lib/user-messages";

function money(value) {
  return `KES ${Number(value).toLocaleString("en-KE", { maximumFractionDigits: 2 })}`;
}

export default function QuantityCorrection({ order, onUpdated }) {
  const kgLines = order.service_lines.filter((line) => line.service_unit === "kg");
  const legacyWash = !order.service_lines.length && order.service_type === "wash_fold";
  const [lineId, setLineId] = useState(kgLines[0]?.id || null);
  const [quantity, setQuantity] = useState(String(kgLines[0]?.quantity || order.quantity));
  const [discount, setDiscount] = useState(String(kgLines[0]?.discount_amount || 0));
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const save = usePendingSave(`/orders/${order.id}/quantity-corrections`);
  const line = kgLines.find((item) => item.id === Number(lineId));
  const currentQuantity = Number(line?.quantity ?? order.quantity);
  const unitPrice = Number(line?.unit_price ?? order.unit_price);
  const currentLineTotal = Number(line?.line_total ?? order.total_price);
  const estimatedTotal = Number(order.total_price) - currentLineTotal + Number(quantity) * unitPrice - (line ? Number(discount) : 0);

  if ((!kgLines.length && !legacyWash) || ["collected", "cancelled"].includes(order.status)) return null;

  function finish(updatedOrder) {
    onUpdated(updatedOrder);
    const updatedLine = updatedOrder.service_lines.find((item) => item.id === lineId);
    setQuantity(String(updatedLine?.quantity ?? updatedOrder.quantity));
    setDiscount(String(updatedLine?.discount_amount ?? 0));
    setReason("");
    setConfirmed(false);
    setMessage("Quantity corrected. Check the new total and correction history.");
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    const amount = Number(quantity);
    if (!Number.isFinite(amount) || amount <= 0 || !/^\d+(?:\.\d{1,2})?$/.test(quantity)) {
      setError("Enter a kg quantity greater than zero, with at most two decimal places.");
      return;
    }
    if (amount === currentQuantity) {
      setError("Enter a different kg quantity before saving.");
      return;
    }
    if (line && (!Number.isFinite(Number(discount)) || Number(discount) < 0 || Number(discount) >= amount * unitPrice)) {
      setError("Enter a discount below the new service subtotal.");
      return;
    }
    if (!Number.isFinite(estimatedTotal) || estimatedTotal < Number(order.amount_paid)) {
      setError("The new total is below money already paid. Correct or refund the payment first.");
      return;
    }
    if (!reason.trim() || !confirmed) {
      setError("Enter the reason and confirm the new quantity and price.");
      return;
    }
    try {
      finish(await save.save({
        service_line_id: line?.id || null,
        expected_quantity: currentQuantity,
        new_quantity: amount,
        new_discount_amount: line ? Number(discount) : null,
        reason: reason.trim(), confirmed: true,
      }));
    } catch (saveError) {
      setError(getUserMessage(saveError, "QLMS could not confirm the correction. Use Retry previous save."));
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
      <summary className="cursor-pointer font-bold text-[#005AAB]">Owner: correct billed kg</summary>
      <form className="mt-4" onSubmit={submit}>
        <p className="text-sm text-slate-700">This changes the price using the rate saved on this order. Clothing counts and condition notes stay as recorded. Check them separately if needed.</p>
        <fieldset disabled={save.isSaving || Boolean(save.pending) || !save.ready} className="mt-4 grid gap-4 sm:grid-cols-2">
          {kgLines.length > 1 ? <label className="font-semibold text-slate-800 sm:col-span-2">Service
            <select className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" value={lineId || ""} onChange={(event) => {
              const chosen = kgLines.find((item) => item.id === Number(event.target.value));
              setLineId(chosen.id); setQuantity(String(chosen.quantity)); setDiscount(String(chosen.discount_amount)); setConfirmed(false);
            }}>
              {kgLines.map((item) => <option value={item.id} key={item.id}>{item.service_name} · {item.quantity} kg</option>)}
            </select>
          </label> : null}
          <label className="font-semibold text-slate-800">Correct kg quantity
            <input className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" type="number" min="0.01" step="0.01" value={quantity} onChange={(event) => setQuantity(event.target.value)} required />
          </label>
          {line ? <label className="font-semibold text-slate-800">Discount for this service (KES)
            <input className="mt-1 min-h-11 w-full rounded-lg border border-slate-400 bg-white px-3" type="number" min="0" step="0.01" value={discount} onChange={(event) => setDiscount(event.target.value)} required />
          </label> : null}
          <p className="self-end text-sm font-semibold text-slate-800">Saved rate: {money(unitPrice)}/kg<br />New order total: {Number.isFinite(estimatedTotal) ? money(estimatedTotal) : "Check the numbers"}</p>
          <label className="font-semibold text-slate-800 sm:col-span-2">Reason for correction
            <textarea className="mt-1 min-h-20 w-full rounded-lg border border-slate-400 bg-white p-3" maxLength={300} value={reason} onChange={(event) => setReason(event.target.value)} required />
          </label>
          <label className="flex items-start gap-2 font-semibold text-slate-800 sm:col-span-2"><input className="mt-1" type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />I checked the new quantity, discount and order total.</label>
          <button className="min-h-11 rounded-lg bg-[#005AAB] px-5 font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB] disabled:opacity-60" type="submit">{save.isSaving ? "Saving…" : "Save quantity correction"}</button>
        </fieldset>
      </form>
      {error ? <p role="alert" className="mt-3 text-sm font-semibold text-red-800">{error}</p> : null}
      {message ? <p role="status" className="mt-3 text-sm font-semibold text-green-800">{message}</p> : null}
    </details>
  </>);
}
