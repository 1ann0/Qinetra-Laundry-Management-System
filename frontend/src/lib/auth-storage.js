const STORAGE_KEY = "qlms-session";

export function readStoredSession() {
  try {
    const rawSession = window.sessionStorage.getItem(STORAGE_KEY);
    return rawSession ? JSON.parse(rawSession) : null;
  } catch {
    return null;
  }
}

export function storeSession(session) {
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredSession() {
  window.sessionStorage.removeItem(STORAGE_KEY);
}
