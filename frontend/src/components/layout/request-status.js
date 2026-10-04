"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function RequestStatus() {
  const { requestActivity } = useAuth();
  const [slowRequestId, setSlowRequestId] = useState(null);

  useEffect(() => {
    if (!requestActivity) return undefined;
    const timer = setTimeout(() => setSlowRequestId(requestActivity.id),
      Math.max(0, 8000 - (Date.now() - requestActivity.startedAt)));
    return () => clearTimeout(timer);
  }, [requestActivity]);

  if (!requestActivity) return null;
  return (
    <div className="pointer-events-none fixed top-20 left-4 right-4 z-40 rounded-xl border border-blue-200 bg-white px-4 py-3 text-sm text-blue-950 shadow-md sm:left-auto sm:max-w-sm" role="status" aria-live="polite" aria-atomic="true">
      <div className="flex items-center gap-3 font-semibold">
        <span className="h-5 w-5 shrink-0 rounded-full border-2 border-blue-200 border-t-[#005AAB] motion-safe:animate-spin" aria-hidden="true" />
        {requestActivity.label}
      </div>
      {slowRequestId === requestActivity.id ? <p className="mt-2">{requestActivity.isRead ? "This is taking longer than usual. Keep this page open." : "Still waiting for confirmation. Keep this tab open."}</p> : null}
    </div>
  );
}
