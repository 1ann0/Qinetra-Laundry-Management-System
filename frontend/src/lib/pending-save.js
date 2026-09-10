import { ApiError } from "./user-messages.js";

export function saveScope(userId, path) {
  return `qlms-pending-save:${userId}:${path}`;
}

export function readPendingSave(storage, scope) {
  try {
    const raw = storage.getItem(scope);
    if (!raw) return null;
    const attempt = JSON.parse(raw);
    if (typeof attempt.key !== "string" || typeof attempt.body !== "string") throw new Error();
    return attempt;
  } catch {
    throw new ApiError("QLMS could not read your previous save. Keep this tab open and contact support.", 0, "QLMS-SAVE-STORAGE");
  }
}

export function prepareSave(storage, scope, body, makeKey = () => crypto.randomUUID()) {
  const pending = readPendingSave(storage, scope);
  if (pending) {
    throw new ApiError("Finish the previous save before you enter another one. Select Retry previous save.", 0, "QLMS-SAVE-PENDING");
  }
  const attempt = { key: makeKey(), body: JSON.stringify(body) };
  try {
    storage.setItem(scope, JSON.stringify(attempt));
  } catch {
    throw new ApiError("QLMS cannot keep a save reference in this browser. Contact support before you save.", 0, "QLMS-SAVE-STORAGE");
  }
  return attempt;
}

export async function sendPendingSave(request, storage, scope, path, attempt) {
  let response;
  try {
    response = await request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": attempt.key },
      body: attempt.body,
    });
  } catch (error) {
    // These responses reject the request before a save; uncertain results retain the key.
    if (error instanceof ApiError && [400, 422].includes(error.status)) {
      storage.removeItem(scope);
    }
    throw error;
  }
  try {
    storage.removeItem(scope);
  } catch {
    throw new ApiError("The save returned a reply, but QLMS could not clear its reference. Contact support.", 0, "QLMS-SAVE-STORAGE");
  }
  return response;
}
