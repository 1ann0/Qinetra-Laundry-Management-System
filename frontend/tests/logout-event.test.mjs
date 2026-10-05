import assert from "node:assert/strict";
import { test } from "node:test";
import { makeLogoutEvent, appliesToSession } from "../src/lib/logout-event.js";

test("logout messages contain no token or password", () => {
  assert.deepEqual(makeLogoutEvent("https://api.example.com", 7), {action:"logout", apiUrl:"https://api.example.com", userId:7});
});
test("logout affects only the same account and API", () => {
  const current = {userId:7, apiUrl:"https://api.example.com"};
  assert.equal(appliesToSession(makeLogoutEvent(current.apiUrl, 7), current), true);
  for (const event of [null, {}, {action:"logout",userId:"7",apiUrl:current.apiUrl}, makeLogoutEvent(current.apiUrl, 8),
                       makeLogoutEvent("https://other.example.com", 7), {action:"login",userId:7,apiUrl:current.apiUrl}]) {
    assert.equal(appliesToSession(event, current), false);
  }
});
