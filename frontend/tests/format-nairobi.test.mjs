import test from "node:test";
import assert from "node:assert/strict";

import { formatNairobiDateTime } from "../src/lib/format-nairobi.js";

test("stored UTC completion time is shown in Nairobi time", () => {
  assert.match(formatNairobiDateTime("2026-09-15T20:30:00Z"), /23:30/);
  assert.match(formatNairobiDateTime("2026-09-15T20:30:00"), /23:30/);
});

test("missing completion time keeps the screen-specific fallback", () => {
  assert.equal(formatNairobiDateTime("", "Not set"), "Not set");
});
