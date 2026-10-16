import assert from "node:assert/strict";
import { test, beforeEach, afterEach } from "node:test";
import { ApiError, apiRequest, loginRequest } from "../src/lib/api.js";
import { getUserMessage, responseError } from "../src/lib/user-messages.js";

const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;
test("report size failures explain how to narrow filters without exposing server details", () => {
  const error = responseError(413, { detail: "private database content" }, "/dashboard/reports/orders/download", "Try again.");
  assert.match(error.message, /narrow|fewer|shorter/i);
  assert.doesNotMatch(error.message, /private database content/);
});

test("report filter failures tell the owner to select the required customer or service", () => {
  const error = responseError(422, { detail: "Select the customer or service for this report" }, "/dashboard/reports/customer", "Try again.");
  assert.match(error.message, /choose|select/i);
  assert.match(error.message, /customer or service/i);
});

test("authenticated XLSX download returns its binary body and safe dated filename", async (t) => {
  const bytes = new Uint8Array([80, 75, 3, 4]);
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    assert.equal(options.headers.get("authorization"), "Bearer fictional-token");
    assert.equal(options.responseType, undefined);
    return new Response(bytes, { headers: {
      "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "content-disposition": 'attachment; filename="qlms_orders_current_20261013.xlsx"',
    } });
  });
  const result = await apiRequest("/dashboard/reports/orders/download?format=xlsx", { token: "fictional-token", responseType: "blob" });
  assert.equal(result.filename, "qlms_orders_current_20261013.xlsx");
  assert.deepEqual(new Uint8Array(await result.blob.arrayBuffer()), bytes);
});

test('closing and till reports use the authenticated binary download path', async (t) => {
  const fetchMock=t.mock.method(globalThis,'fetch',async (url)=>{
    const kind=url.includes('/closing/') ? 'closing' : 'till';
    const format=new URL(url).searchParams.get('format');
    return new Response('fictional export',{headers:{
      'content-type':format==='csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'content-disposition':`attachment; filename="qlms_${kind}_20261016.${format}"`,
    }});
  });
  for (const kind of ['closing','till']) for (const format of ['csv','xlsx']) {
    const result=await apiRequest(`/dashboard/reports/${kind}/download?format=${format}`,{token:'fictional-token',responseType:'blob'});
    assert.equal(result.filename,`qlms_${kind}_20261016.${format}`);
  }
  assert.equal(fetchMock.mock.callCount(),4);
  await assert.rejects(apiRequest('/dashboard/reports/unknown/download',{responseType:'blob'}),{code:'QLMS-RESPONSE'});
});

test("binary downloads preserve sign-in errors and refuse HTML or unsafe filenames", async (t) => {
  for (const response of [
    new Response("<html>private</html>", { status: 401 }),
    new Response("<html>private</html>", { headers: { "content-type": "text/html" } }),
    new Response('{"private":"not a report"}', { headers: { "content-type": "application/json" } }),
    new Response("csv", { headers: { "content-type": "text/csv", "content-disposition": 'attachment; filename="../private.csv"' } }),
  ]) {
    t.mock.method(globalThis, "fetch", async () => response);
    await assert.rejects(apiRequest("/dashboard/reports/orders/download?format=csv", { responseType: "blob" }),
      { code: response.status === 401 ? "QLMS-SIGNIN" : "QLMS-RESPONSE" });
  }
});

test("binary reply parsing stays inside the existing request deadline", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  t.mock.method(globalThis, "fetch", async (_url, { signal }) => ({
    ok: true, status: 200, headers: new Headers({ "content-type": "text/csv", "content-disposition": 'attachment; filename="qlms_orders_current.csv"' }),
    blob: () => new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new Error("body interrupted")))),
  }));
  const pending = assert.rejects(apiRequest("/dashboard/reports/orders/download?format=csv", { responseType: "blob" }), { code: "QLMS-TIMEOUT" });
  await Promise.resolve();
  t.mock.timers.tick(30_000);
  await pending;
});
beforeEach(() => { process.env.NEXT_PUBLIC_API_URL = "http://qlms.invalid"; });
afterEach(() => {
  if (originalApiUrl === undefined) delete process.env.NEXT_PUBLIC_API_URL;
  else process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
});
const json = (payload, status = 200) => new Response(JSON.stringify(payload), {
  status, headers: { "content-type": "application/json" },
});

