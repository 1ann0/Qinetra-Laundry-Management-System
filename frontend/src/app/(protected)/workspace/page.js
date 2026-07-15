"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth-context";

const MODULES = [
  {
    number: "02",
    title: "Customer records",
    description: "Register customers and find them quickly by name or phone.",
    phase: "Open customer registration",
    href: "/customers",
  },
  {
    number: "03",
    title: "Laundry orders",
    description: "Price services, create orders, and issue clear ticket numbers.",
    phase: "Open order entry",
    href: "/orders",
  },
  {
    number: "04",
    title: "Status tracking",
    description: "Move work through four stages and identify overdue collections.",
    phase: "Open status tracking",
    href: "/orders/status",
  },
];

export default function WorkspacePage() {
  const { role } = useAuth();

  return (
    <>
      <section className="workspace-heading">
        <p className="eyebrow">Signed in as {role}</p>
        <h1>QLMS workspace</h1>
        <p>
          The secure foundation is ready. Each operational area will be added and
          tested one phase at a time so the workflow stays easy to understand.
        </p>
      </section>

      <section className="module-grid" aria-label="QLMS roadmap modules">
        {MODULES.map((module) => (
          <article className="module-card" key={module.number}>
            <span className="module-number">{module.number}</span>
            <h2>{module.title}</h2>
            <p>{module.description}</p>
            {module.href ? (
              <Link
                className="mt-5 inline-flex text-sm font-bold text-[#005AAB] no-underline hover:underline"
                href={module.href}
              >
                {module.phase}
              </Link>
            ) : (
              <span className="phase-label">{module.phase}</span>
            )}
          </article>
        ))}
      </section>
    </>
  );
}
