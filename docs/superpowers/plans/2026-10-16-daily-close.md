# Owner daily close implementation plan

> Single active agent; use Superpowers executing-plans, TDD and verification. The human's autonomous-work instruction replaces repeated approval stops. No delegation, new dependency, real fixture write or unrelated draft staging.

**Goal:** Preserve Owner-signed cash and M-Pesa daily checks, explain differences and expose later changes without rewriting a signed snapshot.

**Architecture:** Existing restricted FastAPI/SQLAlchemy/PG boundary, shared report calculations and authenticated Next.js forms. Till movements follow the expense revision/history pattern; close confirmations are immutable versions. Backend computes all monetary figures.

**Tech stack:** Existing Python/SQLAlchemy/FastAPI, PostgreSQL, React/Next static export, pinned XLSX writer. No additions.

**Spec:** `docs/superpowers/specs/2026-10-16-daily-close-design.md` (read before implementation).

## Constraints and review focus

- One date in Africa/Nairobi; no invented opening cash, cash allocation, profit or automatic M-Pesa verification. Personal costs never reduce till cash; unconfirmed cash funding blocks sign-off.
- Keep exact pending bodies/account/API destinations and replay before stale validation. Keep every original financial event.
- Read a consistent source snapshot; concurrent activity after sign-off must appear as Needs review on subsequent reads, including equal-net events and paid-date moves.
- Owner-only sign-off/movements/exports. Backward-compatible additive migration, recovery and compatible rollback before live release.
- Inspect nonfinite/boolean/cents/oversized values; old-order receipts and crossed midnight; mixed methods/refunds; two concurrent sign-offs and lost replies; restored immutable history. Add tests in the owning step rather than relying on a checklist alone.

## Task 1 — transaction-consistent shared daily activity

Progress 16 October: released source d0935e802b4bc76fc7035ef193e7ebdd014ed868 / schema 027. Exact CI 38940888554 passed 378 backend/123 frontend checks, repeated/empty migration, new-table-only permission-preservation and encrypted 27-table restore (3.1s). Owner phone-width fictional signing/retry/review/history and Employee denial passed; actual export bytes passed, while Android locate/open and financial-save acceptance remain human checks. Pre/post cloud backups 38916905290/38942039201 passed. Worker e04fa600 / API dep-db963oss728c73ft824g; actual public smoke passed 147 assets/21 pages/seven denials. The initial broad grant script was rejected and not applied; the narrow accepted replacement preserved old access. Local narrow rehearsal lost its disposable connection; passing CI proof is separate. See docs/daily-close-check.md for exact evidence and rollback limits.

Files: create `backend/daily_control.py`, `backend/tests/test_daily_control.py`; extend existing model/payment calculation only if needed to avoid duplicating corrected-receipt logic; keep existing Finance/Reports callers consistent.

- [x] Write the hand-calculated fixture and date/method/correction/unknown-payer/no-activity tests first; run and observe the missing implementation fail.
- [x] Implement `daily_activity(db, business_date)` returning source components, actionable unknown cash entries and a stable financial fingerprint. Reuse existing report calculations/definitions; exclude unrelated PII and generated timestamps.
- [x] Establish transaction-consistent reads using the existing restricted session/connection; test interleaved financial writes and detect review after the transaction. Test parity with existing report money totals.
- [x] Run focused tests and existing financial/report regressions; review all touched callers. Commit only a tested coherent increment, not an unverified release.

## Task 2 — till movements and immutable closing versions

Files: `backend/models.py`, new `backend/daily_close_routes.py`, `backend/migrations/027_add_daily_close.sql`, `backend/transaction_safety.py`, `backend/main.py`, `backend/ops/schema_setup.py`, `backend/ops/rehearse_recovery.py`, new HTTP/PostgreSQL tests. Generated `backend/schema/` follows actual rehearsal.

- [x] Write failing HTTP permission/validation/replay/revision/variance-reason and original-history tests. Write actual PostgreSQL simultaneous saves and close-signature/review races.
- [x] Add TillMovement/Change and immutable DailyClose versions; extend existing save-result dispatch for these records without changing old fingerprint rules. Expose only the spec's Owner routes.
- [x] Require manual counts/statement values, matching preview fingerprint/latest version and known cash funding. Calculate expected/variance on the backend. Resign appends history; later source changes flag review.
- [x] Add additive tables/RLS/grants; runtime cannot delete movements or update/delete history/closing snapshots. Backup read only; browser roles denied. Rehearse repeated migration and old-record preservation.
- [x] Full PostgreSQL suite and encrypted restore must include an original close, a changed source and a later confirmation. Verify restored signatures/history and permissions, then commit tested code.

## Task 3 — reports and phone flow

Files: existing `backend/owner_reports.py` and report routes; new `frontend/src/lib/daily-close-tools.js`, tests, protected `/daily-close` and `/till-movements` pages; existing Finance/dashboard links, `report-tools.js`, `page-help.js`, app shell titles; reuse OwnerGuard/usePendingSave and error handling.

- [x] Write failing payload, exact-cents variance wording, filtering/source invalidation and pending-body tests.
- [x] Implement the simple date → activity → counts → explanation → Owner confirmation flow; clear saved-versus-current history and Needs review. Link direct corrections; keep new staff operational navigation unchanged.
- [x] Extend existing report allowlist/filters/JSON/XLSX/CSV, with original signed figures and current review state. Reject oversized exports, preserve formula/link safety and numeric/text typing.
- [x] Phone-sized fictional walkthrough: 900 expected/850 counted, no-reason rejection, personally paid cost, ambiguous cash cost, lost reply, source change, reconfirmation, Employee denial and exact file download checks. Capture meaningful numbered evidence; actual Android hardware/file-open remains a separate human check.
- [x] Full frontend tests/lint/Linux static build and offline strict upload check, focused UI/UX review and manual code review. Update learning/presentation/evidence notes with skill effects.

## Task 4 — exact release, recovery and handoff

- [x] Stage explicit feature paths only, diff/secret scan; publish approved branch and require exact candidate CI. Preserve demo stash, unrelated save-rejection edit and Owner OAuth drafts.
- [x] Actual pre-migration cloud backup; pilot-only rehearsed migration and restricted grants; verify metadata/counts and old API readiness before replacing the API.
- [x] Deploy exact reviewed API; export/hash reviewed public frontend image, upload/qualify/activate paired Cloudflare version without reading private token files. Verify provider source and 100% traffic.
- [x] Run existing full live smoke with this release's manifest, actual post-migration cloud backup and hosted verification job. Record source/API/schema/Worker pair, safe rollback and any limits. No artificial production costs/payments.
- [x] Update current handoff and learning notes; only then proceed to another feature. Collect optional private Owner Android acceptance without requesting credentials.
