"use client";

import { useState } from "react";
import usePendingSave from "./use-pending-save";
import PendingSaveNotice from "./pending-save-notice";
import { getUserMessage } from "@/lib/user-messages";
import { formatNairobiDateTime } from "@/lib/format-nairobi";

const labels = {
  received: "Received", in_progress: "In Progress",
  ready: "Ready for Collection", collected: "Collected", cancelled: "Cancelled",
};

export default function OrderCorrections({ order, isOwner, onUpdated }) {
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [goodsReturned, setGoodsReturned] = useState(false);
  const [stillInShop, setStillInShop] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const save = usePendingSave(`/orders/${order.id}/corrections`);
  const canCancel = order.status === "received";
  const canMoveBack = ["in_progress", "ready", "collected"].includes(order.status);

  if (!isOwner && !(order.corrections || []).length) return null;

  function finish(updatedOrder) {
    onUpdated(updatedOrder);
    setReason("");
    setConfirmed(false);
    setGoodsReturned(false);
    setStillInShop(false);
    setMessage("Order correction saved. Check the stage and history below.");
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!reason.trim() || !confirmed) {
      setError("Enter the reason and tick the confirmation box.");
      return;
    }
    if (canCancel && !goodsReturned) {
      setError("Confirm that all customer items have been returned.");
      return;
    }
    if (order.status === "collected" && !stillInShop) {
      setError("Confirm that the order is still in the shop.");
      return;
    }
    try {
      finish(await save.save({
        action: canCancel ? "cancel" : "stage_back",
        expected_status: order.status,
        reason: reason.trim(), confirmed: true,
        goods_returned: goodsReturned, still_in_shop: stillInShop,
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

  return (
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7" aria-label="Order corrections">
      <h2 className="text-2xl font-bold text-slate-900">Order correction history</h2>
      {(order.corrections || []).length ? (
        <ol className="mt-4 space-y-2 text-sm text-slate-800">
          {order.corrections.map((item) => (
            <li className="rounded-xl border border-slate-200 bg-slate-50 p-3" key={item.id}>
              <strong>{item.action === "quantity"
                ? `${item.before_state.service_name}: ${Number(item.before_state.quantity)} → ${Number(item.after_state.quantity)} kg; total ${item.before_state.order_total} → ${item.after_state.order_total} KES`
                : `${labels[item.before_state.status]} → ${labels[item.after_state.status]}`}</strong>
              <span> · {item.confirmed_by_username} · {formatNairobiDateTime(item.created_at)}</span>
              <p className="mt-1">Reason: {item.reason}</p>
              {item.goods_returned_confirmed ? <p className="mt-1">Owner confirmed all items were returned.</p> : null}
              {item.still_in_shop_confirmed ? <p className="mt-1">Owner confirmed the order was still in the shop.</p> : null}
            </li>
          ))}
        </ol>
      ) : <p className="mt-2 text-slate-600">No order stage corrections recorded.</p>}

      {isOwner ? <PendingSaveNotice {...save} onRetry={retry} /> : null}
      {isOwner && (canCancel || canMoveBack) ? (
        <form className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4" onSubmit={submit}>
          <h3 className="font-bold text-slate-900">
            {canCancel ? "Cancel this unpaid order" : "Move back one stage"}
          </h3>
          <p className="mt-1 text-sm text-slate-700">
            {canCancel
              ? "Use this only before work starts, after returning all items and clearing any payment. The ticket stays in history."
              : "Use this only to correct an accidental stage change. The earlier stage and your reason stay in history."}
          </p>
          <fieldset disabled={save.isSaving || Boolean(save.pending) || !save.ready} className="mt-4 space-y-4">
            <label className="block font-semibold text-slate-800">Reason
              <textarea className="mt-1 min-h-20 w-full rounded-lg border border-slate-400 bg-white p-3" maxLength={300} value={reason} onChange={(event) => setReason(event.target.value)} required />
            </label>
            {canCancel ? <label className="flex items-start gap-2 font-semibold text-slate-800"><input className="mt-1" type="checkbox" checked={goodsReturned} onChange={(event) => setGoodsReturned(event.target.checked)} />I confirm all customer items have been returned.</label> : null}
            {order.status === "collected" ? <label className="flex items-start gap-2 font-semibold text-slate-800"><input className="mt-1" type="checkbox" checked={stillInShop} onChange={(event) => setStillInShop(event.target.checked)} />I confirm this order is still in Qinetra’s shop.</label> : null}
            <label className="flex items-start gap-2 font-semibold text-slate-800"><input className="mt-1" type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />I confirm this correction is accurate.</label>
            <button className="min-h-11 rounded-lg bg-[#005AAB] px-5 font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB] disabled:opacity-60" type="submit">{save.isSaving ? "Saving…" : canCancel ? "Cancel order" : "Save stage correction"}</button>
          </fieldset>
          {error ? <p role="alert" className="mt-3 text-sm font-semibold text-red-800">{error}</p> : null}
          {message ? <p role="status" className="mt-3 text-sm font-semibold text-green-800">{message}</p> : null}
        </form>
      ) : null}
    </section>
  );
}
