# Rejected-save recovery review

22 September 2026. Local developer verification; student acceptance and production deployment remain open.

## Contract

An owner correction sends the values originally displayed, the new values, a reason, confirmation and a UUID in `Idempotency-Key`. The API checks for an already-saved request before checking whether the displayed values are stale. A recognized HTTP 409 with `save_state: not_saved` means this attempt made no write. The frontend clears only that rejected pending attempt and asks the owner to reload and review the current record. An unknown conflict, timeout or lost reply retains the exact request and reference for retry.

Owner routes require `Authorization: Bearer <token>`. Signed sessions last 30 minutes. The kg route is `POST /orders/{order_id}/quantity-corrections`; its JSON fields are `service_line_id`, `expected_quantity`, `new_quantity`, `new_discount_amount`, `reason` and `confirmed`. Success returns `OrderOut`, including current totals and correction history.

## Browser results

The existing local production build was tested at `http://127.0.0.1:3100`, using the disposable in-memory fixture on port 8000. No production database was used.

| Scenario | Observed result |
| --- | --- |
| First tab corrects fictional ticket `QL-NAV-TEST-001` | 2 to 3 kg; KES 450; one audit event |
| Older second tab submits 4 kg | Explicit not-saved/reload message, `QLMS-STALE-RECORD`, enabled correction controls and no Retry previous save button |
| Second tab reloads | 3 kg and one audit event; no record of the rejected correction |
| Second tab submits after reviewing current values | 3 to 4 kg; KES 600; exactly two accepted audit events |
| One-use fixture fault hides the reply to 4 to 5 kg | Other tab shows KES 750 and exactly three events; saving tab retains Retry previous save and disables correction controls |
| Same-tab refresh and retry | Retry remains available, then clears; still exactly three audit events and no duplicate correction |

Screenshot [41](diagrams/evidence/41-local-stale-save-rejected.png) shows the rejected stale form before reload. Its displayed receipt/history are deliberately still the older tab's view. The written checks above separately establish the saved history. The screenshot contains only fictional local data. Existing lost-reply screenshots 37 and 38 were not duplicated.

Two initial order-detail loads showed connection errors and recovered on reload. One password re-entry also needed a reload to load the receipt. Their cause was not established during this increment; include navigation/session recovery in staff rehearsal. They do not change the observed save/retry results and are not evidence that general availability is ready.

## Verification and commit boundary

- Current working tree: all 50 frontend tests and five signed-token HTTP cases passed on 22 September.
- The earlier persisted PostgreSQL log records all 135 backend tests passing in 60.020 seconds, including the unfinished contact draft. That is historical test evidence, not staff acceptance.
- The save-recovery commit is separated from the older customer-contact draft. Its HTTP file has four order-recovery/permission cases; the shared-phone case and its contact-route assertions remain in the unstaged draft.
- The isolated commit candidate passed all 134 backend tests in 27.795 seconds against disposable PostgreSQL on 22 September, with no skips. It has no dependency on migration 020 or the draft customer model. The test container was removed by the runner.
- The runner uses a longer dummy JWT signing key to remove the test-only short-key warning. No deployed secret was changed.
- Frontend lint/build passed in the preceding session. The tested build was created after the save-recovery frontend edits; no frontend code changed during this browser review.
- The public Render `/docs` check could not be completed from this session: the read-only network request timed out. Production API/deployment parity is therefore unverified.

## Files in this increment

| File | Purpose |
| --- | --- |
| `backend/main.py` | Mark stale clothing, stage, kg and ticket-customer changes as definitely unsaved |
| `backend/transaction_safety.py` | Structured rejection helper and uncertain reused-reference contract |
| `backend/tests/test_save_rejection_http.py` | Signed-token owner permissions, rejection without a write, resubmission and replay |
| `backend/tests/test_transaction_safety.py` | Competing PostgreSQL corrections and simultaneous retry |
| `backend/tests/run-postgres-tests.ps1` | Select a working Python executable and use a sufficiently long dummy signing key |
| `frontend/src/lib/user-messages.js` | Recognize safe rejection codes and show clear next actions |
| `frontend/src/lib/pending-save.js` | Clear definite rejections while retaining uncertain attempts |
| `frontend/tests/pending-save.test.mjs` | Exercise both recovery decisions, including malformed/unknown conflicts |
| `docs/support-codes.md` | Staff/support meaning of the recovery codes |
| `docs/save-rejection-check.md` | Contract, review evidence, exact student steps and limitations |
| `docs/pilot-handoff.md` | Current state, unfinished draft and next approved increment |
| `DEVELOPMENT_JOURNAL.md` | Development outcome and verification record |
| `docs/diagrams/evidence/41-local-stale-save-rejected.png` | Distinct local stale-save screenshot |
| `docs/evidence-tracker.md` (ignored) | Evidence provenance; developer and student checks separated |
| `LEARNING_NOTES.md` (ignored) | Learning backlog and pending explain-back |
| `PRESENTATION_NOTES.md` (ignored) | Short explanation and demo line |

The existing customer-contact edits in `backend/models.py`, `backend/schemas.py`, migration 020 and the contact-specific hunks/tests are preserved outside this commit. The ignored `tmp/prepare-save-recovery-review.py` and its generated review copy/patch are local verification helpers only. The one-use fault flag was consumed by the test and is absent.

## Student check

If the local servers have stopped, run these in two PowerShell terminals from the repository root:

```powershell
$env:QLMS_REVIEW_PORT = '8000'
& .\tmp\test-venv\Scripts\python.exe .\tmp\usability-nav-server.py
```

```powershell
Set-Location frontend
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3100
```

Use only this local fixture; its built frontend targets `http://127.0.0.1:8000`, and its CORS origins permit port 3100. Restarting the fixture resets its fictional data. Never replace it with the live database.

1. Open `http://127.0.0.1:3100/login` in two tabs. Sign in separately as `nav_owner` with the fixture password `NavTest123!`.
2. Open Track orders, then `QL-NAV-TEST-001` in both tabs. Expand **Owner: correct billed kg** in both before saving either.
3. Note the starting kg. In tab A, increase it by one, add a test reason, tick the confirmation and save.
4. In the still-older tab B, enter a different kg, add a reason and save. Expect the not-saved/reload message, usable controls and no stuck retry notice.
5. Reload B. Check the accepted kg and exactly one new history event, then enter and save the revised correction. Expect one additional event.
6. For the guided lost-reply check, enable the fixture's one-use fault immediately before saving another correction. Verify the retry notice survives a same-tab refresh, then retry and check that the event appears only once. The agent-run version already passed; student execution is still pending.

Explain back: why is a rejected stale change safe to discard, while a missing reply must keep its original save reference?

Truthful refunds remain the next approved increment. Neither this review nor a local commit authorizes production cutover.
