# Daily closing — release qualification

Status: implemented and under local qualification on 16 October 2026. **Not deployed.** Live remains expense-funding source 754e778 / schema 026 until the release evidence below is completed.

## Behaviour and shop decision

The Owner chooses a Nairobi business date, reviews its recorded activity, enters starting cash, counted cash and the shop M-Pesa statement's collected/returned totals, explains differences and confirms. Expected cash includes corrected cash receipts, actual cash refunds, shop-funded cash expenses and separately recorded additions/Owner withdrawals. Personally funded expenses remain business costs and do not reduce till cash. Unconfirmed cash payers block confirmation rather than being guessed.

Cash movements are separate from expenses and income. They use the existing save references, revisions and attributed correction history. Reversing excludes a movement from current totals and preserves its history. Owner withdrawals do not establish a salary or tax treatment.

Confirmations are immutable versions. Later source changes mark the date Needs review, including equal-net changes and moving a transaction to another date. Reconfirmation appends a version and requires a fresh explanation. Exact pending bodies/account/API/date/references survive reload; retry resolves the original attempt before new validation. Employees have no access.

M-Pesa comparisons are manual statement checks, not automatic transaction verification, account balances or expense-payment reconciliation. Opening cash is entered explicitly; no historical opening balance or profit is invented. Day reports are bounded to 366 selected dates and the existing 5,000-source-row limit, failing explicitly rather than truncating.

## Developer proof

- Test-first failures covered the missing calculations/routes/migration/batch helper, future-date error, exact decimal-text response and report/download integration. Shared corrected-payment calculations and report transaction setup are reused.
- Actual disposable PostgreSQL run: **375 tests passed**, no skipped PostgreSQL suite. Simultaneous same-reference and competing-reference confirmations, a deliberately waiting replay and a payment committed during the read snapshot are covered. Full migration chain/repeat/empty restore passed. Restricted runtime/backup rights, browser denial and encrypted separate-database recovery passed for **27 fictional tables**, 29.7 seconds. Fixture archive sizes are not live storage forecasts.
- Subsequent release-smoke regression: **12 tests passed**, including conditional closing/till contract and seven anonymous denials while preserving older release-manifest support.
- The first production frontend passed 122 tests/lint/static build/strict offline upload. Actual phone-width downloads exposed the shared API helper's missing closing/till allowlist. A failing download regression reproduced it; both names were added without widening other paths. Fresh frontend run: **123 tests passed**; final lint/build and actual file checks remain to be recorded.
- At 375 × 812, the form blocked closing for an unknown cash payer. An attributed expense correction confirmed Owner's money while retaining the original unknown payer. Starting 200 + corrected cash receipts 1,000 − cash refunds 100 − till-funded costs 150 + additions 50 − withdrawals 100 = **900 expected**; counted 850 showed **KES 50 short**. Statement totals 700/50 matched. Missing explanation was rejected.
- A deliberately lost committed response retained the exact pending confirmation after reload. Explicit retry showed confirmation 1 saved once; independent fictional record count was one. A repeated confirmation with its now-cleared explanation was rejected.
- Correcting the withdrawal from 100 to 80 flagged Needs review. A new explained confirmation saved expected 920/count 870/50 short. Expanding history showed original expected 900/count 850 unchanged. Two versions, one business day.
- Screenshots 82/83 show fictional variance and the new signed confirmation at phone width. Inputs measured 48px; primary/load actions 46px; no horizontal overflow (375 viewport, 360 document). Existing 40px Log out is unchanged. This is browser emulation, not actual Android hardware acceptance.

## Release gates still open

Finish fresh frontend build and spreadsheet file verification, Employee browser denial and focused manual review. Then stage only this feature, run secret/diff checks and exact candidate CI. Obtain an actual cloud backup before applying pilot-only migration 027 plus the rehearsed runtime/backup grants. Verify old API readiness, deploy the exact compatible API and matching HTTPS frontend, run the full manifest smoke and another cloud backup. Record provider source, schema, Worker version/traffic and safe public evidence. Do not add fictional ledger records to production.

## Rollback

Restore the previous frontend version c49202af-632f-4c14-addb-237c6b77005e **while retaining the new compatible API and schema 027**. Core workflows remain available, but the previous UI cannot open daily closing or cash movements. Restore the new frontend to resolve any new pending references. Do not drop the new tables, rewrite snapshots, remove expense funding or roll back to an API that rejects new pending bodies. Prefer a compatible forward fix.

## Skills and review

Superpowers bounded design/TDD/systematic debugging/verification require reproduced failures, real PostgreSQL races and separate local/hosted claims. Ponytail Full/manual review reuses the save/report/expense/auth boundaries and installed spreadsheet writer; no dependency was added. UI/UX Pro Max informed explicit manual counts, progressive signed details, large controls, focused inline errors, correction links and waking feedback. Supabase guidance supports additive private/RLS tables and tested restricted grants; the existing numbered migration chain takes precedence over introducing a second CLI migration system. Render/Cloudflare release skills apply to the existing services and exact-version verification.

No new live financial records, automated payments, historical opening balances, payroll or independent backup trigger are included. The late scheduled-backup timing problem remains open separately.
