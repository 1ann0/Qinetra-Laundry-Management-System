// Form values mean Nairobi wall-clock time; saved API timestamps mean UTC.
const inputFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Africa/Nairobi",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function formatNairobiInput(date) {
  const parts = Object.fromEntries(inputFormatter.formatToParts(date).map(({ type, value }) => [type, value]));
  return `${parts.year.padStart(4, "0")}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function nairobiInputToUtc(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value) || value.startsWith("0000-")) {
    return null;
  }
  // Kenya stays at UTC+3. A round trip rejects dates JavaScript normalises,
  // such as 30 February, instead of silently saving a different promise.
  const date = new Date(`${value}:00+03:00`);
  if (Number.isNaN(date.getTime()) || formatNairobiInput(date) !== value) return null;
  return date.toISOString();
}

export function getPromisedTimeError(value, now = Date.now()) {
  if (!value) return "Confirm when the order will be ready.";
  const timestamp = nairobiInputToUtc(value);
  if (!timestamp) return "Enter a valid promised completion time.";
  if (Date.parse(timestamp) <= now) return "The promised completion time must be in the future.";
  return "";
}

// Keep the existing longest-service estimate and optional peak-time hour.
export function getSuggestedReadyInput(serviceLines, isPeakTime, now = Date.now()) {
  if (serviceLines.length === 0) return "";
  const turnaroundMinutes = serviceLines.reduce(
    (longestTime, serviceLine) => Math.max(longestTime, serviceLine.turnaround_minutes),
    0,
  );
  return formatNairobiInput(new Date(now + (turnaroundMinutes + (isPeakTime ? 60 : 0)) * 60 * 1000));
}
