"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { ApiError } from "@/lib/user-messages";
import { saveScope, readPendingSave, prepareSave, sendPendingSave } from "@/lib/pending-save";

// Retain the exact request through a lost reply, refresh or password re-entry.
export default function usePendingSave(path) {
  const { userId, authenticatedRequest } = useAuth();
  const scope = saveScope(userId, path);
  const [pending, setPending] = useState(null);
  const [readyScope, setReadyScope] = useState("");
  const [storageError, setStorageError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const busy = useRef(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        setPending(readPendingSave(window.sessionStorage, scope));
        setStorageError("");
        setReadyScope(scope);
      } catch (error) {
        setStorageError(error.message);
      }
    }, 0);
    return () => clearTimeout(timer);
  }, [scope]);

  async function perform(body, retry = false) {
    if (busy.current || readyScope !== scope || !userId) {
      throw new ApiError("Wait for the current action to finish before you save.");
    }
    busy.current = true;
    setIsSaving(true);
    try {
      const attempt = retry
        ? readPendingSave(window.sessionStorage, scope)
        : prepareSave(window.sessionStorage, scope, body);
      if (!attempt) throw new ApiError("There is no previous save to retry. Check the record before you continue.");
      setPending(attempt);
      return await sendPendingSave(authenticatedRequest, window.sessionStorage, scope, path, attempt);
    } finally {
      try {
        setPending(readPendingSave(window.sessionStorage, scope));
      } catch (error) {
        setStorageError(error.message);
      }
      busy.current = false;
      setIsSaving(false);
    }
  }

  return {
    pending, storageError, isSaving, ready: readyScope === scope && !storageError,
    save: (body) => perform(body), retry: () => perform(null, true),
  };
}
