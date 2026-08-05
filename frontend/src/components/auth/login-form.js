"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function LoginForm() {
  const router = useRouter();
  const { isAuthenticated, isLoading, role, login } = useAuth();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Keep the password hidden by default, but let staff check what they typed.
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(role === "owner" ? "/finance" : "/workspace");
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
      router.replace(signedInRole === "owner" ? "/finance" : "/workspace");
    } catch (loginError) {
      setError(loginError.message || "Login failed. Please try again.");
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

      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in…" : "Sign in to QLMS"}
      </button>
    </form>
  );
}
