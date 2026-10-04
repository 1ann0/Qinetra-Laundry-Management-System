# Employee discount authority check

4 October 2026. Implemented and developer-verified locally. Student reported completing the discount checks; independent step-by-step counts were not supplied. Production migration/deployment and customer-contact acceptance remain open. The student's stale-page explanation was corrected: accepted replay succeeds because the server finds the original save before evaluating a new policy, including after a fresh policy read. Explain-back remains pending.

## Contract and data flow

- `GET /settings/discount-policy`: any current authenticated staff member. Returns `employee_max_discount_percent` as a decimal string, `revision` and nullable `updated_at`. An unseeded policy reads as 0%, revision 0, without inserting on GET.
- `POST /settings/discount-policy`: owner only, `Authorization: Bearer …`, UUID `Idempotency-Key`. Body: `{"employee_max_discount_percent":"10","expected_revision":0}`. Accept finite 0–100 percentages with at most two decimal places and a non-negative integer revision; reject extra fields. The initial ceiling is 0%.
- `GET /settings/discount-policy/history`: owner only; latest 50 before/after changes with actor, revision and time. Internal save references/hashes are omitted.
- Owner Shop setup saves the policy plus one attributed change in a transaction. Stale revisions return `QLMS-STALE-RECORD`, `save_state: not_saved`; reload before editing again. A replay confirms the earlier save and returns the current policy without reverting a newer edit.
- Order entry shows the employee limit and estimates the combined allowance. It rounds each service subtotal to cents before summing, matching the API even for fractional kg. Start next order retrieves the current policy again. FastAPI calculates the undiscounted subtotal from catalogue prices and quantities, sums all line discounts, and checks `floor_to_cents(subtotal × percent / 100)` before writing the order, payment or ticket counter. Owner orders are exempt from the employee ceiling; existing reasons and positive per-service charges still apply.
- Excess employee discounts return HTTP 409, `QLMS-DISCOUNT-LIMIT`, `save_state: not_saved`. Lost replies and unknown conflicts retain their original request/key. Accepted order lookup happens before policy validation, so lowering the ceiling does not invalidate an accepted retry.
- Discounted employee order acceptance and owner policy updates share a PostgreSQL transaction advisory lock, held until commit/rollback. A policy update that commits first governs the new order; an order accepted first remains valid. Zero-discount orders do not need this lock. SQLite browser fixtures do not establish concurrency safety.

Migration `backend/migrations/022_add_employee_discount_policy.sql` creates the singleton policy and append-only application history, seeds 0% without resetting an existing policy, enables RLS and revokes PUBLIC/anon/authenticated access to both tables and the history sequence. Apply only through the reviewed release migration process; qualify the restricted application role separately. No Supabase project was changed here.

## Automated evidence

- Disposable Docker PostgreSQL 17: all **171 backend tests passed**, no skips (66.966 seconds). Includes 10 new HTTP and five PostgreSQL policy tests: permissions, tampered/invalid fields, default 0%, KES 100/100.01 boundary on KES 1,000, split-line bypass, fractional-cent flooring, owner exemption, disabled/revoked users, stale changes, concurrent updates, order/update ordering, retries and migration/browser-role denial. An older pricing fixture now explicitly grants its employee the discount allowance that test requires.
- Final calculation follow-up: a targeted isolated run passed all 10 HTTP policy cases after adding fractional-kg subtotal assertions; the five PostgreSQL cases were intentionally skipped in that targeted run and remain covered by the earlier complete PostgreSQL suite. Two KES 1.33/kg lines at 1.5 kg each round to KES 4 combined, so a KES 2 discount at 50% is valid.
- Frontend: **55 tests passed**, including allowance calculations, per-service cent rounding and definite rejection clearing the pending reference. Lint and production build passed after the next-order refresh and rounding fixes. No dependencies added. The local npm shim is broken; direct Node commands were used.
- Commands from project root: `./backend/tests/run-postgres-tests.ps1 -PythonExecutable 'C:/Users/1ann0/qlms/tmp/test-venv/Scripts/python.exe'`. From `frontend`: `node --test tests/*.test.mjs`, `node node_modules/eslint/bin/eslint.js .`, `node node_modules/next/dist/bin/next build`.

## Developer browser evidence

Local production build at port 3100; separate ignored fixture `tmp/discount-fixture.py` at port 8001 using only `tmp/discount-fixture.sqlite`. No real records or actual cash transfer. The contact fixture remains preserved and inactive on that port.

