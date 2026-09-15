"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import CustomerForm from "@/components/customers/customer-form";

export default function CustomerRegistrationPage() {
  const router = useRouter();
  const [savedCustomer, setSavedCustomer] = useState(null);

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Customers
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Add customer
        </h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          QLMS checks the phone number before saving so staff can avoid an
          accidental duplicate.
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
          Find a customer
        </Link>
      </div>

      <CustomerForm
        onSaved={(customer) => setSavedCustomer(customer)}
        onUseExisting={(customer) =>
          router.push(`/orders?customerId=${customer.id}`)
        }
      />

      {savedCustomer ? (
        <div className="mt-5 rounded-xl border border-green-300 bg-green-50 p-4">
          <p className="font-bold text-green-900">
            {savedCustomer.name} is ready for a new order.
          </p>
          <Link
            className="mt-3 inline-flex min-h-11 items-center rounded-lg bg-[#005AAB] px-5 font-bold text-white no-underline hover:bg-[#004782]"
            href={`/orders?customerId=${savedCustomer.id}`}
          >
            Create their order
          </Link>
        </div>
      ) : null}
    </section>
  );
}
