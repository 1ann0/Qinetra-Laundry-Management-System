export function formatNairobiDateTime(value, fallback = "Not recorded") {
  if (!value) return fallback;
  // PostgreSQL returns an offset. SQLite test data can omit it even though the
  // stored value is UTC, so add Z only when the API value has no timezone.
  const timestamp = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Africa/Nairobi",
  }).format(new Date(timestamp));
}
