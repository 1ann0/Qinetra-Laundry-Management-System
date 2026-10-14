"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import QuickFind from "@/components/layout/quick-find";

// Keep the same everyday actions within reach for both staff roles.
const SHORTCUTS = [
  {
    title: "New order",
    description: "Record the customer's laundry, price and ready time.",
    actions: [{ label: "New order", href: "/orders" }],
  },
  {
    title: "Track orders",
    description: "Find an order, check its progress or move it to the next stage.",
    actions: [{ label: "Track orders", href: "/orders/status" }],
  },
  {
    title: "Find customer",
    description: "Search by name or phone and view the customer's past orders.",
    actions: [
      { label: "Find customer", href: "/customers/search" },
      { label: "Add customer", href: "/customers", secondary: true },
    ],
  },
  {
    title: "Owner dashboard",
    description: "See work needing attention, current balances and money received.",
    actions: [{ label: "View dashboard", href: "/dashboard" }],
    ownerOnly: true,
  },
  {
    title: "Shop setup",
    description: "Manage the services, prices and clothing names used for new orders.",
    actions: [{ label: "Shop setup", href: "/settings/catalog" }],
    ownerOnly: true,
  },
];

// Owners keep their extra shortcuts; employees see only daily work.
export default function WorkspacePage() {
  const { role } = useAuth();

  const visibleShortcuts = SHORTCUTS.filter((shortcut) => !shortcut.ownerOnly || role === "owner");

  return (
    <>
      <section className="workspace-heading">
        <p className="eyebrow">Signed in as {role}</p>
        <h1>Home</h1>
        <p>Choose what you need to do.</p>
      </section>

      <QuickFind />

      <section id="daily-shortcuts" className="module-grid" aria-label="Daily work shortcuts">
        {visibleShortcuts.map((shortcut) => (
          <article className="module-card" key={shortcut.title}>
            <div className="module-card-heading">
              <h2>{shortcut.title}</h2>
            </div>
            <p>{shortcut.description}</p>
            <div className="module-actions">
              {shortcut.actions.map((action) => (
                <Link
                  className={`inline-flex min-h-11 items-center gap-2 no-underline hover:underline ${
                    action.secondary ? "font-medium text-slate-600" : "font-bold text-[#005AAB]"
                  }`}
                  href={action.href}
                  key={action.href}
                >
                  {action.label}
                  <svg
                    aria-hidden="true"
                    className="h-5 w-5 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M5 12h14m-5-5 5 5-5 5" />
                  </svg>
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
