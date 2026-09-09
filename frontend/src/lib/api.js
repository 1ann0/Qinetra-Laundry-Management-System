import { ApiError, responseError } from "./user-messages.js";
export { ApiError } from "./user-messages.js";

const REQUEST_TIMEOUT_MS = 30_000;

function getApiBaseUrl() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (!apiUrl) {
    throw new ApiError(
      "QLMS is not ready to use. Contact support.", 0, "QLMS-SETUP",
    );
  }

  return apiUrl.replace(/\/$/, "");
}

export async function apiRequest(path, options = {}) {
  const { token, headers, signal, ...fetchOptions } = options;
  const requestHeaders = new Headers(headers);

  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const url = `${getApiBaseUrl()}${path}`;
  const isSave = !["GET", "HEAD"].includes((fetchOptions.method || "GET").toUpperCase()) && !path.startsWith("/auth/");
  const recovery = isSave
    ? "The change may have been saved. Check the record before you try again."
    : "Try again in a moment.";

  // Stop waiting after 30 seconds. Never repeat a save automatically.
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  const abortRequest = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", abortRequest, { once: true });

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: requestHeaders,
      signal: controller.signal,
    });
    const contentType = response.headers.get("content-type") || "";
    let payload;
    try {
      payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();
    } catch (error) {
      if (controller.signal.aborted) throw error;
      if (response.ok) {
        throw new ApiError(`QLMS could not read the reply. ${recovery} Contact support if this continues.`, response.status, "QLMS-RESPONSE");
      }
    }
    if (!response.ok) throw responseError(response.status, payload, path, recovery);
    const isReport = path.split("?")[0] === "/dashboard/export" && /text\/(csv|plain)/.test(contentType);
    if (!isReport && (!contentType.includes("application/json") || payload === null || typeof payload !== "object")) {
      throw new ApiError(`QLMS could not read the reply. ${recovery} Contact support.`, response.status, "QLMS-RESPONSE");
    }
    return payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (timedOut) {
      throw new ApiError(`QLMS took too long to reply. ${recovery} Contact support if this continues.`, 0, "QLMS-TIMEOUT");
    }
    throw new ApiError(`QLMS could not connect. Check your internet connection. ${recovery} Contact support if this continues.`, 0, "QLMS-CONNECTION");
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abortRequest);
  }
}

export function loginRequest(username, password) {
  const body = new URLSearchParams({ username, password });

  return apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}
