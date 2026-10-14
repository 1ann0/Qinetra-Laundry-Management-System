# Owner reports and dashboard increment

Released 14 October 2026. This is the approved reporting/dashboard increment; deployment is authorized by the user's request to release each finished feature. Actual Android acceptance remains separate below.

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

**Actual release:** source `bf00780b11ef06950713acd02252c46d7ec782e8`, [CI 38553520017](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38553520017) passed both jobs and every step. Render pilot deployment `dep-db7m5d49v7es73ci4j7g` is Live at that exact source, finished 14 October 14:09:34 Nairobi. Anonymous reports are 401; readiness is 200/ready; private headers and allowed-origin Content-Disposition exposure passed. No staff credential or live record contents were inspected.

HTTPS frontend image `sha256:7f0e4073618007dbbe93465374f319167bdc21d05c2efebe765f5bc7f2dc07fb` passed all 99 frontend checks, lint, 20-page static build and offline strict Wrangler dry-run. Public manifest SHA256 `81554571d5b44288e603770e142ba27c1524dc594e5f80ac7b79c152283ba861`. Cloudflare plugin reused a short-lived encrypted asset grant; 94 new unique assets uploaded across three buckets, covering 129 public paths. No private account token was read or renewed. The grant/key were cleared from local memory. Worker `975d3ecc-87d9-4d55-bb6e-52456a38dd15` (version 8, 1ms startup) and `_headers` were read back byte-for-byte before activation. Routing, public API binding and compatibility policy match the preceding version.

Deployment `0c374058-7fe5-4caf-bdbc-096099406d6c` is independently read back at 100%, activated **14 October 14:15:31 Nairobi**. All **129 public asset SHA256 hashes** match; login/dashboard/reports/privacy return 200 with the expected private/CSP/HSTS/frame policy. The anonymous browser login page renders normally. Python's default client signature returned Cloudflare 1010; the explicit `QLMS-release-verification/1.0` client passed without any security-setting change. [Public asset manifest](diagrams/evidence/qlms-owner-report-assets-20261014.json), [hosted evidence](diagrams/evidence/qlms-owner-report-hosted-20261014.json).

No database migration or data import occurred. Retain Worker `cf2c15f9-90c0-4a53-a6dc-3cc7eefbaadd` and pilot API commit `97686708c2f6e4facf574054850847b50bd0dbbd` as the preceding compatible pair. The previous frontend can be reactivated without reverting customer data; the new API preserves its existing contracts. The original practice API and main remain unchanged. No real customer test writes.

Actual Android download, locating and opening each file remains unobserved. Simulated phone widths and desktop download proof are not a substitute. Expenses/closing, isolated hosted demo and memberships remain separate unfinished increments. First automatic scheduled backup invocation remains unobserved; actual manual cloud backup qualification and enabled schedule are recorded in `pilot-cloud-backup-qualified.md`.

## Private Owner acceptance

Sign in privately at the final site after release. Dashboard attention links should open their filtered tickets. Reports -> Shop catalogue should download the 22 services and 30 clothing types, and Employees should remain on daily work. On Android download both Excel and CSV, locate them in Files -> Downloads and open them in a spreadsheet app. Keep credentials and real customer exports outside chat. No practice transactions should be entered into the live pilot for this check.
