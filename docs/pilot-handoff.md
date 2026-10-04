# Qinetra pilot handover

Updated 4 October 2026. Start here when continuing in a fresh task.

## Objective and working rules

Make the single-shop pilot dependable and simple enough for daily use. Finish and verify one increment at a time. Be direct about defects, unfinished work and release limits. The user has approved the reliability fixes below and asked to continue; ask only for missing business decisions or a concrete production cutover approval.

Use the current worktree as the source of truth. Preserve unfinished changes. Do not create a second agent/task that edits these same files while the original task is running.

## Current continuation

- The user approved the full Qinetra-first implementation plan. The [roadmap](../IMPLEMENTATION_ROADMAP.md) now records the zero-spend constraint, separate free-allowance Supabase project, owner-configured whole-order employee discount ceiling (initially 0%), daily encrypted backup/independent copy, one-day reconstruction/four-working-hour recovery targets and ten receipt-backed trading days.
- Keep Render/Supabase for now. Cloudflare/OpenNext is a separate fictional-data qualification; Railway remains an alternative. No paid resources, framework replacement, database provisioning, push or deployment was performed.
- S0 is locally verified: Next.js/eslint-config-next 16.3.6, compatible lockfile fixes, 50 tests, lint/build, audit result and browser evidence in [the patch record](security-patch-check.md). Product, architecture, data and security documents exist and explicitly distinguish requirements from implemented controls.
- Browser smoke initially encountered receipt-load errors in the old shared-connection SQLite fixture. The fresh temporary-file fixture passed employee receipt loading, a KES 100 fictional payment and refresh with one payment/KES 200 balance. Broader old-tab/reauthentication review remains S1c/C3; do not claim it is fixed.
- Current local fixture (4 October): ignored `tmp/discount-fixture.py`, port 8001, production-built frontend at 3100. It forces a separate `tmp/discount-fixture.sqlite`, with fictional `discount_owner`/`discount_employee` accounts; see [the discount checks](discount-policy-check.md). Current ceiling 0%, revision 4; two developer orders and one fictional payment. The earlier `tmp/contact-fixture.py` and `.sqlite` remain preserved, not running on this port. Student contact customer #3 is still **Student contact test**, phone 0733333333, in that separate dataset; use [its acceptance steps](customer-contact-check.md) only after switching fixtures safely. The earlier refund fixture remains separate.
- Refund student acceptance passed; see [the refund check record](refund-check.md). Customer contact correction is now locally implemented and developer-verified (156 backend tests including PostgreSQL, 52 frontend tests, lint/build and focused browser checks). Student contact acceptance remains pending. Expired-session recovery and other security/data/hosting/trial gates remain open.
- Employee discount authority is locally verified on 4 October: all 171 backend tests passed against disposable PostgreSQL, no skips; 55 frontend tests, lint/build and fictional browser checks passed. Migration 022, owner setting/history and combined whole-order enforcement are implemented. Lost-reply order retry survived a subsequent 0% policy; Start next order now refreshes the displayed limit. Student discount acceptance and production migration/deployment remain open. The existing unfinished `docs/save-rejection-check.md` change was untouched.
- The roadmap retains the later Excel/CSV daily-control workbook, privacy-reviewed founder AI assistance, private measured-value view, editable future memberships, monitoring candidates and prior development inventory. These are planned work, not additions implemented by the discount feature. One active agent remains the default; Medium is appropriate for routine follow-up, High for money/permissions/concurrency and Low for bounded docs.

## Completed local increment: recover rejected saves

- Known stale corrections and shared-phone decisions now return HTTP 409 with a recognized code and `save_state: not_saved`. The frontend clears that rejected request and gives the user an action.
- Lost replies, unknown conflicts and conflicting reuse of a reference retain the original request. Do not clear every HTTP 409.
- New tests exercise FastAPI routing and real signed tokens, owner restrictions, rejection without a write, successful resubmission and replay. PostgreSQL tests add competing corrections and simultaneous retry.
- Files: `backend/main.py` (rejection sites), `backend/transaction_safety.py` (response contract), `frontend/src/lib/user-messages.js` (safe instructions), `frontend/src/lib/pending-save.js` (recovery decision), `frontend/tests/pending-save.test.mjs`, `backend/tests/test_save_rejection_http.py`, `backend/tests/test_transaction_safety.py` and `backend/tests/run-postgres-tests.ps1`.
- Verified on 22 September: five working-tree HTTP cases and all 50 frontend tests passed. The isolated save-recovery commit candidate passed all 134 backend tests against disposable PostgreSQL (27.795 seconds, no skips). The earlier `tmp/pilot-postgres-check.log` records 135 tests including the contact draft. The runner now uses a longer dummy JWT key; the isolated run emitted no short-key warning. Frontend lint and production build passed in the preceding session.
- Developer browser checks passed on 22 September: two-tab kg rejection unlocked the form, reload/resubmission added only the accepted correction, and a lost reply survived refresh/retry without a duplicate event. Screenshot 41 records the distinct stale-save warning. See `docs/save-rejection-check.md` for exact results, student steps and review limits.
- Save recovery is isolated in local commit `d6559aa`, `Recover rejected saves without losing uncertain requests`. The older contact-correction draft remains unstaged. On 25 September the student confirmed both two-tab rejection/reload/resubmission and lost-reply/refresh/retry. Browser inspection verified one 4 to 5 kg "lost reply test" event, KES 750 and no retry notice; the fault flag was consumed. Explain-back remains pending. No production deployment was performed; the 22 September public Render `/docs` request timed out.
- The original `backend/venv` points to a removed Python installation. The test runner accepts `-PythonExecutable`; this session uses the working ignored `tmp/test-venv/Scripts/python.exe`. Docker was verified as 29.8.0 after the user started it. Sandbox access to its named pipe required an approved escalation.

