# Owner daily closing

## Purpose and authorized scope

The Owner needs to see whether the shop's counted cash and M-Pesa statement collections/returns match the recorded activity, explain differences and sign off without changing financial history. One shop, fewer than 20 orders/week, phone first, free hosting, no new dependency or hardware. The Owner confirms some expenses are paid personally; funding source was separately deployed and verified as 754e778/schema 026 before this work starts.

This is a new financial-record subsystem using the existing expense, report, permission and save-reference patterns, not a redesign of accounting. The human's current instruction is to decide implementation details and ask only for unavailable shop facts; this supersedes the skills' repeated design-approval pauses. Execution stays single-agent. The shop-fact question about personal funding is answered; no additional fact is required to choose manual opening cash and statement entry.

## Chosen approach and alternatives

Use an immutable signed daily snapshot with append-only later confirmations, plus attributed till-movement corrections. Recomputing a signed close in place would destroy evidence; a full double-entry accounting package is unnecessary. Reuse existing report calculations and request references, not a second financial totals engine or an offline queue.

## Money and dates

- Select one inclusive Nairobi business date, today or earlier. Existing received/effective/expense paid dates remain authoritative, independent of server UTC timestamps. Do not fabricate historical opening balances or infer opening cash from yesterday's count.
- Owner explicitly enters opening cash and physically counted closing cash. Expected cash = opening cash + corrected cash receipts - cash refunds - recorded shop-funded cash expenses + till additions - Owner withdrawals. Personally funded costs remain business expenses but never reduce expected shop cash.
- Unconfirmed, non-reversed **cash** expense funding prevents signing and supplies direct links for confirmation; do not guess. M-Pesa cost funding is shown but does not change a collection/return comparison.
- Owner enters statement money collected and statement money returned separately. Compare those with recorded corrected M-Pesa receipts and M-Pesa refunds. This is not a comparison to the M-Pesa account balance, an automatic transaction verification or a profit calculation. M-Pesa expense payments are outside these collection/return totals.
- Entry-error corrections restate the original receipt date; actual refunds remain on the effective return date, matching existing Finance and Reports. No service allocation of whole-order payments/refunds.
- Amounts use exact Decimal KES cents on the backend, reject booleans/nonfinite/excess precision/negative counts and cap inputs consistently with the expense ledger. Display signed differences plainly: expected 900, counted 850 => **KES 50 short**. Overages and matches are explicit; require an explanation for any variance or a later confirmation.

## Records, consistency and safe retry

- Add `TillMovement` current state and immutable `TillMovementChange` events, following Expense/ExpenseChange. Types: cash addition and Owner withdrawal. Actual date, positive amount, reference/note, actor, revision and request reference; corrections/reversal retain originals. No DELETE. A wage paid as an expense must not also be recorded as a withdrawal.
- Add append-only `DailyClose` rows, unique business date/revision and request reference. Store entered counts, opening cash, statement totals, backend-calculated snapshot, source fingerprint, reason, reviewer identity/time and revision. First expected revision is zero; later sign-off appends the next version, never edits the original snapshot.
- Preview and save use a transaction-consistent financial snapshot. On PostgreSQL, establish repeatable-read before the ledger queries (after capturing/releasing the read-only authentication transaction), using the existing restricted connection/session configuration. Restore normal connection isolation on return. SQLite fixtures retain their supported transaction behavior. Recheck current Owner authority within the signing transaction.
- Save locks the request reference and the business date, checks replay **before** stale-input validation, compares expected closing revision and preview fingerprint, then inserts once. Concurrent different confirmations cannot produce the same revision. Serialization/conflict errors are explicit known-not-saved responses; lost responses retain the original request for retry. A retry returns the same signed version, even after later activity.
- The fingerprint excludes generation time, customer contact details and unrelated order metadata. It includes stable financial identifiers/dates/methods/amounts/entry corrections, expense revisions/funding/reversal and till revisions, so equal-net corrections still require review. Changes committed after the snapshot flag review on the next read; no claim that sign-off freezes the shop or blocks later payments.
- Every close view/report compares its saved source fingerprint with current activity. New/backdated payments, refunds, corrected expenses (including a date move or reversal) and till corrections can flag affected days. Original stored figures remain visible. Reconfirmation requires reviewing fresh figures and explaining the change.

