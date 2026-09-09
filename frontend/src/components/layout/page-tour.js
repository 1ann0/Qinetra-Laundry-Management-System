"use client";

import { useEffect, useRef, useState } from "react";

const ORDER_TOUR_STEPS = [
  {
    targetId: "order-customer-step",
    title: "Choose the customer",
    description:
      "Search by name or phone, then select the customer whose laundry is being received.",
  },
  {
    targetId: "order-services-step",
    title: "Add services and clothing",
    description:
      "Choose Laundry or Dry Cleaning, search the catalogue and add every service on this ticket.",
  },
  {
    targetId: "order-completion-step",
    title: "Confirm the ready time",
    description:
      "Check the suggested completion time with the customer and adjust it when the shop is busy.",
  },
  {
    targetId: "order-payment-step",
    title: "Record payment",
    description:
      "Leave the order unpaid or record a confirmed Cash or M-PESA full payment or deposit.",
  },
  {
    targetId: "order-review-step",
    title: "Review and create",
    description:
      "Check the price, ready time and payment choice. Then select Create order to save the ticket.",
  },
];

const STAFF_TOUR_STEPS = [
  {
    targetId: "staff-add-step",
    title: "Create an employee login",
    description:
      "Give each employee their own username and employee password instead of sharing the owner's account.",
  },
  {
    targetId: "staff-list-step",
    title: "Review who has access",
    description:
      "Check every QLMS account and its current Active or Inactive status from one list.",
  },
  {
    targetId: "staff-security-step",
    title: "Turn access off safely",
    description:
      "Reset a forgotten password. Turn off accounts for staff who should no longer use QLMS.",
  },
];

const STATUS_TOUR_STEPS = [
  {
    targetId: "status-search-step",
    title: "Find the right order",
    description:
      "Search by ticket, customer name, phone number or service instead of reading every card.",
  },
  {
    targetId: "status-stages-step",
    title: "Choose an order stage",
    description:
      "Select View orders on a stage to see its orders below. Select View all orders to see all matches.",
  },
  {
    targetId: "status-focus-step",
    title: "See what needs attention",
    description:
      "Use the clear buttons to find work due today, late production, unpaid orders or overdue collections.",
  },
  {
    targetId: "status-board-step",
    title: "Move one step at a time",
    description:
      "Read the customer's full name and order details, then use the clear action button to move it forward by one stage.",
  },
];

// Give staff a short, real guide without adding a tour library to the project.
export default function PageTour({ pathname }) {
  const [isOpen, setIsOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const headingRef = useRef(null);
  const steps =
    pathname === "/orders"
      ? ORDER_TOUR_STEPS
      : pathname === "/orders/status"
        ? STATUS_TOUR_STEPS
      : pathname === "/staff"
        ? STAFF_TOUR_STEPS
        : [];
  const activeStep = steps[stepIndex];

  function closeTour() {
    setIsOpen(false);
    setStepIndex(0);
  }

  useEffect(() => {
    if (!isOpen || !activeStep) {
      return undefined;
    }

    const target = document.getElementById(activeStep.targetId);
    target?.classList.add("tour-highlight");
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
    headingRef.current?.focus();

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        closeTour();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      target?.classList.remove("tour-highlight");
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [activeStep, isOpen]);

  if (steps.length === 0) {
    return null;
  }

  return (
    <>
      <button
        className="page-tour-button"
        type="button"
        onClick={() => {
          setStepIndex(0);
          setIsOpen(true);
        }}
      >
        <svg
          aria-hidden="true"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M9.5 9a2.5 2.5 0 1 1 4.45 1.57c-.98.78-1.95 1.3-1.95 2.43" />
          <path d="M12 17h.01" />
          <circle cx="12" cy="12" r="9" />
        </svg>
        <span>Page tour</span>
      </button>

      {isOpen ? (
        <section
          className="page-tour-card"
          key={activeStep.targetId}
          role="dialog"
          aria-labelledby="page-tour-heading"
          aria-live="polite"
        >
          <div className="page-tour-progress">
            Step {stepIndex + 1} of {steps.length}
          </div>
          <h2
            id="page-tour-heading"
            ref={headingRef}
            tabIndex="-1"
          >
            {activeStep.title}
          </h2>
          <p>{activeStep.description}</p>

          <div className="page-tour-actions">
            <button
              className="secondary-button"
              type="button"
              disabled={stepIndex === 0}
              onClick={() => setStepIndex((current) => current - 1)}
            >
              Back
            </button>
            <button
              className="primary-button"
              type="button"
              onClick={() => {
                if (stepIndex === steps.length - 1) {
                  closeTour();
                } else {
                  setStepIndex((current) => current + 1);
                }
              }}
            >
              {stepIndex === steps.length - 1 ? "Done" : "Next"}
            </button>
          </div>
          <button
            className="page-tour-close"
            type="button"
            aria-label="Close page tour"
            onClick={closeTour}
          >
            ×
          </button>
        </section>
      ) : null}
    </>
  );
}
