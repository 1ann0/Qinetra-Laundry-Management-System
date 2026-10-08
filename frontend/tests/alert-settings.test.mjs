import assert from "node:assert/strict";
import { test } from "node:test";
import { alertPreferencesIssue } from "../src/lib/alert-settings.js";

test("owner preference feedback identifies invalid email before time", () => {
  for (const email of ["", "wrong", "a@example.test\r\nBcc: b@example.test", "a..b@example.test"]) {
    assert.equal(alertPreferencesIssue(email, "22:00").field, "email");
  }
  assert.equal(alertPreferencesIssue("owner@example.test", "24:00").field, "time");
  assert.equal(alertPreferencesIssue("owner@example.test", "9:00").field, "time");
});

test("daily preference accepts midnight and 10 pm as Nairobi clock readings", () => {
  assert.equal(alertPreferencesIssue(" owner+alerts@example.test ", "22:00"), null);
  assert.equal(alertPreferencesIssue("owner@example.test", "00:00"), null);
  assert.equal(alertPreferencesIssue("owner@example.test", "23:59"), null);
});
