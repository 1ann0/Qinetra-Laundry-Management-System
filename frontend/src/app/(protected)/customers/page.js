"use client";

import { getUserMessage } from "@/lib/user-messages";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/context/auth-context";

// Read and trim the two values submitted by the customer form.
// Keeping this separate makes the submit function easier to follow.
function readCustomerDetails(form) {
  const formData = new FormData(form);

  return {
    name: String(formData.get("name") || "").trim(),
    phone: String(formData.get("phone") || "").trim(),
  };
}

// Check the basic rules that staff can correct before contacting the backend.
// The backend remains responsible for the final database operation.
function getValidationError(customer) {
  if (!customer.name || !customer.phone) {
    return "Enter both the customer name and phone number.";
  }

  return "";
}

export default function CustomerRegistrationPage() {
  const { authenticatedRequest } = useAuth();

  // Track the result shown to the employee and whether a request is in progress.
  // Only these values need React state because the form values are read on submit.
  const [feedback, setFeedback] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate the form, send the customer to FastAPI, then explain the result.
  // A duplicate phone is a warning because the backend still creates the record.
  async function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const customer = readCustomerDetails(form);
    const validationError = getValidationError(customer);

    if (validationError) {
      setFeedback({ type: "error", message: validationError });
      return;
    }

    setFeedback(null);
    setIsSubmitting(true);

    try {
      // Send JSON through the shared authenticated request function so the JWT
      // is attached without repeating the login logic on this screen.
      const response = await authenticatedRequest("/customers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(customer),
      });

      if (response.duplicate_warning) {
        setFeedback({
          type: "warning",
          message: "Customer saved. Another customer uses this phone number. Open Customers to check the records before you create an order.",
        });
      } else {
        setFeedback({
          type: "success",
          message: `${response.customer.name} was registered successfully.`,
        });
      }

      form.reset();
    } catch (error) {
      setFeedback({
        type: "error",
        message: getUserMessage(error, "QLMS could not confirm that the customer was saved. Check Customers before you add them again."),
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  // Choose a clear colour for success, warning or error feedback.
  // The message text still explains the result without relying on colour alone.
  const feedbackStyle =
    feedback?.type === "success"
      ? "border-green-300 bg-green-50 text-green-800"
      : feedback?.type === "warning"
        ? "border-amber-300 bg-amber-50 text-amber-900"
        : "border-red-300 bg-red-50 text-red-800";

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Customers
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Register a customer
        </h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Add the customer before creating their laundry order. Both owners and
          employees can use this form.
        </p>
        <Link
          className="mt-4 inline-flex items-center gap-2 font-bold text-[#005AAB] no-underline hover:underline"
          href="/customers/search"
        >
          <svg
            aria-hidden="true"
            className="h-5 w-5 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          Search customer records
        </Link>
      </div>

      <form
        className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="mb-5">
          <label className="mb-2 block font-semibold text-slate-800" htmlFor="name">
            Customer name
          </label>
          <input
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id="name"
            name="name"
            type="text"
            maxLength={100}
            autoComplete="name"
            autoFocus
            disabled={isSubmitting}
            placeholder="Example: Jane Wanjiku"
          />
        </div>

        <div className="mb-6">
          <label className="mb-2 block font-semibold text-slate-800" htmlFor="phone">
            Phone number
          </label>
          <input
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id="phone"
            name="phone"
            type="tel"
            inputMode="tel"
            maxLength={20}
            autoComplete="tel"
            disabled={isSubmitting}
            placeholder="Example: 0712345678"
          />
          <p className="mt-2 text-sm text-slate-500">
            Use the same phone format each time so duplicate warnings are accurate.
          </p>
        </div>

        {feedback ? (
          <p
            className={`mb-6 rounded-xl border px-4 py-3 text-sm leading-6 ${feedbackStyle}`}
            role={feedback.type === "error" ? "alert" : "status"}
          >
            {feedback.message}
          </p>
        ) : null}

        <button
          className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Registering customer…" : "Register customer"}
        </button>
      </form>
    </section>
  );
}
