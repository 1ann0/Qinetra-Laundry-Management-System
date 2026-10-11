"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { availableHelpSteps } from "@/lib/page-help";

export default function PageTour({ pathname }) {
  const [steps, setSteps] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [message, setMessage] = useState("");
  const headingRef = useRef(null);
  const helpButtonRef = useRef(null);
  const activeStep = steps[stepIndex];

  const closeTour = useCallback(() => {
    setIsOpen(false);
    setStepIndex(0);
    helpButtonRef.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    if (!isOpen || !activeStep) return undefined;
    const target = document.getElementById(activeStep.targetId);
    target?.classList.add("tour-highlight");
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
    target?.scrollIntoView({ behavior, block: "center" });
    headingRef.current?.focus({ preventScroll: true });
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeTour();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      target?.classList.remove("tour-highlight");
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [activeStep, isOpen, closeTour]);

  if (availableHelpSteps(pathname, () => true).length === 0) return null;

  return <>
    <button ref={helpButtonRef} className="page-tour-button" type="button" aria-label="Help with this page" onClick={() => {
      const visible = availableHelpSteps(pathname, id => Boolean(document.getElementById(id)));
      setSteps(visible);
      setStepIndex(0);
      setMessage(visible.length ? "" : "This page is still loading or has no available help sections. Try Help after it opens.");
      setIsOpen(visible.length > 0);
    }}>
      <svg aria-hidden="true" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path d="M9.5 9a2.5 2.5 0 1 1 4.45 1.57c-.98.78-1.95 1.3-1.95 2.43" /><path d="M12 17h.01" /><circle cx="12" cy="12" r="9" />
      </svg><span>Help</span>
    </button>
    {message ? <p role="status" className="page-tour-card">{message}<button type="button" className="page-tour-close" aria-label="Close help message" onClick={() => { setMessage(""); helpButtonRef.current?.focus(); }}>×</button></p> : null}
    {isOpen && activeStep ? <section className="page-tour-card" key={stepIndex} role="dialog" aria-labelledby="page-tour-heading" aria-describedby="page-tour-description">
      <div className="page-tour-progress">Step {stepIndex + 1} of {steps.length}</div>
      <h2 id="page-tour-heading" ref={headingRef} tabIndex="-1">{activeStep.title}</h2>
      <p id="page-tour-description">{activeStep.description}</p>
      <div className="page-tour-actions">
        <button className="secondary-button" type="button" disabled={stepIndex === 0} onClick={() => setStepIndex(current => current - 1)}>Back</button>
        <button className="primary-button" type="button" onClick={() => stepIndex === steps.length - 1 ? closeTour() : setStepIndex(current => current + 1)}>{stepIndex === steps.length - 1 ? "Done" : "Next"}</button>
      </div>
      <button className="page-tour-close" type="button" aria-label="Close page help" onClick={closeTour}>×</button>
    </section> : null}
  </>;
}
