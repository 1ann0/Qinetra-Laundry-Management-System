"use client";

import { useState } from "react";
import { formatNairobiDateTime } from "@/lib/format-nairobi";
import { getUserMessage } from "@/lib/user-messages";

function getDefaultReturnTime() {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

function getDraft(drafts, itemId) {
  return drafts[itemId] || { return_condition: "returned_ok", issue_note: "" };
}

export default function OutsourceRegister({
  orderId,
  orderStatus,
  serviceLine,
  role,
  authenticatedRequest,
  onServiceLineSaved,
}) {
  const [showHandoverForm, setShowHandoverForm] = useState(false);
  const [partnerName, setPartnerName] = useState("");
  const [expectedReturnAt, setExpectedReturnAt] = useState(getDefaultReturnTime);
  const [returnDrafts, setReturnDrafts] = useState({});
  const [resolutionNotes, setResolutionNotes] = useState({});
  const [activeAction, setActiveAction] = useState("");
  const [error, setError] = useState("");
  const [showInHouseForm, setShowInHouseForm] = useState(false);
  const [inHouseReason, setInHouseReason] = useState("");

  if (serviceLine.item_recording_mode !== "detailed") return null;

  const handover = serviceLine.outsourcing_handover;
  const canChange = orderStatus === "received" || orderStatus === "in_progress";
  const garments = new Map(serviceLine.items.map((item) => [item.id, item]));

  async function saveHandover(event) {
    event.preventDefault();
    if (!partnerName.trim()) {
      setError("Enter the dry cleaner's name.");
      return;
    }
    if (!expectedReturnAt) {
      setError("Enter when the garments are expected back.");
      return;
    }

    setActiveAction("handover");
    setError("");
    try {
      const savedLine = await authenticatedRequest(
        `/orders/${orderId}/services/${serviceLine.id}/outsourcing`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            partner_name: partnerName.trim(),
            expected_return_at: new Date(expectedReturnAt).toISOString(),
          }),
        },
      );
      onServiceLineSaved(savedLine);
      setShowHandoverForm(false);
    } catch (saveError) {
      setError(getUserMessage(
        saveError,
        "The handover could not be confirmed. Open the order again before you retry.",
      ));
    } finally {
      setActiveAction("");
    }
  }

  async function confirmInHouse(event) {
    event.preventDefault();
    if (!inHouseReason.trim()) {
      setError("Explain why these garments are being cleaned in the shop.");
      return;
    }
    setActiveAction("in-house");
    setError("");
    try {
      const savedLine = await authenticatedRequest(
        `/orders/${orderId}/services/${serviceLine.id}/in-house`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: inHouseReason.trim() }),
        },
      );
      onServiceLineSaved(savedLine);
    } catch (saveError) {
      setError(getUserMessage(
        saveError,
        "The in-shop cleaning choice could not be confirmed. Open the order again before you retry.",
      ));
    } finally {
      setActiveAction("");
    }
  }

  function updateReturnDraft(itemId, field, value) {
    setReturnDrafts((current) => ({
      ...current,
      [itemId]: { ...getDraft(current, itemId), [field]: value },
    }));
  }

  async function confirmReturn(handoverItem) {
    const draft = getDraft(returnDrafts, handoverItem.id);
    if (draft.return_condition === "issue" && !draft.issue_note.trim()) {
      setError("Describe the issue found when this garment returned.");
      return;
    }

    setActiveAction(`return-${handoverItem.id}`);
    setError("");
    try {
      const savedLine = await authenticatedRequest(
        `/orders/${orderId}/outsourcing/${handover.id}/returns`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: [{
              handover_item_id: handoverItem.id,
              return_condition: draft.return_condition,
              issue_note:
                draft.return_condition === "issue"
                  ? draft.issue_note.trim()
                  : null,
            }],
          }),
        },
      );
      onServiceLineSaved(savedLine);
    } catch (saveError) {
      setError(getUserMessage(
        saveError,
        "The garment return could not be confirmed. Check the handover before you retry.",
      ));
    } finally {
      setActiveAction("");
    }
  }

  async function resolveIssue(handoverItem) {
    const note = resolutionNotes[handoverItem.id]?.trim();
    if (!note) {
      setError("Enter how the return issue was resolved.");
      return;
    }

    setActiveAction(`resolve-${handoverItem.id}`);
    setError("");
    try {
      const savedLine = await authenticatedRequest(
        `/orders/${orderId}/outsourcing/${handover.id}/returns/${handoverItem.id}/resolve`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resolution_note: note }),
        },
      );
      onServiceLineSaved(savedLine);
    } catch (saveError) {
      setError(getUserMessage(
        saveError,
        "The issue could not be closed. Open the order again before you retry.",
      ));
    } finally {
      setActiveAction("");
    }
  }

  if (!handover) {
    if (serviceLine.in_house_at) {
      return (
        <section className="mt-5 rounded-xl border border-green-200 bg-green-50 p-4">
          <h3 className="font-bold text-slate-900">Handled in Qinetra</h3>
          <p className="mt-1 text-sm text-slate-700">
            {serviceLine.in_house_reason} · Confirmed by {serviceLine.in_house_by_username} · {formatNairobiDateTime(serviceLine.in_house_at)}
          </p>
        </section>
      );
    }
    return (
      <section className="mt-5 rounded-xl border border-violet-200 bg-violet-50 p-4">
        <h3 className="font-bold text-slate-900">Outside dry cleaner</h3>
        <p className="mt-1 text-sm text-slate-600">
          Record this only when every listed garment physically leaves Qinetra.
        </p>
        {!showHandoverForm ? (
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              className="min-h-11 rounded-lg border border-violet-700 bg-white px-4 font-bold text-violet-800 hover:bg-violet-100 disabled:opacity-50"
              type="button"
              disabled={
                !canChange ||
                serviceLine.item_check_status !== "completed" ||
                serviceLine.items.length === 0
              }
              onClick={() => setShowHandoverForm(true)}
            >
              Record dry-cleaner handover
            </button>
            {role === "owner" && serviceLine.outsourcing_required ? (
              <button
                className="min-h-11 rounded-lg border border-slate-400 bg-white px-4 font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                type="button"
                disabled={!canChange || serviceLine.item_check_status !== "completed"}
                onClick={() => setShowInHouseForm((current) => !current)}
              >
                Confirm handled in Qinetra
              </button>
            ) : null}
          </div>
        ) : (
          <form className="mt-4 space-y-4" onSubmit={saveHandover}>
            <div>
              <label className="block text-sm font-bold text-slate-800" htmlFor={`partner-${serviceLine.id}`}>
                Dry cleaner
              </label>
              <input
                className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 outline-none focus:border-violet-700 focus:ring-2 focus:ring-violet-100"
                id={`partner-${serviceLine.id}`}
                maxLength="100"
                value={partnerName}
                disabled={Boolean(activeAction)}
                onChange={(event) => setPartnerName(event.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-800" htmlFor={`expected-return-${serviceLine.id}`}>
                Expected back
              </label>
              <input
                className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 outline-none focus:border-violet-700 focus:ring-2 focus:ring-violet-100"
                id={`expected-return-${serviceLine.id}`}
                type="datetime-local"
                value={expectedReturnAt}
                disabled={Boolean(activeAction)}
                onChange={(event) => setExpectedReturnAt(event.target.value)}
              />
            </div>
            <p className="text-sm font-semibold text-violet-950">
              {serviceLine.items.length} {serviceLine.items.length === 1 ? "garment" : "garments"} will be recorded as sent.
            </p>
            <div className="flex flex-wrap gap-3">
              <button className="min-h-11 rounded-lg bg-violet-800 px-4 font-bold text-white disabled:opacity-50" type="submit" disabled={Boolean(activeAction)}>
                {activeAction === "handover" ? "Saving…" : "Confirm handover"}
              </button>
              <button className="min-h-11 rounded-lg border border-slate-300 bg-white px-4 font-bold text-slate-700" type="button" disabled={Boolean(activeAction)} onClick={() => setShowHandoverForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        )}
        {showInHouseForm && !showHandoverForm ? (
          <form className="mt-4 rounded-lg border border-slate-200 bg-white p-4" onSubmit={confirmInHouse}>
            <label className="block text-sm font-bold text-slate-800" htmlFor={`in-house-reason-${serviceLine.id}`}>
              Why is this staying in the shop?
            </label>
            <input
              className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3"
              id={`in-house-reason-${serviceLine.id}`}
              maxLength="300"
              value={inHouseReason}
              disabled={Boolean(activeAction)}
              onChange={(event) => setInHouseReason(event.target.value)}
            />
            <button className="mt-3 min-h-11 rounded-lg bg-slate-800 px-4 font-bold text-white disabled:opacity-50" type="submit" disabled={Boolean(activeAction)}>
              {activeAction === "in-house" ? "Saving…" : "Confirm in-shop cleaning"}
            </button>
          </form>
        ) : null}
        {error ? <p className="mt-3 text-sm font-semibold text-red-800" role="alert">{error}</p> : null}
      </section>
    );
  }

  return (
    <section className="mt-5 rounded-xl border border-violet-200 bg-violet-50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-bold text-slate-900">Dry-cleaner handover</h3>
          <p className="mt-1 text-sm text-slate-700">
            {handover.partner_name} · Sent by {handover.sent_by_username} · {formatNairobiDateTime(handover.sent_at)}
          </p>
          <p className="mt-1 text-sm text-slate-700">
            Expected back: {formatNairobiDateTime(handover.expected_return_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-violet-800">
            {handover.outstanding_count} outstanding
          </span>
          {handover.unresolved_issue_count > 0 ? (
            <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-bold text-red-800">
              {handover.unresolved_issue_count} unresolved
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {handover.items.map((handoverItem) => {
          const garment = garments.get(handoverItem.order_item_id);
          const draft = getDraft(returnDrafts, handoverItem.id);
          const isWorking = activeAction.endsWith(`-${handoverItem.id}`);
          return (
            <article className="rounded-lg border border-violet-100 bg-white p-4" key={handoverItem.id}>
              <p className="font-bold text-slate-900">{handoverItem.garment_reference}</p>
              <p className="mt-1 text-sm text-slate-600">{garment?.description || garment?.item_name || "Recorded garment"}</p>

              {!handoverItem.returned_at ? (
                canChange ? (
                  <div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
                    <div>
                      <label className="block text-sm font-semibold text-slate-800" htmlFor={`return-condition-${handoverItem.id}`}>Return check</label>
                      <select
                        className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 px-3"
                        id={`return-condition-${handoverItem.id}`}
                        value={draft.return_condition}
                        disabled={Boolean(activeAction)}
                        onChange={(event) => updateReturnDraft(handoverItem.id, "return_condition", event.target.value)}
                      >
                        <option value="returned_ok">Returned as expected</option>
                        <option value="issue">Issue found</option>
                      </select>
                      {draft.return_condition === "issue" ? (
                        <input
                          aria-label={`Issue for ${handoverItem.garment_reference}`}
                          className="mt-2 min-h-11 w-full rounded-lg border border-red-300 px-3"
                          maxLength="300"
                          placeholder="Describe what is wrong"
                          value={draft.issue_note}
                          disabled={Boolean(activeAction)}
                          onChange={(event) => updateReturnDraft(handoverItem.id, "issue_note", event.target.value)}
                        />
                      ) : null}
                    </div>
                    <button className="min-h-11 rounded-lg bg-violet-800 px-4 font-bold text-white disabled:opacity-50" type="button" disabled={Boolean(activeAction)} onClick={() => confirmReturn(handoverItem)}>
                      {isWorking ? "Saving…" : "Confirm return"}
                    </button>
                  </div>
                ) : (
                  <p className="mt-3 text-sm font-bold text-amber-900">Still with the dry cleaner</p>
                )
              ) : handoverItem.return_condition === "returned_ok" ? (
                <p className="mt-3 text-sm font-semibold text-green-800">
                  Returned as expected · {handoverItem.returned_by_username} · {formatNairobiDateTime(handoverItem.returned_at)}
                </p>
              ) : (
                <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-900">
                  <p className="font-bold">Return issue: {handoverItem.issue_note}</p>
                  {handoverItem.issue_resolved_at ? (
                    <p className="mt-2">Resolved: {handoverItem.resolution_note} · {handoverItem.issue_resolved_by_username} · {formatNairobiDateTime(handoverItem.issue_resolved_at)}</p>
                  ) : role === "owner" ? (
                    <div className="mt-3">
                      <input
                        aria-label={`Resolution for ${handoverItem.garment_reference}`}
                        className="min-h-11 w-full rounded-lg border border-red-300 bg-white px-3"
                        maxLength="300"
                        placeholder="How was this resolved?"
                        value={resolutionNotes[handoverItem.id] || ""}
                        disabled={Boolean(activeAction)}
                        onChange={(event) => setResolutionNotes((current) => ({ ...current, [handoverItem.id]: event.target.value }))}
                      />
                      <button className="mt-2 min-h-10 rounded-lg bg-red-800 px-4 font-bold text-white disabled:opacity-50" type="button" disabled={Boolean(activeAction)} onClick={() => resolveIssue(handoverItem)}>
                        {isWorking ? "Saving…" : "Resolve issue"}
                      </button>
                    </div>
                  ) : (
                    <p className="mt-2 font-semibold">Ask the owner to resolve this issue before the order is ready.</p>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>
      {error ? <p className="mt-3 text-sm font-semibold text-red-800" role="alert">{error}</p> : null}
    </section>
  );
}
