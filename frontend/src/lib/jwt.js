function readJwtPayload(token) {
  try {
    const payloadPart = token.split(".")[1];
    const base64 = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    return JSON.parse(window.atob(padded));
  } catch {
    return null;
  }
}

export function getJwtExpiry(token) {
  const payload = readJwtPayload(token);
  return Number.isFinite(payload?.exp) ? payload.exp * 1000 : null;
}

export function getJwtIssuedAt(token) {
  const payload = readJwtPayload(token);
  return Number.isFinite(payload?.iat) ? payload.iat * 1000 : null;
}
