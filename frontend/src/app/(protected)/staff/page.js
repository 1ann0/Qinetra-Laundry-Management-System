"use client";

import { getUserMessage } from "@/lib/user-messages";

import { useCallback, useEffect, useMemo, useState } from "react";
import OwnerGuard from "@/components/auth/owner-guard";
import { useAuth } from "@/context/auth-context";

function sortAccounts(accounts) {
  return [...accounts].sort((first, second) => {
    if (first.role !== second.role) {
      return first.role === "owner" ? -1 : 1;
    }
    return first.username.localeCompare(second.username);
  });
}

function formatCreatedDate(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeZone: "Africa/Nairobi",
  }).format(date);
}

function getPasswordValidationError(password) {
  if (password.length < 8) {
    return "Password must contain at least 8 characters.";
  }

  if (new TextEncoder().encode(password).length > 72) {
    return "Password must be no more than 72 bytes. Use fewer special characters.";
  }

  return "";
}

function StaffManagementContent() {
  const { authenticatedRequest, userId } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [busyAction, setBusyAction] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [passwordResetAccountId, setPasswordResetAccountId] = useState(null);
  const [showResetPasswords, setShowResetPasswords] = useState(false);

  const loadAccounts = useCallback(async () => {
    setIsLoading(true);
    setLoadError("");

    try {
      const response = await authenticatedRequest("/users");
      setAccounts(sortAccounts(response));
    } catch (error) {
      setLoadError(getUserMessage(error, "Staff accounts could not be loaded."));
    } finally {
      setIsLoading(false);
    }
  }, [authenticatedRequest]);

  useEffect(() => {
    let ignoreResponse = false;

    async function loadInitialAccounts() {
      try {
        const response = await authenticatedRequest("/users");
        if (!ignoreResponse) {
          setAccounts(sortAccounts(response));
        }
      } catch (error) {
        if (!ignoreResponse) {
          setLoadError(getUserMessage(error, "Staff accounts could not be loaded."));
        }
      } finally {
        if (!ignoreResponse) {
          setIsLoading(false);
        }
      }
    }

    loadInitialAccounts();
    return () => {
      ignoreResponse = true;
    };
  }, [authenticatedRequest]);

  const accountSummary = useMemo(() => {
    const employees = accounts.filter((account) => account.role === "employee");
    return {
      total: accounts.length,
      activeEmployees: employees.filter((account) => account.is_active).length,
      inactiveEmployees: employees.filter((account) => !account.is_active).length,
    };
  }, [accounts]);

  async function handleCreateEmployee(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const username = String(formData.get("username") || "").trim();
    const password = String(formData.get("password") || "");
    const confirmPassword = String(formData.get("confirmPassword") || "");

    if (username.length < 3 || username.length > 50) {
      setFeedback({
        type: "error",
        message: "Username must be between 3 and 50 characters.",
      });
      return;
    }

    const passwordError = getPasswordValidationError(password);
    if (passwordError) {
      setFeedback({
        type: "error",
        message: passwordError,
      });
      return;
    }

    if (password !== confirmPassword) {
      setFeedback({ type: "error", message: "The passwords do not match." });
      return;
    }

    setIsCreating(true);
    setFeedback(null);

    try {
      const createdAccount = await authenticatedRequest("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, role: "employee" }),
      });

      setAccounts((current) => sortAccounts([...current, createdAccount]));
      setFeedback({
        type: "success",
        message: `${createdAccount.username}'s employee account is ready to use.`,
      });
      setShowPasswords(false);
      form.reset();
    } catch (error) {
      setFeedback({
        type: "error",
        message: getUserMessage(error, "QLMS could not confirm the new account. Check Staff before you add it again."),
      });
    } finally {
      setIsCreating(false);
    }
  }

  async function handleStatusChange(account) {
    const nextActiveState = !account.is_active;
    const action = nextActiveState ? "reactivate" : "deactivate";
    const explanation = nextActiveState
      ? "They will be able to sign in again with their current password."
      : "They will no longer be able to sign in or load more shop records.";

    if (
      !window.confirm(
        `${action[0].toUpperCase()}${action.slice(1)} ${account.username}?\n\n${explanation}`,
      )
    ) {
      return;
    }

    setBusyAction(`status-${account.id}`);
    setFeedback(null);

    try {
      const updatedAccount = await authenticatedRequest(
        `/users/${account.id}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: nextActiveState }),
        },
      );

      setAccounts((current) =>
        sortAccounts(
          current.map((savedAccount) =>
            savedAccount.id === updatedAccount.id
              ? updatedAccount
              : savedAccount,
          ),
        ),
      );
      setFeedback({
        type: "success",
        message: `${updatedAccount.username} is now ${
          updatedAccount.is_active ? "active" : "inactive"
        }.`,
      });
      setPasswordResetAccountId(null);
      setShowResetPasswords(false);
    } catch (error) {
      setFeedback({
        type: "error",
        message: getUserMessage(error, `The account could not be ${action}d.`),
      });
    } finally {
      setBusyAction("");
    }
  }

  function openPasswordReset(accountId) {
    setPasswordResetAccountId((current) =>
      current === accountId ? null : accountId,
    );
    setShowResetPasswords(false);
    setFeedback(null);
  }

  async function handlePasswordReset(event, account) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const password = String(formData.get("newPassword") || "");
    const confirmPassword = String(formData.get("confirmNewPassword") || "");
    const passwordError = getPasswordValidationError(password);

    if (passwordError) {
      setFeedback({ type: "error", message: passwordError });
      return;
    }

    if (password !== confirmPassword) {
      setFeedback({ type: "error", message: "The new passwords do not match." });
      return;
    }

    if (
      !window.confirm(
        `Reset ${account.username}'s password?\n\nThey must sign in again with the new password. Give the new password only to this employee.`,
      )
    ) {
      return;
    }

    setBusyAction(`password-${account.id}`);
    setFeedback(null);

    try {
      await authenticatedRequest(`/users/${account.id}/password`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      form.reset();
      setPasswordResetAccountId(null);
      setShowResetPasswords(false);
      setFeedback({
        type: "success",
        message: `${account.username}'s password was reset. Give the new password to this employee so they can sign in again.`,
      });
    } catch (error) {
      setFeedback({
        type: "error",
        message: getUserMessage(error, "The password could not be reset."),
      });
    } finally {
      setBusyAction("");
    }
  }

  const feedbackClasses =
    feedback?.type === "success"
      ? "border-green-300 bg-green-50 text-green-800"
      : "border-red-300 bg-red-50 text-red-800";

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-7">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Account safety
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Staff accounts
        </h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">
          Give every employee their own QLMS login, then turn access off as soon
          as they no longer need it. This page is available to owners only.
        </p>
      </div>

      <section
        className="mb-7 rounded-2xl border border-blue-200 bg-blue-50 p-5 sm:flex sm:items-start sm:justify-between sm:gap-6"
        id="staff-security-step"
      >
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Separate staff accounts protect shop records
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
            QLMS pauses after 30 minutes without activity. A warning appears two
            minutes before the pause. Staff enter their password to continue.
            An inactive account cannot sign in or load more shop records.
          </p>
        </div>
        <span className="mt-4 inline-flex shrink-0 rounded-full bg-[#005AAB] px-3 py-1.5 text-xs font-bold text-white sm:mt-0">
          Owner only
        </span>
      </section>

      {feedback ? (
        <p
          className={`mb-6 rounded-xl border px-4 py-3 text-sm leading-6 ${feedbackClasses}`}
          role={feedback.type === "error" ? "alert" : "status"}
        >
          {feedback.message}
        </p>
      ) : null}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(280px,0.85fr)_minmax(0,1.4fr)]">
        <form
          className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7"
          id="staff-add-step"
          onSubmit={handleCreateEmployee}
          noValidate
        >
          <h2 className="text-xl font-bold text-slate-900">Add an employee</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Create a separate login for one staff member. Employee accounts
            cannot open Finance, Dashboard, Staff or Shop setup.
          </p>

          <label
            className="mt-6 block font-semibold text-slate-800"
            htmlFor="employee-username"
          >
            Username
          </label>
          <input
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id="employee-username"
            name="username"
            type="text"
            minLength={3}
            maxLength={50}
            autoComplete="off"
            disabled={isCreating}
            placeholder="Example: mary"
          />
          <p className="mt-2 text-xs leading-5 text-slate-500">
            Use 3–50 characters and choose a name the employee will remember.
          </p>

          <label
            className="mt-5 block font-semibold text-slate-800"
            htmlFor="employee-password"
          >
            Employee password
          </label>
          <input
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id="employee-password"
            name="password"
            type={showPasswords ? "text" : "password"}
            minLength={8}
            maxLength={72}
            autoComplete="new-password"
            disabled={isCreating}
          />
          <p className="mt-2 text-xs leading-5 text-slate-500">
            Use 8–72 characters and give this password only to this employee.
          </p>

          <label
            className="mt-5 block font-semibold text-slate-800"
            htmlFor="employee-confirm-password"
          >
            Confirm password
          </label>
          <input
            className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id="employee-confirm-password"
            name="confirmPassword"
            type={showPasswords ? "text" : "password"}
            minLength={8}
            maxLength={72}
            autoComplete="new-password"
            disabled={isCreating}
          />

          <label className="mt-4 flex cursor-pointer items-center gap-3 text-sm font-semibold text-slate-700">
            <input
              className="h-4 w-4 accent-[#005AAB]"
              type="checkbox"
              checked={showPasswords}
              disabled={isCreating}
              onChange={(event) => setShowPasswords(event.target.checked)}
            />
            Show passwords
          </label>

          <button
            className="mt-6 inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
            type="submit"
            disabled={isCreating}
          >
            {isCreating ? "Creating account…" : "Create employee account"}
          </button>
        </form>

        <section
          className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7"
          id="staff-list-step"
          aria-labelledby="staff-list-heading"
        >
          <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900" id="staff-list-heading">
                Who can use QLMS
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {accountSummary.activeEmployees} active and{" "}
                {accountSummary.inactiveEmployees} inactive employee
                {accountSummary.activeEmployees + accountSummary.inactiveEmployees === 1
                  ? ""
                  : "s"}
                .
              </p>
            </div>
            <span className="inline-flex w-fit rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700">
              {accountSummary.total} total account
              {accountSummary.total === 1 ? "" : "s"}
            </span>
          </div>

          {loadError ? (
            <div className="mt-5 rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-800" role="alert">
              <p>{loadError}</p>
              <button
                className="mt-3 font-bold text-red-800 underline underline-offset-2"
                type="button"
                onClick={loadAccounts}
              >
                Try again
              </button>
            </div>
          ) : isLoading ? (
            <p className="py-10 text-center text-slate-600" role="status">
              Loading staff accounts…
            </p>
          ) : accounts.length === 0 ? (
            <p className="mt-5 rounded-xl border border-dashed border-slate-300 p-5 text-sm text-slate-600">
              No accounts were returned. Create the first employee using the form.
            </p>
          ) : (
            <ul className="divide-y divide-slate-200" aria-label="QLMS accounts">
              {accounts.map((account) => {
                const isCurrentAccount = account.id === userId;
                const isEmployee = account.role === "employee";
                const isStatusBusy = busyAction === `status-${account.id}`;
                const isPasswordBusy = busyAction === `password-${account.id}`;
                const isResetOpen = passwordResetAccountId === account.id;

                return (
                  <li className="py-5" key={account.id}>
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="break-all font-bold text-slate-900">
                            {account.username}
                          </h3>
                          {isCurrentAccount ? (
                            <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-bold text-[#005AAB]">
                              You
                            </span>
                          ) : null}
                          <span
                            className={`rounded-full px-2 py-1 text-xs font-bold ${
                              account.is_active
                                ? "bg-green-100 text-green-800"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {account.is_active ? "Active" : "Inactive"}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-slate-600">
                          <span className="capitalize">{account.role}</span>
                          {" · "}Added {formatCreatedDate(account.created_at)}
                        </p>
                      </div>

                      {isEmployee ? (
                        <div className="flex flex-wrap gap-2">
                          <button
                            className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl border border-slate-300 px-4 font-bold text-slate-700 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60"
                            type="button"
                            aria-controls={`password-reset-${account.id}`}
                            aria-expanded={isResetOpen}
                            disabled={Boolean(busyAction)}
                            onClick={() => openPasswordReset(account.id)}
                          >
                            {isPasswordBusy ? "Saving…" : "Reset password"}
                          </button>
                          <button
                            className={`inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl border px-4 font-bold disabled:cursor-wait disabled:opacity-60 ${
                              account.is_active
                                ? "border-red-300 text-red-700 hover:bg-red-50"
                                : "border-[#005AAB] text-[#005AAB] hover:bg-blue-50"
                            }`}
                            type="button"
                            disabled={Boolean(busyAction)}
                            onClick={() => handleStatusChange(account)}
                          >
                            {isStatusBusy
                              ? "Saving…"
                              : account.is_active
                                ? "Deactivate"
                                : "Reactivate"}
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs font-semibold text-slate-500">
                          Protected owner
                        </span>
                      )}
                    </div>

                    {isEmployee && isResetOpen ? (
                      <form
                        className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4"
                        id={`password-reset-${account.id}`}
                        onSubmit={(event) => handlePasswordReset(event, account)}
                        noValidate
                      >
                        <h4 className="font-bold text-slate-900">
                          Reset {account.username}&apos;s password
                        </h4>
                        <p className="mt-1 text-sm leading-5 text-slate-600">
                          After you save the new password, the employee must
                          sign in again.
                        </p>
                        <div className="mt-4 grid gap-4 sm:grid-cols-2">
                          <div>
                            <label
                              className="block text-sm font-semibold text-slate-800"
                              htmlFor={`new-password-${account.id}`}
                            >
                              New password
                            </label>
                            <input
                              className="mt-2 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                              id={`new-password-${account.id}`}
                              name="newPassword"
                              type={showResetPasswords ? "text" : "password"}
                              minLength={8}
                              maxLength={72}
                              autoComplete="new-password"
                              disabled={isPasswordBusy}
                            />
                          </div>
                          <div>
                            <label
                              className="block text-sm font-semibold text-slate-800"
                              htmlFor={`confirm-new-password-${account.id}`}
                            >
                              Confirm new password
                            </label>
                            <input
                              className="mt-2 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                              id={`confirm-new-password-${account.id}`}
                              name="confirmNewPassword"
                              type={showResetPasswords ? "text" : "password"}
                              minLength={8}
                              maxLength={72}
                              autoComplete="new-password"
                              disabled={isPasswordBusy}
                            />
                          </div>
                        </div>
                        <label className="mt-3 flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-700">
                          <input
                            className="h-4 w-4 accent-[#005AAB]"
                            type="checkbox"
                            checked={showResetPasswords}
                            disabled={isPasswordBusy}
                            onChange={(event) =>
                              setShowResetPasswords(event.target.checked)
                            }
                          />
                          Show new password
                        </label>
                        <div className="mt-4 flex flex-wrap gap-3">
                          <button
                            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#005AAB] px-4 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
                            type="submit"
                            disabled={Boolean(busyAction)}
                          >
                            {isPasswordBusy ? "Saving…" : "Save new password"}
                          </button>
                          <button
                            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 px-4 font-bold text-slate-700 hover:bg-white disabled:opacity-60"
                            type="button"
                            disabled={Boolean(busyAction)}
                            onClick={() => openPasswordReset(account.id)}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </section>
  );
}

export default function StaffPage() {
  return (
    <OwnerGuard>
      <StaffManagementContent />
    </OwnerGuard>
  );
}