## Completed local increment: truthful refunds

- Owner only. Support partial/full service refunds after collection without changing physical order status. Require a reason, original payment, method, actual return date and confirmation that money was returned.
- Keep original payments/prices in history. A service refund reduces the charge as well as retained money; returning excess payment does not reduce the charge again.
- Add `POST /orders/{order_id}/refunds`. Keep earlier payment-adjustment replays valid. Add refund purpose and charge reduction, plus `net_charge` and `refund_due` on order responses. Save related monetary changes atomically, with locks and idempotency.
- Debt is `max(net_charge - net payments, 0)`; money owed back is `max(net payments - net_charge, 0)`. A paid KES 1,000 collected order with a KES 200 service refund ends at KES 800 charged/retained and zero debt, still Collected.
- Let a valid kg correction create excess payment to return. Permit owner payment-entry corrections after collection without falsely changing garment custody. Update receipts, Finance, exports and outstanding totals consistently.
- New forward migration; do not guess the purpose of historical refunds. No automatic money transfer, store credit or compensation beyond the service charge in this increment.

## Customer contact correction: student acceptance pending

The older draft is completed locally with an owner editor/history, existing migration 020, direct permissions/validation/replay tests and PostgreSQL race checks. Name-only edits do not need renewed shared-phone approval; changed phones require explicit confirmation when a match exists. No customer merging or order reassignment occurs. See [customer-contact-check.md](customer-contact-check.md) for files, contract, developer evidence and the pending student check. No production migration/deployment occurred.

The preceding feature commit was `89f07c2` (wrong customer on a saved ticket); the save-recovery follow-up is titled `Recover rejected saves without losing uncertain requests`. Existing local features include garment references/outsourcing, clothing checks/holds, inline customer intake and owner corrections. Several still require representative staff/browser checks.

## Remaining release work, in order

1. Complete student discount acceptance using [the current fictional fixture](discount-policy-check.md), and the separate pending contact acceptance. Both features are locally implemented; the student service-refund repeat passed. Do not rebuild either feature. Explain-back remains a learning task. Check the observed promised-time formatting mismatch and ordinary read recovery during C3.
2. Close launch security gaps, ordinary session/read recovery and remaining staff/clothing/money scenarios. Reconcile existing Finance/export figures and lookup. Extra work lists/pagination/filtered exports follow the trial unless a concrete failure requires them earlier.
3. Prepare a separate Supabase project within the free allowance; rehearse full migrations and restricted runtime access, approved catalogue/accounts and opening records. Do not silently reuse the old schema or spend money if no free slot is available.
4. Prove restore targets, database-aware readiness, alert delivery/recovery, compatible release rollback and the receipt reconciliation procedure. Qualify the frontend and check free-plan/commercial-use limits.
5. Obtain approval for the exact tested release/data setup, then run ten trading days alongside existing receipts with daily reconciliation. The trial is not permission to discard manual records or rely permanently on free hosting.

Supabase and Render were last checked on 17 September: backend `5da24e5` from 10 August; protected `qinetra_live` has nine tables and zero users/customers/orders/payments; old and fresh schemas deny browser-role table access. These are dated observations, not a current release guarantee. The app has not been switched to the fresh schema. The Vercel version was not independently confirmed.

Subscriptions, Google OAuth, automated M-PESA prompts, multi-business onboarding and AWS migration stay outside this launch. Google OAuth will be a guided lesson with the user. Physical garment-reference attachment must be agreed with the outside cleaner.

## Historical save-recovery browser check

The historical save-recovery browser sequences below are complete as of 25 September; explain-back remains on the learning backlog. Branch: `codex/transaction-save-safety`. The current refund checks use a different temporary-file fixture described in refund-check.md, including its already-tested values. Keep the older contact-correction draft separate. Check the development journal, Git status and server availability before continuing. Never substitute the production database for a disposable test fixture.

Use disposable local data only. Sign in as the fixture owner and open the same received Wash & Fold ticket in two tabs. Save a kg correction in the first tab. Submit a different correction from the older second tab. It must say the change was not saved, show a reload instruction, and leave no stuck Retry previous save notice. Reload, review the new values and save again. Confirm one audit event per accepted correction and no event for the rejection. Separately retain the lost-reply/retry behavior.

Evidence belongs in `docs/diagrams/evidence/`. Add a screenshot only if it proves distinct behavior with fictional data. Update the evidence tracker, development journal, learning notes and presentation notes; identify automated checks separately from the student's acceptance.
