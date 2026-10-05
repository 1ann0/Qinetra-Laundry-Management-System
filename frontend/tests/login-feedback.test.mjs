import assert from "node:assert/strict";
import { test } from "node:test";
import { responseError } from "../src/lib/user-messages.js";

test("throttled sign-in explains the bounded wait without suggesting a save retry", () => {
  const error = responseError(429, {}, "/auth/login", "Retry the original save.");
  assert.equal(error.code, "QLMS-LOGIN-LIMIT");
  assert.match(error.message, /up to five minutes/);
  assert.doesNotMatch(error.message, /save|one minute/);
});
