"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { ApiError, apiRequest, loginRequest } from "@/lib/api";
import {
  clearStoredSession,
  readStoredSession,
  storeSession,
} from "@/lib/auth-storage";
import { getJwtExpiry, getJwtIssuedAt } from "@/lib/jwt";

const AuthContext = createContext(null);
const VALID_ROLES = new Set(["owner", "employee"]);
const IDLE_TIMEOUT_MS = 30 * 60 * 1000;
const TOKEN_RENEWAL_INTERVAL_MS = 5 * 60 * 1000;
const TOKEN_RENEWAL_CHECK_MS = 15 * 1000;
const ACTIVITY_SAVE_DELAY_MS = 500;
const INACTIVITY_SESSION_MESSAGE =
  "QLMS paused after 30 minutes without activity. Enter your password to continue.";
const TOKEN_RENEWAL_MESSAGE =
  "QLMS needs to check your account again. Enter your password to continue.";
const INACTIVE_SESSION_MESSAGE =
  "Enter your password to continue. If you cannot sign in, ask the owner to check your account.";

function getSessionFromLogin(response, lastActivityAt = Date.now()) {
  const expiresAt = getJwtExpiry(response.access_token);
  const issuedAt = getJwtIssuedAt(response.access_token);
  const hasValidUserId = Number.isInteger(response.user_id) && response.user_id > 0;
  const hasValidUsername =
    typeof response.username === "string" && response.username.trim();

  if (
    !expiresAt ||
    !issuedAt ||
    !VALID_ROLES.has(response.role) ||
    !hasValidUserId ||
    !hasValidUsername
  ) {
    throw new ApiError("QLMS could not sign you in. Contact support.", 0, "QLMS-LOGIN-REPLY");
  }

  return {
    token: response.access_token,
    role: response.role,
    expiresAt,
    issuedAt,
    lastActivityAt,
    userId: response.user_id,
    username: response.username,
  };
}

