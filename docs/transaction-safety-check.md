# Phase 2: dependable order and payment saves

Updated 10 September 2026. Local implementation; not deployed. PostgreSQL acceptance is still open.

Implementation commit: `3275e35` on `codex/transaction-save-safety`.

## Why this matters

A lost reply does not prove a save failed. Staff need a safe way to recover the original result.
The new order form also used to create an order and then send a separate payment request. A failure between them could leave the payment unrecorded.

## Data flow

1. The browser stores the exact request and a random save reference in this tab before sending it.
2. The API requires that reference in the `Idempotency-Key` header for both order routes and the payment route.
3. PostgreSQL waits for any in-flight request with the same reference before checking its result. The saved reference, request fingerprint and staff ID identify a replay. Different details or a different staff account get HTTP 409.
4. A new order, service lines and optional initial payment commit together. Full initial payment uses the price calculated by the API. An invalid payment prevents the whole save.
5. A per-date counter allocates ticket numbers within the transaction. It starts above the highest existing suffix, including numbers above 999. Removing a saved order does not lower the counter.
6. Later payments lock their order before checking the remaining balance. Clothing edits carry the revision that staff opened; an old editor cannot replace a newer list. Status updates still allow only the next stage.
7. A successful response clears the browser reference. An uncertain response keeps it, locks the form and shows Retry previous save. Refresh preserves the pending request in the same tab. The retry returns the order with its current status and balance.

The request fingerprint is a comparison value, not encryption. No new frontend dependency was added.
PostgreSQL transaction locks release when the transaction ends. See [PostgreSQL locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS).

## Current verification

| Check | Result |
| --- | --- |
| Backend suite | Latest Docker-backed run: 91 passed, 1 test-setup error, no skips |
| Frontend request/recovery tests | 32 passed |
| Frontend lint | Passed, including the final focus improvement |
| Production build | Passed, including the final focus improvement |
| HTTP with disposable SQLite data | Required header, initial payment, order replay, changed-body rejection, payment replay, revision output and CORS header passed |
| Browser: lost order reply | Saved 2 kg at KES 150/kg and a KES 100 deposit; notice appeared and controls were disabled. After refresh, retry returned ticket QL-20260910-001 with one deposit |
| Browser: lost final payment reply | Saved KES 200, refreshed, saw KES 0 balance and the retained retry action. Retry left exactly two payment rows: KES 100 and KES 200 |
| Browser: mobile | At 390 × 844 the notice scrolled into view, Retry previous save received focus, both Create order buttons were disabled, and Enter recovered the original ticket |
| PostgreSQL migration and concurrency | Five concurrency cases passed. Migration SQL ran twice and existing-record assertions passed; final new-order assertion was blocked by a detached test User object. Full gate remains open |
| Student review | Earlier navigation usability review reported working. This new feature still needs the student's hands-on check |

The simulated failure runs only in ignored `tmp/usability-nav-server.py`, against an in-memory database. It replaces one reply after the save. No real customer or payment was used. Screenshots are test evidence, not proof of a production incident.

## Run the remaining database checks

The earlier Docker startup fault is resolved. On 10 September, both client and engine reported 29.5.2. The script downloaded `postgres:17`, ran all 92 tests and removed its temporary container. The image remains cached locally.

1. Before the next builder run, fix the migration test's session setup: after opening its replacement session, load `self.user` from that session using `self.user_id`. Its old User object belongs to the closed session. No application-code correction is established by this error.
2. This Docker lesson leaves application and test code unchanged. The fixture correction and rerun remain a separate builder step.
3. In Antigravity's PowerShell terminal, run `./backend/tests/run-postgres-tests.ps1` from the QLMS folder.
4. The script creates a temporary `postgres:17` container on local port 55432. It runs the suite and removes its own container. It does not use your saved database credentials. The first run may download the image.
5. The exit gate is all 92 tests passing with no skips. Current result: 91 passed and one `DetachedInstanceError` in the migration test. Do not present the gate as passed.

The PostgreSQL tests cover simultaneous ticket allocation, duplicate order/initial-payment requests, duplicate payment requests, competing partial payments, competing clothing editors, and upgrading existing rows with migration 010 twice. Each test uses its own random schema in a database named `qlms_test`; remote hosts and other database names are rejected.

## Student browser check

Use only the disposable local API on port 8100 and the matching frontend on port 3100. The local accounts are `nav_employee` and `nav_owner`; their fixture password is `NavTest123!`. These credentials do not belong to the live shop.