test("successful requests preserve the body and Bearer authorization contract", async (t) => {
  const fetchMock = t.mock.method(globalThis, "fetch", async (_url, options) => {
    assert.equal(options.headers.get("Authorization"), "Bearer fixture-only");
    assert.equal(options.method, "POST");
    assert.equal(options.body, '{"name":"Fixture"}');
    return json({ id: 7 });
  });
  assert.deepEqual(await apiRequest("/customers", { token: "fixture-only", method: "POST", body: '{"name":"Fixture"}' }), { id: 7 });
  assert.equal(fetchMock.mock.callCount(), 1);
});

test("login still sends form data without treating sign-in as a record save", async (t) => {
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    assert.equal(options.headers.get("content-type"), "application/x-www-form-urlencoded");
    assert.equal(options.body.get("username"), "fixture");
    return json({ detail: "Incorrect username or password" }, 401);
  });
  await assert.rejects(loginRequest("fixture", "dummy"), (error) => {
    assert.equal(error.status, 401);
    assert.equal(error.code, "QLMS-SIGNIN");
    assert.match(error.message, /Check your username and password/);
    assert.doesNotMatch(error.message, /may have been saved/);
    return true;
  });
});

test("missing configuration has its own code and does not attempt a connection", async (t) => {
  delete process.env.NEXT_PUBLIC_API_URL;
  const fetchMock = t.mock.method(globalThis, "fetch", async () => json({}));
  await assert.rejects(apiRequest("/customers"), { code: "QLMS-SETUP" });
  assert.equal(fetchMock.mock.callCount(), 0);
});

test("connection failures hide technical details and never repeat a save", async (t) => {
  const fetchMock = t.mock.method(globalThis, "fetch", async () => { throw new TypeError("private host details"); });
  await assert.rejects(apiRequest("/orders/detailed", { method: "POST" }), (error) => {
    assert.equal(error.code, "QLMS-CONNECTION");
    assert.match(error.message, /Check your internet connection/);
    assert.match(error.message, /may have been saved/);
    assert.doesNotMatch(error.message, /private host/);
    return true;
  });
  assert.equal(fetchMock.mock.callCount(), 1);
});

test("a timeout releases a waiting save without retrying it", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const fetchMock = t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
  }));
  const pending = assert.rejects(apiRequest("/orders/7/payments", { method: "POST" }), (error) => {
    assert.equal(error.code, "QLMS-TIMEOUT");
    assert.match(error.message, /Check the record before you try again/);
    return true;
  });
  t.mock.timers.tick(30_000);
  await pending;
  assert.equal(fetchMock.mock.callCount(), 1);
});

test("the timeout also covers a response body that stops arriving", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  t.mock.method(globalThis, "fetch", async (_url, { signal }) => ({
    ok: true, status: 200, headers: new Headers({ "content-type": "application/json" }),
    json: () => new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new Error("body interrupted")))),
  }));
  const pending = assert.rejects(apiRequest("/orders"), { code: "QLMS-TIMEOUT" });
  await Promise.resolve();
  t.mock.timers.tick(30_000);
  await pending;
});

test("server errors show a support code without exposing the response body", async (t) => {
  t.mock.method(globalThis, "fetch", async () => json({ detail: "database password=secret" }, 500));
  await assert.rejects(apiRequest("/orders/7/payments", { method: "POST" }), (error) => {
    assert.equal(error.code, "QLMS-SERVICE");
    assert.equal(error.status, 500);
    assert.match(error.message, /may have been saved/);
    assert.doesNotMatch(error.message, /database|password|secret/);
    return true;
  });
});

test("HTML errors preserve the status used by sign-in protection", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("<html>private</html>", { status: 401 }));
  await assert.rejects(apiRequest("/orders"), { status: 401, code: "QLMS-SIGNIN" });
});

