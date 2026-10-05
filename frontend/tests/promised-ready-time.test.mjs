import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { test } from "node:test";
import {
  getPromisedTimeError,
  getSuggestedReadyInput,
  nairobiInputToUtc,
} from "../src/lib/promised-ready-time.js";
import { formatNairobiDateTime } from "../src/lib/format-nairobi.js";

test("entered Nairobi time has the same review, UTC payload and receipt", () => {
  const timestamp = nairobiInputToUtc("2026-10-06T10:00");
  assert.equal(timestamp, "2026-10-06T07:00:00.000Z");
  assert.match(formatNairobiDateTime(timestamp), /10:00/);
  assert.equal(formatNairobiDateTime(timestamp), formatNairobiDateTime("2026-10-06T07:00:00Z"));
});

test("blank, invalid and offset-bearing form values are rejected safely", () => {
  for (const value of ["", null, undefined, "tomorrow", "2026-02-30T10:00", "2026-02-29T10:00", "2026-10-06T24:00", "2026-10-06T10:60", "2026-10-06T10:00Z", "2026-10-06T10:00:00", "0000-01-01T10:00"]) {
    assert.equal(nairobiInputToUtc(value), null, String(value));
  }
  assert.equal(nairobiInputToUtc("2028-02-29T10:00"), "2028-02-29T07:00:00.000Z");
  assert.equal(formatNairobiDateTime(nairobiInputToUtc(""), "Not set"), "Not set");
});

test("validation compares the Nairobi promise with the current instant", () => {
  assert.equal(getPromisedTimeError(""), "Confirm when the order will be ready.");
  assert.equal(getPromisedTimeError("invalid"), "Enter a valid promised completion time.");
  assert.equal(getPromisedTimeError("2026-10-06T10:00", Date.parse("2026-10-06T06:00:00Z")), "");
  assert.equal(getPromisedTimeError("2026-10-06T10:00", Date.parse("2026-10-06T07:00:00Z")), "The promised completion time must be in the future.");
  assert.equal(getPromisedTimeError("2026-10-06T10:00", Date.parse("2026-10-06T08:00:00Z")), "The promised completion time must be in the future.");
});

test("suggestions use the longest service and retain the peak-time hour", () => {
  const services = [{ turnaround_minutes: 60 }, { turnaround_minutes: 180 }];
  const now = Date.parse("2026-10-05T06:00:00Z");
  assert.equal(getSuggestedReadyInput([], false, now), "");
  assert.equal(getSuggestedReadyInput(services, false, now), "2026-10-05T12:00");
  assert.equal(getSuggestedReadyInput(services, true, now), "2026-10-05T13:00");
});

test("suggestions roll into the next Nairobi day", () => {
  assert.equal(getSuggestedReadyInput([{ turnaround_minutes: 60 }], false, Date.parse("2026-10-05T20:30:00Z")), "2026-10-06T00:30");
  assert.equal(nairobiInputToUtc("2026-10-06T00:30"), "2026-10-05T21:30:00.000Z");
});

test("device timezone and daylight saving cannot change a Nairobi promise", () => {
  const moduleUrl = new URL("../src/lib/promised-ready-time.js", import.meta.url).href;
  const script = `
    import { getPromisedTimeError, getSuggestedReadyInput, nairobiInputToUtc } from ${JSON.stringify(moduleUrl)};
    console.log(JSON.stringify({
      payload: nairobiInputToUtc("2026-10-06T10:00"),
      error: getPromisedTimeError("2026-10-06T10:00", Date.parse("2026-10-06T06:00:00Z")),
      suggestion: getSuggestedReadyInput([{ turnaround_minutes: 60 }], false, Date.parse("2026-10-05T20:30:00Z")),
      dstDate: nairobiInputToUtc("2026-03-08T02:30")
    }));
  `;
  for (const timezone of ["Africa/Nairobi", "UTC", "America/New_York"]) {
    const result = JSON.parse(execFileSync(process.execPath, ["--input-type=module", "-e", script], {
      env: { ...process.env, TZ: timezone, NODE_NO_WARNINGS: "1" },
      encoding: "utf8",
    }));
    assert.deepEqual(result, {
      payload: "2026-10-06T07:00:00.000Z",
      error: "",
      suggestion: "2026-10-06T00:30",
      dstDate: "2026-03-07T23:30:00.000Z",
    }, timezone);
  }
});
