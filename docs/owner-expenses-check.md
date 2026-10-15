# Owner expense ledger

Implementation in progress, 15 October 2026; not yet deployed. This is the approved expense increment before till movements and daily closing.

Owner-only `/expenses` creates a paid cost; `/expenses/{id}` reads it and `/expenses/{id}/corrections` appends an attributed correction. Cash and M-Pesa, paid date, category, KES amount, reference and note are supported. Creation and correction require an idempotency reference; concurrent corrections also compare the saved revision. Original details and every correction remain. Reversal preserves history and excludes the current cost from totals. No financial-history deletion route exists.

The phone form retains exact pending save details/references, visibly disables fresh edits until retry resolves, validates dates/decimal amounts/reasons and shows save feedback. Owner navigation, Finance, Dashboard and Reports reach it. Reports add expense paid-date/category/method filters, Excel and CSV, with links to each entry. Dashboard expense figures retain their own displayed dates/snapshot if another section fails. No receipts-minus-costs profit claim.

Business clarification from the Owner: supplies may be bought in bulk and used over time, followed by small top-ups. Outsourcing transport happens when needed. Wages may be weekly/monthly/per-day and deductions are discretionary; Owner pay is also discretionary. Record each actual payment once on its paid date. Wage notes identify the recipient, period and chosen deduction. Outsourcing notes identify transport/dry-cleaner charges and related tickets. An agreed Owner salary may be labelled Wages; personal drawings use the future separate withdrawal control. Inventory consumption, attendance and automatic payroll calculations are outside this increment. General cost totals do not establish a service's margin.

Developer checks: 320 backend tests passed against real disposable PostgreSQL, with concurrent saves/corrections, Employee denial, repeated migrations and encrypted isolated restore of 24 fictional tables. Original expense KES 100 survives its correction to KES 75 in the restored ledger; immutable-history updates and expense deletes are denied to runtime. 103 frontend tests, lint, the 21-route Linux static production build and strict Wrangler upload dry run passed. Final production image: `qlms-owner-expenses-final:20261015`, `sha256:5f68690dcb906f243899f58effbbad58ac81a2749427371d622b8fa54c188a2c`. Windows sandbox initially denied child-process creation; the same fictional test suite passed outside that sandbox.

Local Chrome review at 375px passed zero/excess-decimal rejection with focused errors; committed-save/lost-reply recovery retained exactly one expense and one original event. Correction from KES 250.50 Cash to KES 200 M-Pesa preserved original details; reversal retained history and reduced totals to zero; restoration returned the total to KES 200. Filter edits disabled stale downloads. Both browser-downloaded XLSX/CSV exist and contain the selected Supplies/M-Pesa reversal and history; XLSX archive integrity passed. The download-event observer timed out, but exact downloaded files were independently checked. Wages and outsourcing prompts changed correctly. Native date control retained its maximum date; future-date rejection is covered by backend/frontend automated checks, not a successful browser future-date entry. Screenshots 69/70 show fictional correction history and report download controls. Actual Android expense acceptance and deployment remain pending.

Additive migration 025 adds two tables only. Deployment must apply their restricted runtime/read-only-backup grants and policies, verify browser-role denial and old API readiness before replacing the API. The nightly backup uses whole-schema export; its existing pin must be checked for compatibility with the extra tables, without reading private credentials. Rollback keeps added data/tables and restores the preceding compatible frontend/API pair; it never drops expense history.

## Fictional browser checks

Use the local review fixture, never live practice records:

1. Owner -> Expenses: try future paid date, KES 0 and KES 1.001. Each must show the field error without saving.
2. Record today's Supplies, KES 250.50 Cash, reference Fictional receipt 1 and note Fictional detergent. One confirmation must appear. Open correction history and see the original details.
3. Correct to KES 200 M-Pesa with reason Wrong amount and method. Original KES 250.50 Cash remains; current total becomes KES 200 M-Pesa. Change another screen and confirm a stale correction is refused.
4. Reverse with a reason: the entry/history remains; expense totals become zero. Clearing reversal with a reason restores it.
5. Reports -> Shop expenses: select category/method/dates, apply filters and download both formats. Preview and files must agree; filters changed without refresh disable downloads.
6. At 375px, controls remain readable without page overflow. Employee has no Expense navigation and direct access is denied. Page help shows only the controls currently visible.

Employee browser review passed: no Expenses link in the menu; direct `/expenses` access returned to operational Home. API tests separately prove 401/403 denial. Human Android expense entry/correction/report checks remain separate after deployment. Daily closing, till movements, demo, memberships and receipt improvements remain unfinished.
