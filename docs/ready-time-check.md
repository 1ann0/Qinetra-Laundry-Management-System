# Nairobi promised ready time

5 October 2026. First increment of the approved real-data-pilot plan. Locally verified; student repeat and live release remain separate.

## Cause and change

The old form mixed two meanings for a value without a timezone. Review treated `2026-10-06T10:00` as UTC and displayed 13:00 Nairobi; submission treated it as the device's local time. The reproduced Nairobi-device result was 10:00 entered, 13:00 reviewed and 10:00 on the saved receipt. On another device timezone, submission could save a different promise.

- `frontend/src/lib/promised-ready-time.js`: interprets form values as Nairobi time, converts to UTC explicitly, rejects invalid dates by round trip, validates against the current instant and formats suggestions in Nairobi. The longest service estimate and optional peak-time hour are retained.
- `frontend/src/app/(protected)/orders/page.js`: uses the same helpers for suggestion, validation, review and submission. The field says **Ready by (Nairobi time)**. `2026-10-06T10:00` becomes `2026-10-06T07:00:00.000Z`.
- `frontend/tests/promised-ready-time.test.mjs`: six checks cover conversion, invalid dates, future-time validation, suggestions, midnight rollover and separate Node processes in Nairobi, UTC and New York, including a daylight-saving boundary.

Existing `format-nairobi.js` still handles UTC and legacy saved timestamps. Pending-save storage, bodies, account/destination scope and request references were not changed. A pending accepted or uncertain save uses its original timestamp; it is not recalculated from the current form.

Supporting files changed:

- `IMPLEMENTATION_ROADMAP.md`: approved pilot order, hosting gates and this increment.
- `docs/pilot-handoff.md`: current verification and next remaining checks.
- `docs/order-feedback-check.md`: student-reported acceptance and pointer to the fixed time issue.
- `docs/skills-workflow-guide.md`: installed skill scope, selection and economical use across projects.
- `DEVELOPMENT_JOURNAL.md`: dated implementation evidence.
- Local ignored `AGENTS.md`, `LEARNING_NOTES.md`, `PRESENTATION_NOTES.md` and `docs/evidence-tracker.md`: skill/release instructions, learning status, demo explanation and screenshot attribution.
- `docs/diagrams/evidence/52-local-nairobi-ready-review.jpg` and `53-local-nairobi-ready-receipt.jpg`: fictional browser evidence. `docs/save-rejection-check.md` remains untouched and excluded from this commit.

## Current developer evidence

- The old inconsistency was reproduced before the change. Six new tests pass. All **72 frontend tests**, lint and the production build pass. Run from `frontend`: `node --test tests/*.test.mjs`, `node node_modules/eslint/bin/eslint.js .`, `node node_modules/next/dist/bin/next build`.
- The existing saved-time and pending-save regression tests passed in that suite. No backend, migration or dependency changed; PostgreSQL tests were not rerun for this frontend-only increment.
- Restarted the verified old local frontend so the browser tested the fresh production build. The fictional backend remains at port 8001 and forces `tmp/discount-fixture.sqlite`; `.env.local` points the frontend at that API.
- Native keyboard entry of 6 October 2026, 10:00 showed 10:00 in review. The field label and input were readable at 375 × 812; the document did not overflow horizontally. Broader enlarged-text, screen-reader, reduced-motion and staff workflow acceptance remain in the next increment.
- Saved one unpaid fictional order: **#7 / QL-20261005-001**, KES 1,000 charge, KES 0 paid, KES 1,000 balance. The result and full receipt show **6 Oct 2026, 10:00**, including after receipt refresh. SQLite stores `2026-10-06 07:00:00.000000`, the UTC instant. Orders increased from six to seven; payments remained three, with none on this order. Existing records were preserved.
- Screenshots `52-local-nairobi-ready-review.jpg` and `53-local-nairobi-ready-receipt.jpg` show the review and receipt. These are fictional developer evidence, not student acceptance or production records.

## Exact student repeat

Use only `http://127.0.0.1:3100`, the fictional fixture. Sign in as `discount_employee`, password `DiscountTest123!`. The existing customer is **Discount policy test — 0744444444**; the service is **Discount boundary test**, KES 1,000 per item, no clothing list. The current employee policy is 10%; this check needs no discount or policy change. Preserve existing orders.

1. Open New order, select that customer and add that service with quantity 1. Leave **Not paid yet** selected.
2. Set **Ready by (Nairobi time)** to **6 October 2026 at 10:00**. Pass: the review says **6 Oct 2026, 10:00**, not 13:00. If testing after that time, use a future day at 10:00 instead.
3. Temporarily choose a past ready time and click Create order. Pass: no ticket is created; the time field comes into view with **The promised completion time must be in the future.** Restore the future date at 10:00.
4. Click Create order once. Pass: one ticket, KES 1,000 total/balance, KES 0 paid, and the same 10:00 ready time. Open full receipt, then refresh it. Pass: the same ticket and 10:00 remain; no payment was created.
5. At phone width, confirm the time label/input stay readable and keyboard focus remains visible when editing. Report any obscured control. Do not change the computer clock or send a WhatsApp message for this check.

The important idea: the customer's promise is Nairobi time. QLMS subtracts three hours to store UTC and adds three hours when displaying the saved promise. Explaining that back is a learning exercise, not a release veto.

## Release position

No push, deployment, database provisioning or real-data entry. Staff acceptance, launch security, separate dataset/restricted credentials, tested encrypted recovery, readiness/alerts, hosting qualification and compatible release/rollback remain open in the master roadmap. This fix alone does not satisfy those gates.
