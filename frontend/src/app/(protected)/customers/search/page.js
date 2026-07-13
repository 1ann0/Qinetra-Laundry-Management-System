"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function CustomerSearchPage() {
  const { authenticatedRequest } = useAuth();

  // Keep the returned customers and the current search status on this page.
  const [customers, setCustomers] = useState([]);
  const [lastSearch, setLastSearch] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Submit one search request when the employee presses the button.
  // Leaving the field blank asks the backend to return all customers.
  async function handleSearch(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const search = String(formData.get("search") || "").trim();
    const path = search
      ? `/customers?search=${encodeURIComponent(search)}`
      : "/customers";

    setError("");
    setHasSearched(false);
    setIsLoading(true);

    try {
      // Use the shared request function so the JWT is sent with the search.
      const response = await authenticatedRequest(path);

      setCustomers(response);
      setLastSearch(search);
      setHasSearched(true);
    } catch (searchError) {
      setCustomers([]);
      setError(searchError.message || "Customer search failed. Try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="mx-auto max-w-5xl">
      <div className="mb-8">
        <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#005AAB]">
          Customer module
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Find a customer
        </h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Search by part of a customer name or phone number. Leave the field
          blank to view all customer records.
        </p>
        <Link
          className="mt-4 inline-flex font-bold text-[#005AAB] no-underline hover:underline"
          href="/customers"
        >
          Register a new customer
        </Link>
      </div>

      <form
        className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
        onSubmit={handleSearch}
      >
        <label className="mb-2 block font-semibold text-slate-800" htmlFor="search">
          Customer name or phone
        </label>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="min-h-12 flex-1 rounded-xl border border-slate-300 px-4 text-slate-900 outline-none focus:border-[#005AAB] focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100"
            id="search"
            name="search"
            type="search"
            maxLength={100}
            autoFocus
            disabled={isLoading}
            placeholder="Example: Jane or 0712"
          />
          <button
            className="inline-flex min-h-12 items-center justify-center rounded-xl bg-[#005AAB] px-6 font-bold text-white hover:bg-[#004782] disabled:cursor-wait disabled:opacity-60"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? "Searching…" : "Search customers"}
          </button>
        </div>
      </form>

      {error ? (
        <p
          className="mt-6 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {hasSearched ? (
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <h2 className="text-xl font-bold text-slate-900">
              {lastSearch ? `Results for “${lastSearch}”` : "All customers"}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {customers.length} {customers.length === 1 ? "record" : "records"} found
            </p>
          </div>

          {customers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead className="bg-slate-50 text-sm text-slate-600">
                  <tr>
                    <th className="px-6 py-3 font-semibold" scope="col">
                      ID
                    </th>
                    <th className="px-6 py-3 font-semibold" scope="col">
                      Customer name
                    </th>
                    <th className="px-6 py-3 font-semibold" scope="col">
                      Phone number
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {customers.map((customer) => (
                    <tr className="text-slate-800" key={customer.id}>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-500">
                        {customer.id}
                      </td>
                      <td className="px-6 py-4 font-semibold">{customer.name}</td>
                      <td className="whitespace-nowrap px-6 py-4">{customer.phone}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-6 py-10 text-center text-slate-600">
              No customers matched this search.
            </p>
          )}
        </div>
      ) : null}
    </section>
  );
}
