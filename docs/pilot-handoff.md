# Qinetra pilot handover

Updated 22 September 2026. Start here when continuing in a fresh task.

## Objective and working rules

Make the single-shop pilot dependable and simple enough for daily use. Finish and verify one increment at a time. Be direct about defects, unfinished work and release limits. The user has approved the reliability fixes below and asked to continue; ask only for missing business decisions or a concrete production cutover approval.

Use the current worktree as the source of truth. Preserve unfinished changes. Do not create a second agent/task that edits these same files while the original task is running.

## Current increment: recover rejected saves

- Known stale corrections and shared-phone decisions now return HTTP 409 with a recognized code and `save_state: not_saved`. The frontend clears that rejected request and gives the user an action.
- Lost replies, unknown conflicts and conflicting reuse of a reference retain the original request. Do not clear every HTTP 409.
- New tests exercise FastAPI routing and real signed tokens, owner restrictions, rejection without a write, successful resubmission and replay. PostgreSQL tests add competing corrections and simultaneous retry.
- Files: `backend/main.py` (rejection sites), `backend/transaction_safety.py` (response contract), `frontend/src/lib/user-messages.js` (safe instructions), `frontend/src/lib/pending-save.js` (recovery decision), `frontend/tests/pending-save.test.mjs`, `backend/tests/test_save_rejection_http.py`, `backend/tests/test_transaction_safety.py` and `backend/tests/run-postgres-tests.ps1`.
- Verified on 22 September: five working-tree HTTP cases and all 50 frontend tests passed. The isolated save-recovery commit candidate passed all 134 backend tests against disposable PostgreSQL (27.795 seconds, no skips). The earlier `tmp/pilot-postgres-check.log` records 135 tests including the contact draft. The runner now uses a longer dummy JWT key; the isolated run emitted no short-key warning. Frontend lint and production build passed in the preceding session.
- Developer browser checks passed on 22 September: two-tab kg rejection unlocked the form, reload/resubmission added only the accepted correction, and a lost reply survived refresh/retry without a duplicate event. Screenshot 41 records the distinct stale-save warning. See `docs/save-rejection-check.md` for exact results, student steps and review limits.
- Save recovery is isolated in the local commit titled `Recover rejected saves without losing uncertain requests`. The older contact-correction draft remains unstaged. Student hands-on acceptance remains pending. No production deployment was performed; this session's public Render `/docs` request timed out.
- The original `backend/venv` points to a removed Python installation. The test runner accepts `-PythonExecutable`; this session uses the working ignored `tmp/test-venv/Scripts/python.exe`. Docker was verified as 29.8.0 after the user started it. Sandbox access to its named pipe required an approved escalation.

## Next approved increment: truthful refunds

- Owner only. Support partial/full service refunds after collection without changing physical order status. Require a reason, original payment, method, actual return date and confirmation that money was returned.
- Keep original payments/prices in history. A service refund reduces the charge as well as retained money; returning excess payment does not reduce the charge again.
- Add `POST /orders/{order_id}/refunds`. Keep earlier payment-adjustment replays valid. Add refund purpose and charge reduction, plus `net_charge` and `refund_due` on order responses. Save related monetary changes atomically, with locks and idempotency.
- Debt is `max(net_charge - net payments, 0)`; money owed back is `max(net payments - net_charge, 0)`. A paid KES 1,000 collected order with a KES 200 service refund ends at KES 800 charged/retained and zero debt, still Collected.
- Let a valid kg correction create excess payment to return. Permit owner payment-entry corrections after collection without falsely changing garment custody. Update receipts, Finance, exports and outstanding totals consistently.
- New forward migration; do not guess the purpose of historical refunds. No automatic money transfer, store credit or compensation beyond the service charge in this increment.

## Existing unfinished work

Customer contact correction was already uncommitted before this increment: model, schema, routes, migration 020 and migration-test integration. Some rejection behavior now has HTTP coverage, but there is no owner UI or complete feature acceptance. Do not call it finished or deploy it accidentally. Review the existing shared-phone case when changing only a name.

The preceding feature commit was `89f07c2` (wrong customer on a saved ticket); the save-recovery follow-up is titled `Recover rejected saves without losing uncertain requests`. Existing local features include garment references/outsourcing, clothing checks/holds, inline customer intake and owner corrections. Several still require representative staff/browser checks.

## Remaining release work, in order

1. Finish verified save recovery and the approved refund correction; complete essential customer contact editing.
2. Reconcile owner totals/filtered exports and provide concise actionable work lists rather than extra charts.
3. Rehearse migration and explicit fresh-schema routing, use a restricted runtime database role, configure approved prices and real individual accounts, and agree opening orders/payments.
4. Prove a backup restore, database-aware health check, UptimeRobot alert and recovery, rollback and paper outage procedure.
5. Complete the staff workflow rehearsal, obtain approval for the exact cutover, deploy matching frontend/backend versions, verify them and start the controlled pilot.

Supabase and Render were last checked on 17 September: backend `5da24e5` from 10 August; protected `qinetra_live` has nine tables and zero users/customers/orders/payments; old and fresh schemas deny browser-role table access. These are dated observations, not a current release guarantee. The app has not been switched to the fresh schema. The Vercel version was not independently confirmed.

Subscriptions, Google OAuth, automated M-PESA prompts, multi-business onboarding and AWS migration stay outside this launch. Google OAuth will be a guided lesson with the user. Physical garment-reference attachment must be agreed with the outside cleaner.

## Browser check for this increment

The agent-run browser sequence below is complete; the student's repetition remains open. Branch: `codex/transaction-save-safety`. Keep the older contact-correction draft separate from the save-recovery commit. Check the development journal and current Git status before continuing. Check server availability before restarting the disposable fixture and frontend. The built frontend uses local API port 8000; the fixture supports `QLMS_REVIEW_PORT=8000` and uses in-memory fictional data. Never substitute the production database for these tests.

Use disposable local data only. Sign in as the fixture owner and open the same received Wash & Fold ticket in two tabs. Save a kg correction in the first tab. Submit a different correction from the older second tab. It must say the change was not saved, show a reload instruction, and leave no stuck Retry previous save notice. Reload, review the new values and save again. Confirm one audit event per accepted correction and no event for the rejection. Separately retain the lost-reply/retry behavior.

Evidence belongs in `docs/diagrams/evidence/`. Add a screenshot only if it proves distinct behavior with fictional data. Update the evidence tracker, development journal, learning notes and presentation notes; identify automated checks separately from the student's acceptance.
