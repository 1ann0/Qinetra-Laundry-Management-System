// Point the owner to a common input problem; FastAPI remains authoritative.
export function alertPreferencesIssue(email, time) {
  const address = email.trim();
  const local = address.split("@")[0];
  if (/[\x00-\x1f\x7f]/.test(email) || address.length > 254 || local.length > 64 ||
      local.startsWith(".") || local.endsWith(".") || local.includes("..") ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address)) {
    return { field: "email", message: "Enter one email address, such as owner@example.com." };
  }
  if (!/^([01][0-9]|2[0-3]):[0-5][0-9]$/.test(time)) {
    return { field: "time", message: "Choose a daily backup time between 00:00 and 23:59 in Nairobi." };
  }
  return null;
}