1. Create a test order with a deposit. Confirm the receipt total, amount paid and balance.
2. For a guided failure test, ask to enable the one-use reply fault before saving. After the notice appears, verify the form and both desktop/mobile save buttons cannot create another order.
3. Refresh the same tab. Select Retry previous save using the keyboard. Confirm the original ticket and one deposit.
4. Repeat with the remaining payment. Refresh after the lost reply. The retry action must remain available even when the order now shows fully paid. Confirm there is only one row for that final payment.
5. With a clothing-tracked test order, open its editor in two tabs. Save the first list. The second tab must ask you to reopen the order instead of overwriting the first list.

Learning checkpoint: explain why keeping the same save reference is safer than generating a new one after a timeout. This is a short optional review, not a quiz required before every change.

## Release and rollback gate

- Do not release this branch until the PostgreSQL checks and student review pass.
- Apply `backend/migrations/010_transaction_safety.sql` to an isolated staging copy first. Confirm historical tickets, prices and payment totals are unchanged. Confirm the backend database role can use `ticket_counters`; anonymous browser roles must not access it.
- The API now requires a header that old frontends do not send. Coordinate the migration, backend and frontend release; require staff to reload before new saves. Do not run old and new order-writing backends together.
- Pause new saves for a rollback. Keep the additive schema and saved references. Review unresolved requests before reverting both app versions; the old backend does not enforce these protections.
- Never clear a pending reference merely to unlock a form. Support must establish the outcome first. Do not hard-delete orders or keyed payments as a correction mechanism.

## Pre-mortem

| Failure | Protection or next action |
| --- | --- |
| Two staff receive the same ticket number | Transactional counter and unique ticket constraint; PostgreSQL race test still required |
| A retry arrives while the first save is unfinished | Transaction-level lock by save reference precedes business validation; PostgreSQL verification remains open |
| A payment is counted twice after a timeout | Same reference and request body on explicit retry; browser and SQLite checks passed |
| Two different payments overpay one order | Order row lock and fresh balance check; PostgreSQL race test still required |
| A stale clothing list overwrites another employee's work | Revision check rejects the older editor; reopen and review before editing |
| Staff close the tab or use a different device during uncertainty | Session storage is tab-local. Keep the tab open; otherwise check the saved record with support before entering a new transaction |
| Browser storage is unavailable or damaged | Block the save and show QLMS-SAVE-STORAGE; do not silently issue another reference |
| Staff cannot see the recovery action after a long form | Scroll the notice into view and focus its button; mobile keyboard check passed |
| Old frontend or insufficient migration privileges cause rejected saves | Coordinated staging/release check; no production deployment in this phase |
| Receipt times differ on devices with a different timezone | Date-only business fields use Nairobi. Some existing timestamp displays use the device zone; record this for a focused follow-up before pilot acceptance |

## File map

| Files | Purpose |
| --- | --- |
| `backend/logic.py` | Transactional ticket counter and explicit money rounding |
| `backend/models.py`, `backend/schemas.py` | Saved references, initial-payment contract, clothing revisions and quantity validation |
| `backend/transaction_safety.py`, `backend/main.py` | Request locking/replay checks and atomic saves |
| `backend/migrations/010_transaction_safety.sql` | Additive database upgrade; not applied live |
| `backend/tests/test_transaction_safety.py`, `test_detailed_order_contract.py`, `run-postgres-tests.ps1` | Unit contracts, direct-call compatibility and isolated PostgreSQL runner |
| `frontend/src/lib/pending-save.js`, `components/orders/use-pending-save.js`, `pending-save-notice.js` | Retain the original request and expose recovery |
| `frontend/src/app/(protected)/orders/page.js`, `orders/[orderId]/page.js` | Connect order/payment forms and send the editor revision |
| `frontend/src/lib/api.js`, `user-messages.js` | Specific retry instructions and safe conflict messages |
| `frontend/tests/pending-save.test.mjs`, `frontend/package.json` | Recovery tests and test command |
| `IMPLEMENTATION_ROADMAP.md`, `DEVELOPMENT_JOURNAL.md`, support/check notes | Phase status, learning requirement, evidence and release limits |

Evidence: [37: recovery notice](diagrams/evidence/37-local-save-recovery.png), [38: recovered payment history](diagrams/evidence/38-local-recovered-payment-history.png). Existing navigation image 34 is unchanged.
