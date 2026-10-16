import { ApiError, responseError } from "./user-messages.js";
export { ApiError } from "./user-messages.js";

const REQUEST_TIMEOUT_MS = 30_000;

function retryDelay(response, attempt) {
  const header = response?.headers.get("retry-after");
  let requestedDelay = null;
  if (header) {
    const trimmed = header.trim();
    const isHttpDate = /^[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} GMT$/.test(trimmed);
    const value = /^\d+$/.test(trimmed) ? Number(trimmed) * 1000 : isHttpDate ? Date.parse(trimmed) - Date.now() : NaN;
    if (Number.isFinite(value)) requestedDelay = Math.max(0, value);
  }
  if (response?.status === 429 && requestedDelay === null) return null;
  return Math.max(requestedDelay || 0, 500 * 2 ** attempt + Math.random() * 250);
}

function waitForRetry(delay, signal) {
  return new Promise((resolve, reject) => {
    if (signal.aborted) return reject(new Error("Request aborted"));
    const abort = () => { clearTimeout(timer); reject(new Error("Request aborted")); };
    const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, delay);
    signal.addEventListener("abort", abort, { once: true });
  });
}

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
  const { token, headers, signal, responseType, ...fetchOptions } = options;
  const isBinaryReport = responseType === "blob" && /^\/dashboard\/reports\/(orders|customer|service|money|attention|catalogue|expenses|closing|till|returns)\/download(?:\?|$)/.test(path);
  if (responseType && (responseType !== "blob" || !isBinaryReport || (fetchOptions.method || "GET").toUpperCase() !== "GET")) {
    throw new ApiError("QLMS could not prepare this download. Contact support.", 0, "QLMS-RESPONSE");
  }
  const requestHeaders = new Headers(headers);

  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const url = `${getApiBaseUrl()}${path}`;
  const isSave = !["GET", "HEAD"].includes((fetchOptions.method || "GET").toUpperCase()) && !path.startsWith("/auth/");
  const recovery = isSave
    ? requestHeaders.has("Idempotency-Key")
      ? "The change may have been saved. Keep this tab open and select Retry previous save."
      : "The change may have been saved. Check the record before you try again."
    : "Try again in a moment.";

  const canRetry = ["GET", "HEAD"].includes((fetchOptions.method || "GET").toUpperCase()) && !path.startsWith("/auth/");
  // Free hosting can take a minute to wake; record requests keep their normal deadline.
  const timeout = path === "/auth/login" || (path === "/health/ready" && canRetry) ? 120_000 : REQUEST_TIMEOUT_MS;
  const deadline = Date.now() + timeout;
  // Fetches, backoff and reply parsing share one deadline. Saves are never repeated here.
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
  const abortRequest = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", abortRequest, { once: true });

  try {
    let response;
    for (let attempt = 0; ; attempt += 1) {
      if (controller.signal.aborted) throw new Error("Request aborted");
      try {
        response = await fetch(url, { ...fetchOptions, headers: requestHeaders, signal: controller.signal });
      } catch (error) {
        if (!canRetry || attempt >= 2 || controller.signal.aborted || !(error instanceof TypeError)) throw error;
        const delay = retryDelay(null, attempt);
        if (Date.now() + delay >= deadline) throw error;
        await waitForRetry(delay, controller.signal);
        continue;
      }
      if (!canRetry || attempt >= 2 || ![429, 502, 503, 504].includes(response.status)) break;
      const delay = retryDelay(response, attempt);
      if (delay === null || Date.now() + delay >= deadline) break;
      void response.body?.cancel().catch(() => {});
      await waitForRetry(delay, controller.signal);
    }
    if (controller.signal.aborted) throw new Error("Request aborted");
    const contentType = response.headers.get("content-type") || "";
    let payload;
    try {
      payload = isBinaryReport && response.ok ? await response.blob() : contentType.includes("application/json")
        ? await response.json()
        : await response.text();
    } catch (error) {
      if (controller.signal.aborted) throw error;
      if (response.ok) {
        throw new ApiError(`QLMS could not read the reply. ${recovery} Contact support if this continues.`, response.status, "QLMS-RESPONSE");
      }
    }
    if (!response.ok) throw responseError(response.status, payload, path, recovery);
    if (isBinaryReport) {
      const requestedFormat = new URLSearchParams(path.split("?")[1] || "").get("format") || "xlsx";
      const expectedType = requestedFormat === "csv" ? "text/csv" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
      const filename = response.headers.get("content-disposition")?.match(/filename="(qlms_[A-Za-z0-9_.-]{1,170})"/)?.[1];
      if (!contentType.toLowerCase().startsWith(expectedType) || !filename?.endsWith(`.${requestedFormat}`)) {
        throw new ApiError("QLMS could not read the report. Try again or contact support.", response.status, "QLMS-RESPONSE");
      }
      if (controller.signal.aborted) throw new Error("Request aborted");
      return { blob: payload, filename };
    }
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
    if (signal?.aborted) throw new ApiError("The request was cancelled.", 0, "QLMS-CANCELLED");
    throw new ApiError(`QLMS could not connect. Check your internet connection. ${recovery} Contact support if this continues.`, 0, "QLMS-CONNECTION");
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abortRequest);
  }
}

export async function checkApiReadiness({ signal } = {}) {
  const reply = await apiRequest("/health/ready", { signal });
  if (reply.status !== "ready") {
    throw new ApiError("QLMS is not ready yet. Try signing in again in a moment.", 0, "QLMS-SERVICE");
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
