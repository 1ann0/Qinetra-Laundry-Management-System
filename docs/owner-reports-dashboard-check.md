# Owner reports and dashboard increment

Prepared 14 October 2026. This is the approved reporting/dashboard increment; deployment is authorized by the user's request to release each finished feature. Hosting activation and actual Android acceptance are recorded separately below.

## Implemented

Owner-only Orders, Customer, Service, Payments/returns, Current attention and Catalogue reports share backend calculations across JSON, XLSX and CSV. Filters have an allowlist, repeat/unsupported fields fail, and oversized reports fail explicitly without truncation. Existing `/dashboard/export` remains available. The backend pins XlsxWriter 3.2.9; phones/tickets stay text, KES stay numeric, formulas and automatic links are disabled. Downloads contain definitions, dates, filters and frozen headings. PostgreSQL reports use a read-only repeatable-read snapshot.

The Owner starts on Today at Qinetra: due/late/ready/overdue laundry, holds, outsourcing issues, current debts/refunds and actionable tickets. Money has separately labelled inclusive Nairobi dates, cash/M-Pesa receipts and returns. Receipts are not profit. Employees keep Home, intake, tracking and customer lookup; reports remain denied. Reports use phone cards, searchable choices, desktop tables and visible download feedback. Changing filters disables downloads until the preview is refreshed. Customer-history links preserve the successfully loaded filters.

## Developer proof

- 312 backend tests passed against disposable PostgreSQL with no skips, including migration/reapplication, restricted grants and encrypted isolated restore. Two real PostgreSQL report tests prove concurrent changes cannot mix a snapshot and report transactions cannot write.
- 99 frontend tests and lint passed. The Linux static build produced 20 routes including Reports. The final production HTTPS artifact and exact remote CI are recorded at release; a fixture-origin artifact is never uploaded.
- Hand-calculated fixtures cover mixed-service KES 900 work, partial payment, correction and refund, inclusive dates, separate units, closed-order debts, refund due, cancelled work, formula/link injection, oversize refusal and real Owner/Employee JWT permissions.
- Actual local browser XLSX/CSV downloads were inspected using fictional records only. KES 650 received, KES 50 returned and KES 600 net match the ledger; Excel phones remain strings, monetary cells numeric, with no formulas/hyperlinks. Cash-only preview gives KES 550 received, KES 50 returned and KES 500 net; filter changes disable download.
- At 375px, no page overflow; phone cards expose amounts/methods and expandable details. Owner login lands on Dashboard. Employee direct Reports navigation redirects to Home and its menu has no Owner items. Search finds Fictional Service 61 beyond the initial 50 choices. Screenshots 66/67 contain fictional data only.
- The delayed-download/logout browser attempt reached logout but the browser tool timed out; no complete negative-download observation was obtained. The post-response account/role/token/expiry/inactivity guard is inspected, and authenticated API denial is independently tested. Do not call this a passed browser race test.

## Release and rollback

No database migration or data import is required. Preserve live Worker `cf2c15f9-90c0-4a53-a6dc-3cc7eefbaadd` and pilot API commit `97686708c2f6e4facf574054850847b50bd0dbbd` as the preceding compatible pair. Publish the reviewed feature branch, verify exact CI, deploy the existing auto-deploy-off pilot API, verify readiness/access/CORS, then upload/read back/activate the matching HTTPS frontend. The original practice API follows main and must remain unchanged. No real customer test writes.

Actual Android download, locating and opening each file remains unobserved. Simulated phone widths and desktop download proof are not a substitute. Expenses/closing, isolated hosted demo and memberships remain separate unfinished increments. First automatic scheduled backup invocation remains unobserved; actual manual cloud backup qualification and enabled schedule are recorded in `pilot-cloud-backup-qualified.md`.

## Private Owner acceptance

Sign in privately at the final site after release. Dashboard attention links should open their filtered tickets. Reports -> Shop catalogue should download the 22 services and 30 clothing types, and Employees should remain on daily work. On Android download both Excel and CSV, locate them in Files -> Downloads and open them in a spreadsheet app. Keep credentials and real customer exports outside chat. No practice transactions should be entered into the live pilot for this check.