## API, reports and phone flow

- Owner-only `GET /daily-close?date=YYYY-MM-DD` returns current components/fingerprint, unconfirmed cash expenses, till movements, latest signed snapshot/review state and signed history. `POST /daily-close` accepts date, manual counts/statement totals, expected fingerprint/revision and reason under the existing idempotency header.
- Owner-only create/read/correction endpoints under `/till-movements`, using existing replay/revision/correction conventions. Employee navigation and direct API access stay denied; no new role.
- Extend existing `/dashboard/reports/` allowlist with daily closing and till movements, applicable date filters, shared JSON/XLSX/CSV generation, formula protection, explicit limits, text references and numeric amounts. Preserve `/dashboard/export` and existing reports. Closing report identifies original signed figures versus current Needs review; it does not add snapshots across days as if they were income.
- Reach Close day from Finance and the Owner dashboard; retain existing navigation/workflows. One phone page: choose date, review system activity (links to existing records), count money, explain differences, confirm. Till additions/withdrawals have a small linked form and history. Historical sign-offs are disclosed below, not mixed into the primary task.
- Use existing OwnerGuard, authenticated fetch, pending-save notice, date/money formatting, retry-safe form locking, read error/loading/server-waking feedback, tour, 44px+ targets and nearby required labels. Source/filter edits invalidate the preview; pending saves lock date and exact body until resolved. No new global state, UI library or animation dependency.

## Acceptance and pre-mortem

1. Hand calculation: opening 200 + cash receipts 1000 - cash refund 100 - shop cash costs 150 + addition 50 - withdrawal 100 = expected **900**. Owner personally pays a further 300: expected remains 900, business costs include it. Counted 850 => **50 short**, requires reason. Corrected M-Pesa receipts 700 and returns 50 compare to independently entered statement totals.
2. Existing unknown cash cost blocks signing; attributed confirmation clears that blocker without changing its original history. Reversal/date changes and next-day entry corrections flag the proper saved day. A net-zero pair of later events also flags review.
3. Lost create/correction/closing reply and PostgreSQL races leave one stored result/reference. Same reference with changed details conflicts. Two Owners signing the same revision produce one next version and one stale rejection; replay after a later confirmation returns the original immutable version.
4. Nairobi midnight boundaries, receipts on old orders, cancelled orders with real money, partial/mixed-service payments, Cash/M-Pesa refund method, negative/nonfinite/oversized input, no-activity day and permission denial are tested. Existing financial reports remain equal to the shared components.
5. Repeat compatible migration, old API compatibility, unchanged old records, runtime immutable history/nondeletion, backup SELECT, browser denial and encrypted isolated restore of new tables/versions all pass. No fictional live ledger writes.
6. Phone preview/variance/history/pending retry and actual spreadsheet files must agree. Exact candidate CI, actual pre/post cloud backups, exact paired deployment, public smoke and rollback rehearsal precede the next feature. Human Android hardware acceptance remains distinct.

## Release and limits

Migration 027 adds tables only, RLS and restricted grants; existing expense/payment records stay unchanged. Backup whole-schema export must be qualified with them. Rollback restores the previous compatible app while retaining all new rows/tables and any pending-request compatibility. No schema downgrade, delete/rewrite, automatic payroll, reimbursements, accounting certification, customer messages or freeze of future financial activity.

Independent backup timing remains a separate unresolved reliability item: actual scheduled execution/read-back/deduplication and DOWN/UP delivery are proved, but completion was 2h54 late. Keep monitoring; do not hide it behind this feature or repeat credential setup. Demo/photos/delivery/manager/tracking/cookies and earlier approved features stay queued.