test("malformed successful JSON is a readable failure, not a raw parser error", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("{broken", { headers: { "content-type": "application/json" } }));
  await assert.rejects(apiRequest("/orders"), { code: "QLMS-RESPONSE" });
});

test("an HTML success page cannot masquerade as a saved order", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("<html>proxy page</html>", { headers: { "content-type": "text/html" } }));
  await assert.rejects(apiRequest("/orders/detailed", { method: "POST" }), { code: "QLMS-RESPONSE" });
});

test("CSV report downloads still return their original text", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("ticket,total\nfixture,300", { headers: { "content-type": "text/csv; charset=utf-8" } }));
  assert.equal(await apiRequest("/dashboard/export"), "ticket,total\nfixture,300");
});

test("Owner expense downloads use the authenticated binary helper and keep its error boundary", async (t) => {
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    assert.equal(options.headers.get("Authorization"), "Bearer fictional-token");
    return new Response("Expense,Amount\n1,200", { headers: { "content-type": "text/csv", "content-disposition": 'attachment; filename="qlms_expenses_current_20261014.csv"' } });
  });
  const result = await apiRequest("/dashboard/reports/expenses/download?format=csv&category=supplies", { token: "fictional-token", responseType: "blob" });
  assert.equal(await result.blob.text(), "Expense,Amount\n1,200");
  assert.equal(result.filename, "qlms_expenses_current_20261014.csv");
  await assert.rejects(apiRequest("/expenses/download", { responseType: "blob" }), { code: "QLMS-RESPONSE" });
});

test("business rules keep a specific action that staff can take", () => {
  const cases = [
    [400, "Username already taken", /Choose another username/],
    [400, "Payment cannot exceed the remaining balance of KES 300.00", /Check the balance/],
    [400, "Record the remaining payment of KES 300 before collection", /record the remaining payment/],
    [400, "Complete the pending clothing check before this order is ready", /complete its clothing check/],
    [400, "Enter a Kenyan mobile number such as 0712 345 678", /Enter a Kenyan mobile number/],
    [409, "This phone number is already saved. Check the matching customer before creating another record.", /Choose the matching customer/],
    [404, "Order not found", /Find it again in Track orders/],
    [403, "Owner access required", /Ask the owner/],
  ];
  for (const [status, detail, expected] of cases) {
    assert.match(responseError(status, { detail }, "/orders", "Try again.").message, expected);
  }
});

test("validation arrays identify a field without exposing internal paths or input", () => {
  const error = responseError(422, { detail: [
    { loc: ["body", "quantity"], msg: "Input should be a valid float: private", input: "private" },
    { loc: ["body"], msg: "Value error, Enter a reason for the discount" },
  ] }, "/orders", "Try again.");
  assert.match(error.message, /Check the quantity/);
  assert.match(error.message, /Enter a reason for the discount/);
  assert.doesNotMatch(error.message, /private|float|body|Value error/);
});

test("unknown and malformed error details do not leak raw server messages", () => {
  for (const detail of ["Traceback private", null, [null, { loc: ["body", "__proto__"] }]]) {
    const error = responseError(422, { detail }, "/orders", "Try again.");
    assert.doesNotMatch(error.message, /Traceback|private|\[object Object\]/);
    assert.match(error.message, /Support code: QLMS-INPUT/);
  }
});

test("unexpected browser errors are hidden while approved staff messages survive", () => {
  assert.doesNotMatch(getUserMessage(new Error("sessionStorage private")), /sessionStorage|private/);
  const expected = new ApiError("Enter your password to continue.", 401);
  assert.equal(getUserMessage(expected), expected.message);
});

test("rate limits provide a wait instruction without automatically retrying", async (t) => {
  const fetchMock = t.mock.method(globalThis, "fetch", async () => json({}, 429));
  await assert.rejects(apiRequest("/orders"), (error) => {
    assert.equal(error.code, "QLMS-BUSY");
    assert.match(error.message, /Wait one minute/);
    return true;
  });
  assert.equal(fetchMock.mock.callCount(), 1);
});
