# Truthful refunds — local acceptance

Updated 29 September 2026. Local implementation; no production deployment or real money transfer.

## Verification record

- **29 September student repeat passed:** after the student reported completion, browser inspection and an agent refresh of `QL-20260929-002` (`/orders/4`) confirmed one KES 60 cash service refund, reason `single garment not washed`, KES 240 net charge/retained money, zero debt/refund due and unchanged Collected status. Original payment remains KES 300. This completes the requested hands-on service-refund check; explain-back remains on the learning backlog. No production deployment.

- **29 September form follow-up:** `payment-corrections.js` now starts without an action or refund purpose selected, previews the resulting charge/retained money/debt, and clears confirmation when details change. All 52 frontend tests, lint and production build passed. Browser checks on fresh fictional receipt 3 verified blank-choice gating, KES 60 entry-correction versus service-refund previews, confirmation reset, and a lost reply followed by refresh/retry with one KES 60 refund (charge/retained KES 240, zero debt/refund due, still Collected). Backend code was unchanged and its suite was not repeated. Screenshot 44 shows the preview and explicit refund confirmation. Expired-session reauthentication required a receipt refresh; this remains in the separate session-recovery launch review.

- **29 September student check:** the student reported completion. Read-only browser inspection of ticket 1 found the additional KES 100 saved as `entry_error`, with reason `further refund test`, rather than a service refund. Current values: net charge KES 800, retained KES 700, debt KES 100, original service refund KES 200, still Collected. This is consistent with an entry correction but does **not** pass the intended refund acceptance check. Preserve the history; repeat the service-refund check on a fresh fictional receipt. This also exposes a form-selection usability issue to address before shop use. No further financial event was created by the agent.

- Working-tree backend: **146 tests passed**, including disposable PostgreSQL 17 concurrency and migration checks; no skips. Separate requests cannot over-refund; same-key concurrent retries create one event; a racing kg correction cannot make the charge negative. Migration 021 repeats and leaves older refund purposes unknown.
- Exact staged backend, copied without the unfinished contact-correction draft: **145 tests passed** in a second disposable PostgreSQL run, with no skips. The one additional working-tree test belongs to that separate draft.
- Frontend: **52 tests passed**, lint passed, Next.js 16.3.6 production build passed. Receipt tests cover both refund meanings and collected status.
- Agent browser acceptance: the fictional KES 200 service refund saved despite a deliberately lost reply. Refresh preserved Retry previous save; retry produced one refund, KES 800 charge/retained money, zero debt/refund due, still Collected. The KES 150 excess return left the corrected charge at KES 150 and cleared refund due. Inactivity reauthentication resumed the second receipt.
- Finance displayed the hand-calculated combined KES 1,150 booked value, KES 200 service refunds, KES 950 net charge, KES 1,300 receipts, KES 350 returned and zero outstanding/refund due. Authenticated CSV retrieval and both order responses matched, with one refund event each and Collected unchanged.
- Employee browser check passed: receipt/history showed KES 800 charge and retained money, zero debt and Collected, with no owner correction/refund controls. Direct employee refund requests were rejected in HTTP tests.
- Screenshots 42 (refund due before return) and 43 (Finance net charge) are local developer evidence in `docs/diagrams/evidence/`. They do not represent student actions or real customers. Student service-refund acceptance is recorded above; explain-back remains pending.

## Files in this increment

- `backend/models.py`, `backend/schemas.py`: refund purpose, derived charge/refund due and request/response validation.
- `backend/main.py`: owner refund route, replay/locking, corrected payment/quantity rules, Finance and CSV values.
- `backend/migrations/021_add_refund_purpose.sql`: additive purpose column/constraint, no guessed historical values or new grants.
- `backend/tests/test_refunds.py`, `backend/tests/test_payment_corrections.py`, `backend/tests/test_order_corrections.py`, `backend/tests/test_transaction_safety.py`: money, permissions, legacy replay, migration and concurrency evidence.
- `frontend/src/components/orders/payment-corrections.js`, `frontend/src/components/orders/quantity-correction.js`: explicit refund purpose, separate retained retry state and truthful correction feedback.
- `frontend/src/app/(protected)/orders/[orderId]/page.js`, `frontend/src/app/(protected)/orders/status/page.js`, `frontend/src/app/(protected)/customers/search/page.js`, `frontend/src/app/(protected)/finance/page.js`: consistent owner/employee amounts and labels.
- `frontend/src/lib/order-receipt.js`, `frontend/tests/order-receipt.test.mjs`: customer receipt wording and tests.
- `ARCHITECTURE.md`, `DATA.md`, `IMPLEMENTATION_ROADMAP.md`, `docs/pilot-handoff.md`, `DEVELOPMENT_JOURNAL.md`, this record: contracts, status, release limits and acceptance instructions.
- Ignored local `LEARNING_NOTES.md`, `PRESENTATION_NOTES.md`, `docs/evidence-tracker.md`: explain-back backlog and screenshot provenance. Existing contact-correction draft is preserved separately.

