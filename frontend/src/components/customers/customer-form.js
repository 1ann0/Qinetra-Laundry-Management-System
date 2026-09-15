"use client";

import { useId, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { getUserMessage } from "@/lib/user-messages";

function customerDetails(name, phone, allowDuplicate = false) {
  return {
    name: name.trim(),
    phone: phone.trim(),
    allow_duplicate: allowDuplicate,
  };
}

export default function CustomerForm({
  onSaved,
  onUseExisting,
  onCancel,
  compact = false,
}) {
  const { authenticatedRequest } = useAuth();
  const fieldId = useId();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [matches, setMatches] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function resetForm() {
    setName("");
    setPhone("");
    setMatches([]);
  }

  async function findPhoneMatches() {
    return authenticatedRequest(
      `/customers/phone-match?phone=${encodeURIComponent(phone.trim())}`,
    );
  }

  async function saveCustomer(allowDuplicate) {
    const response = await authenticatedRequest("/customers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(customerDetails(name, phone, allowDuplicate)),
    });
    resetForm();
    setFeedback({
      type: response.duplicate_warning ? "warning" : "success",
      message: response.duplicate_warning
        ? "A separate customer record was saved with this shared phone number."
        : `${response.customer.name} was saved.`,
    });
    onSaved?.(response.customer, response.duplicate_warning || "");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!name.trim() || !phone.trim()) {
      setFeedback({
        type: "error",
        message: "Enter the customer name and phone number.",
      });
      return;
    }

    setFeedback(null);
    setMatches([]);
    setIsSubmitting(true);
    try {
      const phoneMatches = await findPhoneMatches();
      if (phoneMatches.length > 0) {
        setMatches(phoneMatches);
        setFeedback({
          type: "warning",
          message: "This phone number is already in use. Choose the matching customer, or create a separate record if people share the number.",
        });
        return;
      }
      await saveCustomer(false);
    } catch (error) {
      // A second staff member may save this number after the first check.
      if (error?.status === 409) {
        try {
          const phoneMatches = await findPhoneMatches();
          setMatches(phoneMatches);
          setFeedback({
            type: "warning",
            message: "This phone number was just saved. Choose the matching customer, or create a separate record if people share the number.",
          });
          return;
        } catch {
          // Use the original save error if the follow-up check also fails.
        }
      }
      setFeedback({
        type: "error",
        message: getUserMessage(error, "QLMS could not save this customer."),
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function createSeparateCustomer() {
    setIsSubmitting(true);
    try {
      await saveCustomer(true);
    } catch (error) {
      setFeedback({
        type: "error",
        message: getUserMessage(error, "QLMS could not save this customer."),
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  function selectExistingCustomer(customer) {
    resetForm();
    setFeedback(null);
    onUseExisting?.(customer);
  }

  const feedbackStyle =
    feedback?.type === "success"
      ? "border-green-300 bg-green-50 text-green-800"
      : feedback?.type === "warning"
        ? "border-amber-300 bg-amber-50 text-amber-950"
        : "border-red-300 bg-red-50 text-red-800";

  return (
    <form
      className={
        compact
          ? "rounded-2xl border border-blue-200 bg-blue-50/40 p-5"
          : "rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
      }
      onSubmit={handleSubmit}
      noValidate
    >
      {compact ? (
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Add customer</h2>
            <p className="mt-1 text-sm text-slate-600">
              The current order details will stay on this page.
            </p>
          </div>
          {onCancel ? (
            <button
              className="min-h-10 rounded-lg border border-slate-300 bg-white px-4 text-sm font-bold text-slate-700 hover:bg-slate-50"
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          ) : null}
        </div>
      ) : null}

      <div className={compact ? "grid gap-4 sm:grid-cols-2" : "space-y-5"}>
        <div>
          <label className="mb-2 block font-semibold text-slate-800" htmlFor={`${fieldId}-name`}>
            Customer name
          </label>
          <input
            className="min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id={`${fieldId}-name`}
            type="text"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setMatches([]);
              setFeedback(null);
            }}
            minLength={2}
            maxLength={100}
            autoComplete="name"
            autoFocus
            disabled={isSubmitting}
            placeholder="Example: Jane Wanjiku"
          />
        </div>

        <div>
          <label className="mb-2 block font-semibold text-slate-800" htmlFor={`${fieldId}-phone`}>
            Kenyan mobile number
          </label>
          <input
            className="min-h-12 w-full rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id={`${fieldId}-phone`}
            type="tel"
            value={phone}
            onChange={(event) => {
              setPhone(event.target.value);
              setMatches([]);
              setFeedback(null);
            }}
            maxLength={20}
            autoComplete="tel"
            inputMode="tel"
            disabled={isSubmitting}
            placeholder="Example: 0712 345 678"
          />
        </div>
      </div>

      {feedback ? (
        <p
          className={`mt-5 rounded-xl border px-4 py-3 text-sm leading-6 ${feedbackStyle}`}
          role={feedback.type === "error" ? "alert" : "status"}
        >
          {feedback.message}
        </p>
      ) : null}

      {matches.length > 0 ? (
        <div className="mt-5 rounded-xl border border-amber-300 bg-white p-4">
          <h3 className="font-bold text-slate-900">Customers using this number</h3>
          <div className="mt-3 space-y-3">
            {matches.map((customer) => (
              <div
                className="flex flex-col gap-3 rounded-lg border border-slate-200 p-3 sm:flex-row sm:items-center sm:justify-between"
                key={customer.id}
              >
                <div>
                  <p className="font-bold text-slate-900">{customer.name}</p>
                  <p className="text-sm text-slate-600">{customer.phone}</p>
                </div>
                <button
                  className="min-h-10 rounded-lg border border-[#005AAB] px-4 text-sm font-bold text-[#005AAB] hover:bg-blue-50"
                  type="button"
                  onClick={() => selectExistingCustomer(customer)}
                  disabled={isSubmitting || !onUseExisting}
                >
                  Use this customer
                </button>
              </div>
            ))}
          </div>
          <button
            className="mt-4 min-h-11 rounded-lg border border-amber-500 bg-amber-50 px-4 text-sm font-bold text-amber-950 hover:bg-amber-100 disabled:cursor-wait disabled:opacity-60"
            type="button"
            onClick={createSeparateCustomer}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Saving…" : "Create separate customer"}
          </button>
        </div>
      ) : (
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            className="inline-flex min-h-12 items-center justify-center rounded-xl bg-[#005AAB] px-5 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Checking…" : "Save customer"}
          </button>
          {!compact && onCancel ? (
            <button
              className="min-h-12 rounded-xl border border-slate-300 px-5 font-bold text-slate-700 hover:bg-slate-50"
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          ) : null}
        </div>
      )}
    </form>
  );
}
