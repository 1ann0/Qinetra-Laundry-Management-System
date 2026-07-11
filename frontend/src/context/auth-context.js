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

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    clearStoredSession();
    setSession(null);
  }, []);

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

    const remainingTime = session.expiresAt - Date.now();

    const expiryTimer = window.setTimeout(logout, Math.max(remainingTime, 0));
    return () => window.clearTimeout(expiryTimer);
  }, [logout, session]);

  const login = useCallback(async (username, password) => {
    const response = await loginRequest(username, password);
    const expiresAt = getJwtExpiry(response.access_token);

    if (!expiresAt || !VALID_ROLES.has(response.role)) {
      throw new ApiError("The backend returned an invalid login session.");
    }

    const nextSession = {
      token: response.access_token,
      role: response.role,
      expiresAt,
    };

    storeSession(nextSession);
    setSession(nextSession);
  }, []);

  const authenticatedRequest = useCallback(
    async (path, options = {}) => {
      try {
        return await apiRequest(path, { ...options, token: session?.token });
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          logout();
        }
        throw error;
      }
    },
    [logout, session],
  );

  const value = useMemo(
    () => ({
      token: session?.token ?? null,
      role: session?.role ?? null,
      isAuthenticated: Boolean(session),
      isLoading,
      login,
      logout,
      authenticatedRequest,
    }),
    [authenticatedRequest, isLoading, login, logout, session],
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
