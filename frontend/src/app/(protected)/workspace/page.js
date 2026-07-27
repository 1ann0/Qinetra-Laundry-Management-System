"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth-context";

// List the real tasks available from the workspace instead of development phases.
const MODULES = [
  {
    number: "01",
    title: "Customers",
    description: "Add a new customer or find an existing record before creating an order.",
    actions: [
      { label: "Register customer", href: "/customers" },
      { label: "Search customers", href: "/customers/search" },
    ],
  },
  {
    number: "02",
    title: "Create order",
    description: "Choose a customer and service, then let QLMS confirm the price and create the ticket.",
    actions: [{ label: "Open order entry", href: "/orders" }],
  },
  {
    number: "03",
    title: "Track orders",
    description: "View every order, move it to the next stage and check overdue collections.",
    actions: [{ label: "Open status tracking", href: "/orders/status" }],
  },
  {
    number: "04",
    title: "Owner dashboard",
    description: "Review order totals and open the page used to download the CSV report.",
    actions: [{ label: "Open owner dashboard", href: "/dashboard" }],
    ownerOnly: true,
  },
  {
    number: "05",
    title: "Shop setup",
    description: "Manage the services, prices and clothing names used for new orders.",
    actions: [{ label: "Open shop setup", href: "/settings/catalog" }],
    ownerOnly: true,
  },
];

// Show the central feature list allowed for the signed-in role.
export default function WorkspacePage() {
  const { role } = useAuth();

  // Employees see daily operations, while the owner also sees reporting tools.
  const visibleModules = MODULES.filter((module) => !module.ownerOnly || role === "owner");

  return (
    <>
      <section className="workspace-heading">
        <p className="eyebrow">Signed in as {role}</p>
        <h1>QLMS workspace</h1>
        <p>
          Everything needed for daily work is in one place; manage customers,
          create orders and follow each load through to collection.
        </p>
      </section>

      <section className="module-grid" aria-label="QLMS features">
        {visibleModules.map((module) => (
          <article className="module-card" key={module.number}>
            <div className="module-card-heading">
              <span className="module-number">{module.number}</span>
              <h2>{module.title}</h2>
            </div>
            <p>{module.description}</p>
            <div className="module-actions">
              {module.actions.map((action) => (
                <Link
                  className="inline-flex items-center gap-2 font-bold text-[#005AAB] no-underline hover:underline"
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