function hasRememberedIdentity(session) {
  return Boolean(
    session &&
      VALID_ROLES.has(session.role) &&
      Number.isInteger(session.userId) &&
      session.userId > 0 &&
      typeof session.username === "string" &&
      session.username.trim(),
  );
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [idleExpiresAt, setIdleExpiresAt] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reauthenticationMessage, setReauthenticationMessage] = useState("");
  const sessionRef = useRef(null);
  const lastActivityAtRef = useRef(null);
  const activitySaveTimerRef = useRef(null);
  const activitySinceRenewalRef = useRef(false);
  const renewalRequestRef = useRef(null);

  const commitSession = useCallback((nextSession) => {
    sessionRef.current = nextSession;
    if (nextSession) {
      storeSession(nextSession);
    } else {
      clearStoredSession();
    }
    setSession(nextSession);
  }, []);

  const logout = useCallback(() => {
    if (activitySaveTimerRef.current) {
      window.clearTimeout(activitySaveTimerRef.current);
      activitySaveTimerRef.current = null;
    }
    lastActivityAtRef.current = null;
    activitySinceRenewalRef.current = false;
    renewalRequestRef.current = null;
    setIdleExpiresAt(null);
    setReauthenticationMessage("");
    commitSession(null);
  }, [commitSession]);

  const requireReauthentication = useCallback(
    (message) => {
      const currentSession = sessionRef.current;

      if (activitySaveTimerRef.current) {
        window.clearTimeout(activitySaveTimerRef.current);
        activitySaveTimerRef.current = null;
      }

      lastActivityAtRef.current = null;
      activitySinceRenewalRef.current = false;
      setIdleExpiresAt(null);

      if (currentSession?.token || currentSession?.expiresAt) {
        // Keep only non-secret identity details so the current page can remain
        // mounted while the same staff member confirms their password.
        commitSession({
          ...currentSession,
          token: null,
          expiresAt: null,
          issuedAt: null,
          lastActivityAt: null,
        });
      } else if (!currentSession) {
        commitSession(null);
      }

      setReauthenticationMessage(message);
    },
    [commitSession],
  );

  const checkInactivity = useCallback(() => {
    const currentSession = sessionRef.current;
    if (!currentSession?.token) {
      return true;
    }

    const lastActivityAt = lastActivityAtRef.current;
    if (
      !Number.isFinite(lastActivityAt) ||
      Date.now() >= lastActivityAt + IDLE_TIMEOUT_MS
    ) {
      requireReauthentication(INACTIVITY_SESSION_MESSAGE);
      return true;
    }

    return false;
  }, [requireReauthentication]);

  const renewSessionToken = useCallback(async () => {
    const currentSession = sessionRef.current;
    if (
      renewalRequestRef.current ||
      !currentSession?.token ||
      checkInactivity()
    ) {
      return;
    }

    if (!currentSession.expiresAt || currentSession.expiresAt <= Date.now()) {
      requireReauthentication(TOKEN_RENEWAL_MESSAGE);
      return;
    }

    const tokenBeingRenewed = currentSession.token;
    const renewalRequest = apiRequest("/auth/refresh", {
      method: "POST",
      token: tokenBeingRenewed,
    });
    renewalRequestRef.current = renewalRequest;

    try {
      const response = await renewalRequest;

      // Ignore a late renewal response if login, logout or another lock already
      // replaced the token that started this request.
      if (sessionRef.current?.token !== tokenBeingRenewed) {
        return;
      }

      const nextSession = getSessionFromLogin(
        response,
        lastActivityAtRef.current,
      );
      if (
        nextSession.userId !== currentSession.userId ||
        nextSession.username !== currentSession.username
      ) {
        throw new ApiError("QLMS could not confirm your account. Log out and sign in again. Contact support if this continues.", 0, "QLMS-ACCOUNT");
      }

      activitySinceRenewalRef.current = false;
      commitSession(nextSession);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        requireReauthentication(INACTIVE_SESSION_MESSAGE);
      }
    } finally {
      if (renewalRequestRef.current === renewalRequest) {
        renewalRequestRef.current = null;
      }
    }
  }, [checkInactivity, commitSession, requireReauthentication]);

  const saveLatestActivity = useCallback(() => {
    activitySaveTimerRef.current = null;
    const currentSession = sessionRef.current;
    const lastActivityAt = lastActivityAtRef.current;

    if (!currentSession?.token || !Number.isFinite(lastActivityAt)) {
      return;
    }

    const updatedSession = { ...currentSession, lastActivityAt };
    sessionRef.current = updatedSession;
    storeSession(updatedSession);
    setIdleExpiresAt(lastActivityAt + IDLE_TIMEOUT_MS);
  }, []);

  const recordUserActivity = useCallback(() => {
    const currentSession = sessionRef.current;
    if (!currentSession?.token || checkInactivity()) {
      return;
    }

    lastActivityAtRef.current = Date.now();
    activitySinceRenewalRef.current = true;

    if (!activitySaveTimerRef.current) {
      activitySaveTimerRef.current = window.setTimeout(
        saveLatestActivity,
        ACTIVITY_SAVE_DELAY_MS,
      );
    }

    if (
      Number.isFinite(currentSession.issuedAt) &&
      Date.now() - currentSession.issuedAt >= TOKEN_RENEWAL_INTERVAL_MS
    ) {
      void renewSessionToken();
    }
  }, [checkInactivity, renewSessionToken, saveLatestActivity]);

  useEffect(() => {
    // Storage is browser-only, so the session is restored after hydration.
    const storedSession = readStoredSession();
    const now = Date.now();
    const storedIssuedAt = storedSession?.token
      ? storedSession.issuedAt || getJwtIssuedAt(storedSession.token)
      : null;
    const storedActivityAt = Number.isFinite(storedSession?.lastActivityAt)
      ? storedSession.lastActivityAt
      : now;
    const inactivityExpired =
      storedActivityAt + IDLE_TIMEOUT_MS <= now;
    const tokenIsValid =
      storedSession?.token &&
      storedSession.expiresAt > now &&
      Number.isFinite(storedIssuedAt);

    const hydrationTimer = window.setTimeout(() => {
      if (
        hasRememberedIdentity(storedSession) &&
        tokenIsValid &&
        !inactivityExpired
      ) {
        const currentActivityAt =
          document.visibilityState === "visible" ? now : storedActivityAt;
        const restoredSession = {
          ...storedSession,
          issuedAt: storedIssuedAt,
          lastActivityAt: currentActivityAt,
        };
        lastActivityAtRef.current = currentActivityAt;
        activitySinceRenewalRef.current =
          document.visibilityState === "visible";
        setIdleExpiresAt(currentActivityAt + IDLE_TIMEOUT_MS);
        commitSession(restoredSession);
      } else if (hasRememberedIdentity(storedSession)) {
        const lockedSession = {
          ...storedSession,
          token: null,
          expiresAt: null,
          issuedAt: null,
          lastActivityAt: null,
        };
        commitSession(lockedSession);
        setReauthenticationMessage(
          inactivityExpired
            ? INACTIVITY_SESSION_MESSAGE
            : TOKEN_RENEWAL_MESSAGE,
        );
      } else {
        commitSession(null);
      }

      setIsLoading(false);
    }, 0);

    return () => window.clearTimeout(hydrationTimer);
  }, [commitSession]);

  useEffect(() => {
    if (!session?.token) {
      return undefined;
    }

    function checkWhenVisible() {
      if (document.visibilityState === "visible") {
        checkInactivity();
      }
    }

    window.addEventListener("focus", checkInactivity);
    document.addEventListener("visibilitychange", checkWhenVisible);

    return () => {
      window.removeEventListener("focus", checkInactivity);
      document.removeEventListener("visibilitychange", checkWhenVisible);
    };
  }, [checkInactivity, session?.token]);

  useEffect(() => {
    if (!session?.token || !idleExpiresAt) {
      return undefined;
    }

    const inactivityTimer = window.setTimeout(
      checkInactivity,
      Math.max(idleExpiresAt - Date.now(), 0),
    );
    return () => window.clearTimeout(inactivityTimer);
  }, [checkInactivity, idleExpiresAt, session?.token]);

  useEffect(() => {
    if (!session?.token) {
      return undefined;
    }

    const activityEvents = ["pointerdown", "keydown", "touchstart", "wheel"];
    for (const eventName of activityEvents) {
      window.addEventListener(eventName, recordUserActivity, { passive: true });
    }

    return () => {
      for (const eventName of activityEvents) {
        window.removeEventListener(eventName, recordUserActivity);
      }
    };
  }, [recordUserActivity, session?.token]);

  useEffect(() => {
    if (!session?.token) {
      return undefined;
    }

    function renewIfDue() {
      const currentSession = sessionRef.current;
      if (
        document.visibilityState !== "visible" ||
        !activitySinceRenewalRef.current ||
        !Number.isFinite(currentSession?.issuedAt) ||
        Date.now() - currentSession.issuedAt < TOKEN_RENEWAL_INTERVAL_MS
      ) {
        return;
      }
      void renewSessionToken();
    }

    const renewalTimer = window.setInterval(
      renewIfDue,
      TOKEN_RENEWAL_CHECK_MS,
    );
    renewIfDue();
    return () => window.clearInterval(renewalTimer);
  }, [renewSessionToken, session?.token]);

  const login = useCallback(
    async (username, password) => {
      const response = await loginRequest(username, password);
      const now = Date.now();
      const nextSession = getSessionFromLogin(response, now);

      lastActivityAtRef.current = now;
      activitySinceRenewalRef.current = false;
      setIdleExpiresAt(now + IDLE_TIMEOUT_MS);
      setReauthenticationMessage("");
      commitSession(nextSession);
      return response.role;
    },
    [commitSession],
  );

  const reauthenticate = useCallback(
    async (password) => {
      const currentSession = sessionRef.current;
      if (!currentSession?.username) {
        throw new ApiError(
          "Log out and sign in again to continue.",
        );
      }

      const response = await loginRequest(currentSession.username, password);
      const now = Date.now();
      const nextSession = getSessionFromLogin(response, now);

      if (nextSession.userId !== currentSession.userId) {
        throw new ApiError("QLMS could not confirm your account. Log out and sign in again. Contact support if this continues.", 0, "QLMS-ACCOUNT");
      }

      lastActivityAtRef.current = now;
      activitySinceRenewalRef.current = false;
      setIdleExpiresAt(now + IDLE_TIMEOUT_MS);
      setReauthenticationMessage("");
      commitSession(nextSession);
    },
    [commitSession],
  );

  const authenticatedRequest = useCallback(
    async (path, options = {}) => {
      const currentSession = sessionRef.current;
      if (!currentSession?.token) {
        throw new ApiError("Enter your password to continue.", 401);
      }

      if (checkInactivity()) {
        throw new ApiError(INACTIVITY_SESSION_MESSAGE, 401);
      }

      if (
        !currentSession.expiresAt ||
        currentSession.expiresAt <= Date.now()
      ) {
        requireReauthentication(TOKEN_RENEWAL_MESSAGE);
        throw new ApiError(TOKEN_RENEWAL_MESSAGE, 401);
      }

      try {
        return await apiRequest(path, {
          ...options,
          token: currentSession.token,
        });
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          requireReauthentication(INACTIVE_SESSION_MESSAGE);
        }
        throw error;
      }
    },
    [checkInactivity, requireReauthentication],
  );

  const value = useMemo(
    () => ({
      token: session?.token ?? null,
      role: session?.role ?? null,
      userId: session?.userId ?? null,
      username: session?.username ?? null,
      expiresAt: session?.expiresAt ?? null,
      idleExpiresAt,
      isAuthenticated: Boolean(session),
      isLoading,
      reauthenticationRequired: Boolean(reauthenticationMessage),
      reauthenticationMessage,
      login,
      reauthenticate,
      logout,
      authenticatedRequest,
    }),
    [
      authenticatedRequest,
      idleExpiresAt,
      isLoading,
      login,
      logout,
      reauthenticate,
      reauthenticationMessage,
      session,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
