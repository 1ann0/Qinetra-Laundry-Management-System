// Labels describe the action without exposing URLs, customer details or tokens.
export function getRequestFeedback(path, method = "GET") {
  const isRead = ["GET", "HEAD"].includes(method.toUpperCase());
  let label = isRead ? "Loading records…" : "Saving changes…";
  if (path.startsWith("/auth/")) label = "Checking sign-in…";
  else if (path.startsWith("/dashboard/export")) label = "Preparing download…";
  else if (!isRead && path === "/orders/detailed") label = "Saving order…";
  else if (!isRead && /\/payments$/.test(path)) label = "Recording payment…";
  else if (!isRead && /\/refunds$/.test(path)) label = "Recording refund…";
  return { label, isRead };
}

export function getActiveRequest(requests) {
  const active = Object.values(requests);
  return active.find((request) => !request.isRead) || active[0] || null;
}
