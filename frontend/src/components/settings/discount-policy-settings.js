"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import usePendingSave from "@/components/orders/use-pending-save";
import PendingSaveNotice from "@/components/orders/pending-save-notice";
import { getUserMessage } from "@/lib/user-messages";
import { formatNairobiDateTime } from "@/lib/format-nairobi";

export default function DiscountPolicySettings() {
  const { authenticatedRequest } = useAuth();
  const save = usePendingSave("/settings/discount-policy");
  const [policy, setPolicy] = useState(null);
  const [percentage, setPercentage] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [current, changes] = await Promise.all([
        authenticatedRequest("/settings/discount-policy", { cache: "no-store" }),
        authenticatedRequest("/settings/discount-policy/history", { cache: "no-store" }),
      ]);
      setPolicy(current);
      setPercentage(String(current.employee_max_discount_percent));
      setHistory(changes);
    } catch (loadError) {
      setError(getUserMessage(loadError, "The discount policy could not be loaded."));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest]);

  useEffect(() => {
    const timer = setTimeout(load, 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function finish(current) {
    setPolicy(current);
    setPercentage(String(current.employee_max_discount_percent));
    setMessage(`Policy save confirmed. The current employee limit is ${current.employee_max_discount_percent}%.`);
    try {
      setHistory(await authenticatedRequest("/settings/discount-policy/history", { cache: "no-store" }));
    } catch (historyError) {
      setError(getUserMessage(historyError, "The policy is saved, but its history could not be refreshed."));
    }
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    const value = percentage.trim();
    if (!policy || !/^\d+(\.\d{1,2})?$/.test(value) || Number(value) > 100) {
      setError("Enter a percentage from 0 to 100 with at most two decimal places.");
      return;
    }
    try {
      await finish(await save.save({
        employee_max_discount_percent: value,
        expected_revision: policy.revision,
      }));
    } catch (saveError) {
      setError(getUserMessage(saveError));
    }
  }

  async function retry() {
    setError("");
    setMessage("");
    try { await finish(await save.retry()); }
    catch (saveError) { setError(getUserMessage(saveError)); }
  }

  return (
    <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="discount-policy-title">
      <h2 id="discount-policy-title" className="text-xl font-bold text-slate-900">Employee discount limit</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">Applies to the combined discount across the whole order, before discounts. At 0%, only an owner can give a discount. Earlier tickets keep their saved prices. Every service must still have a positive charge.</p>
      <PendingSaveNotice {...save} onRetry={retry} />
      {error ? <p className="mt-3 rounded-xl border border-red-300 bg-red-50 p-3 text-red-800" role="alert">{error}</p> : null}
      {message ? <p className="mt-3 rounded-xl border border-green-300 bg-green-50 p-3 text-green-800" role="status">{message}</p> : null}
      <form onSubmit={submit} className="mt-4" noValidate>
        <fieldset disabled={loading || save.isSaving || Boolean(save.pending) || !save.ready || !policy}>
          <label htmlFor="employee-discount-percent" className="block font-semibold text-slate-800">Maximum employee discount (%)</label>
          <input id="employee-discount-percent" className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 sm:max-w-xs" type="number" min="0" max="100" step="0.01" value={percentage} onChange={(event) => setPercentage(event.target.value)} />
          <p className="mt-2 text-sm text-slate-600">A 10% limit permits at most KES 100 on a KES 1,000 order.</p>
          <button className="mt-3 min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white disabled:opacity-60" type="submit">{save.isSaving ? "Saving…" : "Save employee limit"}</button>
        </fieldset>
      </form>
      <button className="mt-3 min-h-11 rounded-xl border border-[#005AAB] px-4 font-semibold text-[#005AAB] disabled:opacity-60" type="button" disabled={loading || save.isSaving || Boolean(save.pending)} onClick={load}>Reload limit and history</button>
      <details className="mt-4">
        <summary className="cursor-pointer font-semibold text-slate-800">Recent policy changes</summary>
        {history.length ? <ul className="mt-3 space-y-2 text-sm text-slate-700">{history.map((change) => <li key={change.id}>{change.before_percent}% → {change.after_percent}% · {change.confirmed_by_username} · {formatNairobiDateTime(change.created_at)}</li>)}</ul> : <p className="mt-2 text-sm text-slate-600">{loading ? "Loading history…" : error ? "History is unavailable. Reload to check it." : "No policy changes recorded."}</p>}
      </details>
    </section>
  );
}
