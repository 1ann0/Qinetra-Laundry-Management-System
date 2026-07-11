export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getApiBaseUrl() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (!apiUrl) {
    throw new ApiError(
      "QLMS is missing its API address. Add NEXT_PUBLIC_API_URL to .env.local.",
    );
  }

  return apiUrl.replace(/\/$/, "");
}

function getErrorMessage(payload, fallback) {
  if (typeof payload?.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg).join(" ");
  }

  return fallback;
}

export async function apiRequest(path, options = {}) {
  const { token, headers, ...fetchOptions } = options;
  const requestHeaders = new Headers(headers);

  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  let response;

  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...fetchOptions,
      headers: requestHeaders,
    });
  } catch {
    throw new ApiError(
      "QLMS could not reach the backend. Check that the API is running and try again.",
    );
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload, `Request failed with status ${response.status}.`),
      response.status,
    );
  }

  return payload;
}

export function loginRequest(username, password) {
  const body = new URLSearchParams({ username, password });

  return apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}