1. Owner policy 0% → 10% saved while the fixture returned a simulated 503 after commit. Retry notice appeared; after a requested refresh and retry, the page showed 10% and exactly one history event. The owner refresh caused fresh setup reads in API logs.
2. Employee selected the KES 1,000 service. KES 100.01 with a reason was blocked by the whole-order validation without a save. KES 100 and fictional full cash KES 900 were accepted; the reply was deliberately replaced with 503.
3. Owner changed the ceiling to 0%. Employee requested refresh and retried the retained save: ticket `QL-20261004-001`, KES 900 charge/paid, zero balance, one order/payment. The browser reload did not show new setup requests for this employee tab, so this is confirmed retry-after-policy-change evidence, not independent proof of a full employee browser reload. Automated persistence checks and the student's real refresh check remain relevant.
4. Final rebuilt frontend: saved a second fictional KES 900 unpaid order under 10%; owner then set 0%. Start next order immediately showed 0% and disabled Add discount. Earlier stale display was corrected before completion.
5. Read-only fixture check: policy 0%, revision 4; four policy events; orders 1/2 at KES 900 each; exactly one payment, order 1 at KES 900. No duplicate was added by the lost-reply retry. Both fault flags were consumed.

Screenshots 46 (owner policy/history), 47 (accepted order replay) and 48 (full zero-percent form) are fictional developer evidence in `docs/diagrams/evidence/`. A screenshot alone does not prove concurrency or student acceptance.

Open C3 observation: the existing order form and created-result screen showed different promised-ready display times (16:46 versus 13:46) for the first fixture. This increment does not change that formatting; verify Nairobi-time consistency during daily-work acceptance. An initial catalogue read error recovered on re-entry; ordinary read/session reliability remains open.

## Exact student browser checks

Use **only this fictional fixture**, not the production URL. The local servers are left running: frontend `http://127.0.0.1:3100`, backend `http://127.0.0.1:8001`. If restarting, from the project root run `./tmp/test-venv/Scripts/python.exe ./tmp/discount-fixture.py`; in a separate terminal in `frontend`, run `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3100`. The built frontend must target 8001. Do not start the preserved contact fixture on the same port.

Fictional accounts: `discount_owner` and `discount_employee`, both password `DiscountTest123!`. Customer **Discount policy test**, phone **0744444444**. Service **Discount boundary test**, KES 1,000 per item. Developer history already exists; count new events relative to the current baseline.

1. Sign in as owner; open **Shop setup** at `/settings/catalog`. Verify 0%, set **10**, Save employee limit. Open Recent policy changes: one new 0 → 10 event with your username. Leave this tab open.
2. In a second tab sign in as employee; open **New order**. Select the test customer and add one test service, quantity 1. Verify the banner says 10% and up to KES 100. Add discount **100.01**, reason **Student discount check**, leave Not paid yet, then Create order. Expect the maximum-KES-100 message and no ticket. Change to **100** and save: one ticket, KES 900 charge/debt, zero paid. Note the ticket number.
3. In the owner tab set **0** and save. In the employee tab select **Start next order**, add the test service. Expect 0% and Add discount disabled. Open the ticket from step 2: its saved KES 100 discount remains. Employees cannot access Shop setup; direct API permission checks already cover hidden-button bypass.
4. Two owner tabs: open Shop setup in both at the same revision. In A save 10%; in older B attempt 20%. B must say the change was not saved, without a stuck retry notice. Select Reload limit and history in B, confirm 10%, then set 0 and save. No history event for the rejected 20% attempt.
5. Guided lost-reply check: ask the agent to arm `tmp/discount-order-lost-reply.flag` for one fictional save. Set 10% as owner; load a new employee KES 1,000 order with KES 100 discount/reason. Save Not paid yet. Expect Retry previous save. Owner sets 0%; **refresh the employee tab yourself**, then retry. Expect one accepted KES 900 ticket, no retry notice, and no second ticket. Do not resubmit using a fresh save reference.

Explain back: why is the ceiling calculated across the whole order, and why must an already accepted save remain replayable after the owner changes it? Student result and explain-back are pending; record the actual outcome before starting another feature.

## Files in this increment

Backend: `models.py`, `schemas.py`, `main.py`, `discount_policy.py`, `transaction_safety.py`, migration 022, `tests/test_discount_policy.py` and the pricing fixture in `tests/test_detailed_order_contract.py`. Frontend: `lib/discount-policy.js`, `lib/user-messages.js`, `components/settings/discount-policy-settings.js`, owner catalogue/order pages and `tests/discount-policy.test.mjs`. Roadmap, handoff, data/security inventory, premortem and journal record scope, evidence and remaining gates. Local learning/presentation/evidence notes and fixture scripts are ignored working files.

The pre-existing unfinished change in `docs/save-rejection-check.md` was preserved. No production migration, push, deployment, purchase or customer-data export occurred. Release still requires customer-contact acceptance and the launch security/data/recovery/hosting gates in the roadmap.
