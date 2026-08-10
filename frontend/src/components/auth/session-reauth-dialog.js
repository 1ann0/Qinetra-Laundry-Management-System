"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function SessionReauthenticationDialog() {
  const router = useRouter();
  const {
    username,
    reauthenticationMessage,
    reauthenticate,
    logout,
  } = useAuth();
  const dialogRef = useRef(null);
  const passwordRef = useRef(null);
  const logoutButtonRef = useRef(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    if (username) {
      passwordRef.current?.focus();
    } else {
      logoutButtonRef.current?.focus();
    }

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [username]);

  function keepFocusInside(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      return;
    }

    if (event.key !== "Tab") {
      return;
    }

    const controls = dialogRef.current?.querySelectorAll(
      'input:not([disabled]):not([tabindex="-1"]), button:not([disabled]):not([tabindex="-1"])',
    );

    if (!controls?.length) {
      return;
    }

    const firstControl = controls[0];
    const lastControl = controls[controls.length - 1];

    if (event.shiftKey && document.activeElement === firstControl) {
      event.preventDefault();
      lastControl.focus();
    } else if (!event.shiftKey && document.activeElement === lastControl) {
      event.preventDefault();
      firstControl.focus();
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const password = String(new FormData(form).get("password") || "");

    if (!password) {
      setError("Enter your password to continue.");
      passwordRef.current?.focus();
      return;
    }

    setIsSubmitting(true);
    setError("");
    let shouldRefocusPassword = false;

    try {
      await reauthenticate(password);
      form.reset();
    } catch (loginError) {
      form.reset();
      setError(
        `${loginError.message || "QLMS could not confirm your password."} If this account was deactivated, ask the owner about your access.`,
      );
      shouldRefocusPassword = true;
    } finally {
      setIsSubmitting(false);
      if (shouldRefocusPassword) {
        window.requestAnimationFrame(() => passwordRef.current?.focus());
      }
    }
  }

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="fixed inset-0 z-[100] overflow-y-auto bg-slate-950/90 p-4 backdrop-blur-sm">
      <div className="flex min-h-full items-center justify-center py-6">
        <section
          className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl sm:p-8"
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="reauthentication-heading"
          aria-describedby="reauthentication-description"
          onKeyDown={keepFocusInside}
        >
          <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-[#005AAB]">
            <svg
              aria-hidden="true"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <rect x="5" y="10" width="14" height="11" rx="2" />
              <path d="M8 10V7a4 4 0 0 1 8 0v3" />
            </svg>
          </div>
          <h2
            className="text-2xl font-bold tracking-tight text-slate-900"
            id="reauthentication-heading"
          >
            Session paused — login required
          </h2>
          <p
            className="mt-3 text-sm leading-6 text-slate-600"
            id="reauthentication-description"
          >
            {reauthenticationMessage} Your open page and unsaved entries remain
            in place while you sign in again.
          </p>

          <form className="mt-6" onSubmit={handleSubmit} noValidate>
            <label className="block font-semibold text-slate-800" htmlFor="reauth-username">
              Username
            </label>
            <input
              className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 bg-slate-100 px-4 font-semibold text-slate-700"
              id="reauth-username"
              type="text"
              value={username || "Username unavailable"}
              readOnly
              tabIndex={-1}
            />

            <label className="mt-5 block font-semibold text-slate-800" htmlFor="reauth-password">
              Password
            </label>
            <div className="mt-2 grid grid-cols-[minmax(0,1fr)_auto] gap-2">
              <input
                className="min-h-12 min-w-0 rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100"
                id="reauth-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                ref={passwordRef}
                disabled={isSubmitting || !username}
              />
              <button
                className="min-h-12 rounded-xl border border-slate-300 px-4 font-bold text-[#005AAB] hover:bg-blue-50 disabled:opacity-60"
                type="button"
                aria-pressed={showPassword}
                disabled={isSubmitting || !username}
                onClick={() => setShowPassword((current) => !current)}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>

            {error ? (
              <p
                className="mt-4 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800"
                role="alert"
              >
                {error}
              </p>
            ) : null}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row-reverse">
              <button
                className="inline-flex min-h-12 flex-1 items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
                type="submit"
                disabled={isSubmitting || !username}
              >
                {isSubmitting ? "Checking…" : "Continue where I left off"}
              </button>
              <button
                className="inline-flex min-h-12 items-center justify-center rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                type="button"
                ref={logoutButtonRef}
                disabled={isSubmitting}
                onClick={handleLogout}
              >
                Log out
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}