## What the owner records

- `POST /orders/{order_id}/refunds` requires an owner Bearer session, `Idempotency-Key`, original `payment_id`, `refund_purpose`, `refund_method`, amount, reason, actual `effective_date` and `confirmed: true`.
- `service_refund` reduces the charge and retained money together. `excess_payment` returns money owed after a correction without reducing the charge twice.
- Original payments and prices remain visible. Debt is `max(net_charge - amount_paid, 0)`; refund due is `max(amount_paid - net_charge, 0)`. Full service refunds show Settled.
- Collected remains Collected, with its original collection timestamp. An owner can correct a payment or billed kg after collection; a remaining real debt is visible and only the owner can record its replacement payment.
- Refund amount cannot exceed the selected payment's remaining money, or the relevant charge/refund due. Legacy payment placeholders cannot be refunded as confirmed Cash/M-PESA receipts.
- Earlier accepted adjustment requests still replay. New refunds on the old ambiguous endpoint are rejected with a direction to use the current form. Older refund purposes remain unclassified; investigate them before relying on historical balances.

## Reporting meanings

Receipts, order screens, customer history and status work lists use the current net charge/balance. CSV preserves the original total and adds Service Refunds, Net Charge and Refund Due; Effective Order Value is the net charge.

Finance keeps booked order/service values before service refunds and separately shows current net charge, service refunds and money still due back for the selected **order dates**. Payments received remain on their receipt dates (restated for entry mistakes); refunds sent are cash out on actual return dates. Thus a refund today can affect an older order's net charge while appearing in today's cash movement. These figures are not profit.

## Exact browser checks — fictional data only

The ignored `tmp/refund-fixture.py` is a disposable local API on port 8000. It creates two already-collected fictional tickets and owner/employee accounts; it never reads the real database URL. Test frontend: `http://127.0.0.1:3100`.

1. Sign in as `nav_owner` with local dummy password `NavTest123!`. Open `/orders/1`, ticket `QL-REFUND-TEST-001`. Starting values: total/paid KES 1,000, zero balance, Collected. Its KES 500/kg rate is fictional test data.
2. In Payment corrections and refunds, select Money returned, Service refund, KES 200, Cash, today's date. Enter `Fictional service refund test` and confirm the fictional return. Save refund.
3. Expect original total/payment KES 1,000, net charge KES 800, money retained KES 800, zero balance/refund due, one KES 200 history event, still Collected. Refresh and verify the same values.
4. For lost-reply testing, arm the one-use flag **before step 2** with `New-Item tmp/refund-lost-reply.flag -ItemType File`. The fixture saves once then returns a deliberate 503. Expect Retry previous save, a locked form and the original save reference. Refresh and retry; expect exactly the single refund in step 3.
5. Open `/orders/2`, ticket `QL-REFUND-TEST-002`, paid KES 300 for 2 kg. Under Owner: correct billed kg, correct to 1 kg with a reason and confirmation. Expect charge KES 150, retained KES 300, refund due KES 150, zero debt, still Collected. Return KES 150 using **Return excess payment**. Expect charge and retained money both KES 150; refund due zero.
6. Check today's Finance and downloaded CSV: across these two fixtures, booked value KES 1,150, service refunds KES 200, net charge/retained money KES 950, money received KES 1,300, refunds sent KES 350, zero outstanding/refund due. Original payments still total KES 1,300.
7. Sign out and sign in as `nav_employee` using the same dummy password. History and truthful totals are visible; owner refund/correction controls are absent. Direct API tests must also reject employee refunds.

Student acceptance and explain-back remain separate from agent checks. Explain why returning excess payment must not reduce the corrected service charge again. Evidence should show the collected receipt with truthful totals/history and the recovery result.

### Continue with the currently running fixture

The student repeat on **QL-20260929-002**, `/orders/4`, is complete: KES 240 charge/retained money, zero debt/refund due, one KES 60 service refund and Collected. Do not repeat the save on this receipt. Receipt 1 preserves the earlier entry correction; receipt 3 is the completed agent test. The initial two-receipt Finance totals above are historical and do not include these new receipts.

## Release requirements

Apply migration `021_add_refund_purpose.sql` before starting the new backend, then deploy the matching frontend after the normal release gates. The migration adds a nullable purpose and a constraint, preserves old records, and changes no grants. Do not run an older money-writing backend after new service refunds exist: it does not understand charge reductions. Preserve backups and use a reviewed forward fix or restore procedure for rollback; do not drop refund history.

This increment does not clear launch security, separate-data, backup/restore or hosting gates. No real customer trial is started by local acceptance.
