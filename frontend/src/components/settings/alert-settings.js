"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";
import usePendingSave from "@/components/orders/use-pending-save";
import PendingSaveNotice from "@/components/orders/pending-save-notice";
import { alertPreferencesIssue } from "@/lib/alert-settings";
import { getUserMessage } from "@/lib/user-messages";
import { formatNairobiDateTime } from "@/lib/format-nairobi";

export default function AlertSettings() {
  const { authenticatedRequest } = useAuth();
  const save = usePendingSave("/settings/alerts");
  const [settings, setSettings] = useState(null);
  const [email, setEmail] = useState("");
  const [time, setTime] = useState("22:00");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [issue, setIssue] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const emailInput = useRef(null);
  const timeInput = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setIssue(null);
    setMessage("");
    try {
      const [current, changes] = await Promise.all([
        authenticatedRequest("/settings/alerts", { cache: "no-store" }),
        authenticatedRequest("/settings/alerts/history", { cache: "no-store" }),
      ]);
      setSettings(current);
      setEmail(current.owner_email || "");
      setTime(current.backup_time);
      setHistory(changes);
    } catch (failure) {
      setError(getUserMessage(failure, "Alert preferences could not be loaded."));
    } finally { setLoading(false); }
  }, [authenticatedRequest]);

  useEffect(() => {
    const timer = setTimeout(load, 0);
    return () => clearTimeout(timer);
  }, [load]);

  function validate(focus = false) {
    const problem = alertPreferencesIssue(email, time);
    setIssue(problem);
    if (problem && focus) {
      const input = problem.field === "email" ? emailInput.current : timeInput.current;
      input?.focus();
      input?.scrollIntoView({ block: "center", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
    return !problem;
  }

  async function finish(current) {
    setSettings(current);
    setEmail(current.owner_email || "");
    setTime(current.backup_time);
    setMessage("Preferences saved. Scheduled backups and alert delivery still need setup and verification.");
    try { setHistory(await authenticatedRequest("/settings/alerts/history", { cache: "no-store" })); }
    catch (failure) { setError(getUserMessage(failure, "Preferences are saved, but history could not be refreshed.")); }
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!settings || !validate(true)) return;
    try { await finish(await save.save({ owner_email: email.trim(), backup_time: time, expected_revision: settings.revision })); }
    catch (failure) { setError(getUserMessage(failure)); }
  }

  async function retry() {
    setError("");
    setMessage("");
    try { await finish(await save.retry()); }
    catch (failure) { setError(getUserMessage(failure)); }
  }

  const disabled = loading || save.isSaving || Boolean(save.pending) || !save.ready || !settings;
  const inputClass = "mt-2 min-h-12 w-full scroll-mt-28 rounded-xl border border-slate-300 px-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#005AAB]";
  return (
    <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="alert-settings-title">
      <h2 id="alert-settings-title" className="text-xl font-bold text-slate-900">Backup and alert preferences</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">Owner only. Choose the email for operational alerts and a preferred daily backup time. These preferences do not change your login or grant anyone access.</p>
      <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-950">Automation is not configured. Backups and email alerts will start only after their connection, delivery and recovery checks pass.</p>
      <PendingSaveNotice {...save} onRetry={retry} />
      {error ? <p className="mt-3 rounded-xl border border-red-300 bg-red-50 p-3 text-red-800" role="alert">{error}</p> : null}
      {message ? <p className="mt-3 rounded-xl border border-green-300 bg-green-50 p-3 text-green-800" role="status">{message}</p> : null}
      <form className="mt-4" onSubmit={submit} noValidate>
        <fieldset disabled={disabled}>
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="block font-semibold text-slate-800" htmlFor="owner-alert-email">Alert email</label>
              <input ref={emailInput} id="owner-alert-email" className={inputClass} type="email" autoComplete="email" maxLength={254}
                value={email} onChange={(event) => { setEmail(event.target.value); setIssue(null); }} onBlur={() => validate()}
                aria-invalid={issue?.field === "email"} aria-describedby="alert-email-help alert-email-error" />
              <p id="alert-email-help" className="mt-2 text-sm text-slate-600">Use an address you control. Mailbox delivery must be verified before alerts are activated.</p>
              <p id="alert-email-error" className="mt-2 text-sm text-red-800" role={issue?.field === "email" ? "alert" : undefined}>{issue?.field === "email" ? issue.message : ""}</p>
            </div>
            <div>
              <label className="block font-semibold text-slate-800" htmlFor="daily-backup-time">Preferred daily backup time</label>
              <input ref={timeInput} id="daily-backup-time" className={inputClass} type="time" step="60" value={time}
                onChange={(event) => { setTime(event.target.value); setIssue(null); }} onBlur={() => validate()}
                aria-invalid={issue?.field === "time"} aria-describedby="backup-time-help backup-time-error" />
              <p id="backup-time-help" className="mt-2 text-sm text-slate-600">Nairobi time (UTC+3). The initial preference is 10 pm. The scheduler must be connected before this time takes effect.</p>
              <p id="backup-time-error" className="mt-2 text-sm text-red-800" role={issue?.field === "time" ? "alert" : undefined}>{issue?.field === "time" ? issue.message : ""}</p>
            </div>
          </div>
          <button type="submit" className="mt-3 min-h-11 rounded-xl bg-[#005AAB] px-5 font-bold text-white focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60">{save.isSaving ? "Saving preferences…" : "Save preferences"}</button>
        </fieldset>
      </form>
      <button type="button" className="mt-3 min-h-11 rounded-xl border border-[#005AAB] px-4 font-semibold text-[#005AAB] focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60"
        disabled={loading || save.isSaving || Boolean(save.pending)} onClick={load}>Reload preferences and history</button>
      <details className="mt-4">
        <summary className="cursor-pointer font-semibold text-slate-800">Recent preference changes</summary>
        {history.length ? <ul className="mt-3 space-y-2 break-words text-sm text-slate-700">{history.map((change) => <li key={change.id}>{change.after_email} · {change.after_backup_time} Nairobi · {change.confirmed_by_username} · {formatNairobiDateTime(change.created_at)}</li>)}</ul>
          : <p className="mt-2 text-sm text-slate-600">{loading ? "Loading history…" : error ? "History is unavailable. Reload to check it." : "No preference changes recorded."}</p>}
      </details>
    </section>
  );
}
