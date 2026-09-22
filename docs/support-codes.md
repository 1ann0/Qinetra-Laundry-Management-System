# QLMS messages and support codes

Support codes identify a problem category. They are not unique incident IDs. No private server response is displayed to staff.

Staff should report the code, time, page and action. Do not ask for passwords, sign-in tokens or customer records.

| Code | Meaning for support | First checks |
| --- | --- | --- |
| QLMS-STALE-RECORD | A correction used older details; this attempt did not save | Reload the page, check the current details, then enter the correction again. This recognized rejection clears its pending save reference. |
| QLMS-PHONE-SHARED | A customer correction needs an explicit shared-number decision; this attempt did not save | Check the matching customer before confirming that the number is shared. The form can be edited again. |
| QLMS-SAVE-CONFLICT | A reference belongs to different saved details or another actor | Preserve the reference and investigate the saved event. Do not discard it or generate a new reference to bypass the conflict. |
| QLMS-CONNECTION | Fetch failed before a usable reply | Check the user's connection, then API reachability, TLS and CORS. A browser failure alone cannot identify the cause. |
| QLMS-TIMEOUT | No complete reply within 30 seconds | Check slow requests, hosting wake-up time and service health. A timed-out save may still finish on the server. |
| QLMS-SETUP | Frontend API address is missing | Check `NEXT_PUBLIC_API_URL` in the environment used to build the frontend. Rebuild after correcting it. |
| QLMS-SERVICE | API or proxy returned HTTP 5xx | Check service health and logs around the reported time. Verify any attempted save before asking for a retry. |
| QLMS-RESPONSE | Successful reply was unreadable or had the wrong format | Check API/proxy responses and frontend compatibility. Check whether a save completed. |
| QLMS-BUSY | HTTP 429 | Check request limits and unusual traffic. Staff should wait before another attempt. |
| QLMS-SIGNIN | HTTP 401 | Check credentials, account state and token validity. Authenticated requests retain 401 so the password dialog still works. |
| QLMS-ACCESS | HTTP 403 | Check the staff role and requested action. Do not bypass owner restrictions. |
| QLMS-NOTFOUND | HTTP 404 | Check the record or route. Staff should find the record from its normal screen again. |
| QLMS-INPUT | Known business rule or HTTP 400/409/422 | Help staff correct the named field or action. Unknown details use a safe general message. |
| QLMS-REQUEST | Other unsuccessful HTTP response | Inspect the request status and service logs. |
| QLMS-LOGIN-REPLY | Login response lacks required identity or token fields | Compare the login response with the frontend contract. Do not expose the token in screenshots. |
| QLMS-ACCOUNT | Renewal or re-entry returned a different account identity | Investigate authentication state. Staff should log out and sign in again. |
| QLMS-UNEXPECTED | Unexpected browser or application exception | Reproduce the action locally and inspect the error. Raw exception messages do not reach staff. |

## Message rules

Phase 2 adds `QLMS-SAVE-STORAGE` when the tab cannot retain/read/clear its original request, and `QLMS-SAVE-PENDING` when an unresolved request blocks a new save. Keep the tab open and establish the saved outcome before clearing anything. For keyed order/payment requests, use Retry previous save. Auth failures retain the key for sign-in recovery. See [transaction recovery](transaction-safety-check.md).

- State the problem in familiar words.
- Give the next action in a separate sentence.
- Use a support code for system failures.
- Keep each instruction short. Use one action per sentence where possible.
- Preserve useful validation instructions. Do not send staff to support for every missing field.
- Do not say a save failed when its result is unknown.
- Do not automatically repeat order, payment, customer or account writes.
- Preserve form values when the result is uncertain. For a recognized stale correction that was definitely rejected, explain that it was not saved before asking the user to reload and re-enter it.

`src/lib/api.js` handles transport failures and the deadline. `src/lib/user-messages.js` translates known errors into staff instructions.
Screen-level catches use `getUserMessage` so unexpected JavaScript errors also receive safe wording.

## Failure review before wider release

| What could go wrong? | Current protection | Remaining work |
| --- | --- | --- |
| Staff mistake a filter for an order update | Stage buttons say View orders; the selected button says Showing these orders | Ask an unfamiliar user to filter without coaching. |
| A slow save succeeds, but staff submit it again | Keyed saves retain the exact request and recognize retries | Release verification must include both lost replies and simultaneous requests. |
| A rejected correction traps the owner in Retry previous save | Only recognized pre-save rejections unlock the form; unknown conflicts retain the reference | Local two-tab and lost-reply checks passed on 22 September; student acceptance remains pending. See `save-rejection-check.md`. |
| The API fails and staff see an empty shop | Tracking shows a load failure and retry action instead of No orders found | Other screens still need hands-on outage checks. |
| A new backend validation rule has no translation | Generic safe message and QLMS-INPUT code | Add its specific instruction when the API rule changes. |
| A slow hosting wake-up exceeds 30 seconds | Finite wait and a clear timeout message | Measure real response times; consider always-on hosting if needed. |
| Nobody receives the support request | The message asks staff to contact support | Agree a real contact and response process before commercial use. No contact details were invented. |
| The site is reachable but cannot complete laundry work | Error handling preserves uncertainty | UptimeRobot, a meaningful API health check, alerts and a recovery procedure remain separate work. |

Clear wording reduces confusion. It does not guarantee availability or provide offline operation.
