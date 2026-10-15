"use client";

import { getUserMessage } from "@/lib/user-messages";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { checkApiReadiness } from "@/lib/api";

export default function LoginForm() {
  const router = useRouter();
  const { isAuthenticated, isLoading, role, login } = useAuth();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [startup, setStartup] = useState("connecting");

  // Keep the password hidden by default, but let staff check what they typed.
  const [showPassword, setShowPassword] = useState(false);

  // Wake the free API while staff type; never poll or block credential submission.
  useEffect(() => {
    if (isLoading || isAuthenticated) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(() => setStartup("waking"), 8000);
    checkApiReadiness({ signal: controller.signal }).then(
      () => { if (!controller.signal.aborted) setStartup("ready"); },
      () => { if (!controller.signal.aborted) setStartup("unavailable"); },
    ).finally(() => clearTimeout(timer));
    return () => { controller.abort(); clearTimeout(timer); };
  }, [isAuthenticated, isLoading]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(role === "owner" ? "/dashboard" : "/workspace");
    }
  }, [isAuthenticated, isLoading, role, router]);

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const username = String(formData.get("username") || "").trim();
    const password = String(formData.get("password") || "");

    if (!username || !password) {
      setError("Enter both your username and password.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      const signedInRole = await login(username, password);
      router.replace(signedInRole === "owner" ? "/dashboard" : "/workspace");
    } catch (loginError) {
      setError(getUserMessage(loginError, "QLMS could not sign you in."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-field">
        <label htmlFor="username">Username</label>
        <input
          id="username"
          name="username"
          type="text"
          autoComplete="username"
          autoFocus
          disabled={isSubmitting}
        />
      </div>

      <div className="form-field">
        <label htmlFor="password">Password</label>
        <div className="password-input-row">
          <input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            disabled={isSubmitting}
          />
          <button
            className="password-toggle"
            type="button"
            aria-pressed={showPassword}
            onClick={() => setShowPassword((currentValue) => !currentValue)}
            disabled={isSubmitting}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}

      <button className="primary-button gap-3" type="submit" disabled={isSubmitting} aria-busy={isSubmitting} aria-label={isSubmitting ? "Signing in…" : "Sign in to QLMS"}>
        {isSubmitting ? <span className="h-5 w-5 shrink-0 rounded-full border-2 border-white/40 border-t-white motion-safe:animate-spin" aria-hidden="true" /> : null}
        <span role="status" aria-live="polite">
        {isSubmitting ? "Signing in…" : "Sign in to QLMS"}
        </span>
      </button>
      <p className="login-server-status" role="status" aria-live="polite" aria-atomic="true">
        {isSubmitting ? "Keep this page open. Connecting can take up to two minutes after QLMS has been idle."
          : startup === "ready" ? "Ready to sign in."
          : startup === "unavailable" ? "QLMS is not reachable yet. Check your internet, then try Sign in."
          : startup === "waking" ? "QLMS may be waking up. You can enter your details while it connects."
          : "Connecting to QLMS… You can enter your sign-in details."}
      </p>
    </form>
  );
}
