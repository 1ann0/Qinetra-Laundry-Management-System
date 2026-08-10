"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { ApiError, apiRequest, loginRequest } from "@/lib/api";
import {
  clearStoredSession,
  readStoredSession,
  storeSession,
} from "@/lib/auth-storage";
import { getJwtExpiry } from "@/lib/jwt";

const AuthContext = createContext(null);
const VALID_ROLES = new Set(["owner", "employee"]);
const EXPIRED_SESSION_MESSAGE =
  "Your 30-minute session ended. Re-enter your password to continue without losing this page.";
const INACTIVE_SESSION_MESSAGE =
  "Your session is no longer active. Re-enter your password or ask the owner about your access.";

function getSessionFromLogin(response) {
  const expiresAt = getJwtExpiry(response.access_token);
  const hasValidUserId = Number.isInteger(response.user_id) && response.user_id > 0;
  const hasValidUsername =
    typeof response.username === "string" && response.username.trim();

  if (
    !expiresAt ||
    !VALID_ROLES.has(response.role) ||
    !hasValidUserId ||
    !hasValidUsername
  ) {
    throw new ApiError("The backend returned an invalid login session.");
  }

  return {
    token: response.access_token,
    role: response.role,
    expiresAt,
    userId: response.user_id,
    username: response.username,
  };
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reauthenticationMessage, setReauthenticationMessage] = useState("");

  const logout = useCallback(() => {
    clearStoredSession();
    setSession(null);
    setReauthenticationMessage("");
  }, []);

  const requireReauthentication = useCallback(
    (message) => {
      if (session) {
        const lockedSession = { ...session, token: null, expiresAt: null };

        // Keep only non-secret identity details so a refresh still asks for the
        // fixed account password instead of losing the reauthentication state.
        storeSession(lockedSession);
        if (session.token || session.expiresAt) {
          setSession(lockedSession);
        }
      } else {
        clearStoredSession();
      }

      setReauthenticationMessage(message);
    },
    [session],
  );

  useEffect(() => {
    // Storage is browser-only, so the session is restored after hydration.
    const storedSession = readStoredSession();
    const isValid =
      storedSession?.token &&
      VALID_ROLES.has(storedSession.role) &&
      storedSession.expiresAt > Date.now();

    const hydrationTimer = window.setTimeout(() => {
      if (isValid) {
        setSession(storedSession);
      } else if (storedSession && VALID_ROLES.has(storedSession.role)) {
        const lockedSession = {
          ...storedSession,
          token: null,
          expiresAt: null,
        };
        storeSession(lockedSession);
        setSession(lockedSession);
        setReauthenticationMessage(EXPIRED_SESSION_MESSAGE);
      } else {
        clearStoredSession();
      }

      setIsLoading(false);
    }, 0);

    return () => window.clearTimeout(hydrationTimer);
  }, []);

  useEffect(() => {
    if (!session?.expiresAt) {
      return undefined;
    }

    function checkExpiry() {
      if (Date.now() >= session.expiresAt) {
        requireReauthentication(EXPIRED_SESSION_MESSAGE);
      }
    }

    function checkExpiryWhenVisible() {
      if (document.visibilityState === "visible") {
        checkExpiry();
      }
    }

    const remainingTime = session.expiresAt - Date.now();

    const expiryTimer = window.setTimeout(
      checkExpiry,
      Math.max(remainingTime, 0),
    );
    window.addEventListener("focus", checkExpiry);
    document.addEventListener("visibilitychange", checkExpiryWhenVisible);

    return () => {
      window.clearTimeout(expiryTimer);
      window.removeEventListener("focus", checkExpiry);
      document.removeEventListener("visibilitychange", checkExpiryWhenVisible);
    };
  }, [requireReauthentication, session]);

  const login = useCallback(async (username, password) => {
    const response = await loginRequest(username, password);
    const nextSession = getSessionFromLogin(response);

    storeSession(nextSession);
    setReauthenticationMessage("");
    setSession(nextSession);
    return response.role;
  }, []);

  const reauthenticate = useCallback(
    async (password) => {
      if (!session?.username) {
        throw new ApiError(
          "This older session cannot be resumed. Log out and sign in again.",
        );
      }

      const response = await loginRequest(session.username, password);
      const nextSession = getSessionFromLogin(response);

      if (session.userId && nextSession.userId !== session.userId) {
        throw new ApiError("QLMS could not confirm the same staff account.");
      }

      storeSession(nextSession);
      setSession(nextSession);
      setReauthenticationMessage("");
    },
    [session],
  );

  const authenticatedRequest = useCallback(
    async (path, options = {}) => {
      if (!session?.token) {
        throw new ApiError("Your session needs to be confirmed again.", 401);
      }

      if (!session.expiresAt || session.expiresAt <= Date.now()) {
        requireReauthentication(EXPIRED_SESSION_MESSAGE);
        throw new ApiError("Your session has expired.", 401);
      }

      try {
        return await apiRequest(path, { ...options, token: session?.token });
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          requireReauthentication(INACTIVE_SESSION_MESSAGE);
        }
        throw error;
      }
    },
    [requireReauthentication, session],
  );

  const value = useMemo(
    () => ({
      token: session?.token ?? null,
      role: session?.role ?? null,
      userId: session?.userId ?? null,
      username: session?.username ?? null,
      expiresAt: session?.expiresAt ?? null,
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
