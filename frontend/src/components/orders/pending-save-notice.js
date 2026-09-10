"use client";

import { useEffect, useRef } from "react";

export default function PendingSaveNotice({ pending, storageError, isSaving, onRetry }) {
  const notice = useRef(null);
  const retryButton = useRef(null);
  // Bring recovery into view even when staff saved from the bottom of a long form.
  useEffect(() => {
    if (pending && !isSaving) {
      notice.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      retryButton.current?.focus({ preventScroll: true });
    }
  }, [pending, isSaving]);
  if (storageError) return <p className="my-4 rounded-xl border border-red-300 bg-red-50 p-4 text-red-800" role="alert">{storageError}</p>;
  if (!pending) return null;
  return (
    <section ref={notice} className="my-4 scroll-mt-24 rounded-xl border border-amber-300 bg-amber-50 p-4" aria-label="Previous save" aria-live="polite">
      <p className="font-semibold text-amber-950">
        {isSaving ? "Saving your original details…" : "Your previous save is not confirmed. Keep this tab open."}
      </p>
      <p className="mt-2 text-sm text-amber-950">Retry uses the same details and save reference. It will not add a second copy.</p>
      <button
        ref={retryButton}
        className="mt-3 min-h-11 cursor-pointer rounded-xl bg-[#005AAB] px-4 font-bold text-white focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60"
        type="button" disabled={isSaving} onClick={onRetry}
      >
        {isSaving ? "Saving…" : "Retry previous save"}
      </button>
    </section>
  );
}
