# Expense funding before daily close

The Owner confirms that some business expenses are paid personally. This is one deployable financial increment before daily closing, not a closing ledger or reimbursement system.

## Scope and rules

- Add nullable `expenses.funding_source`: `shop` or `owner`; absence means not confirmed. Migration 026 adds one checked column, with no default, backfill, history rewrite, new grants or table. Reapplying is safe. Rollback restores the previous frontend while retaining the funding-compatible API and added column, so pending new bodies still work. Do not downgrade the API to a version that forbids the new field while those bodies may be pending; keep its compatibility handling in any backend fix.
- New Owner entries require a deliberate Paid from choice: Shop money or Owner's own money. Cash/M-Pesa remains the independent payment method. Existing unknown entries stay clearly unconfirmed; corrections may retain unknown when the Owner cannot honestly identify the payer. A known source cannot be cleared through the UI.
- Reuse attributed, revision-checked, idempotent expense correction. Preserve original details and all earlier events. An older correction missing funding must preserve a later confirmed source.
- Preserve exact pre-upgrade request fingerprints when funding is missing. Use the installed Pydantic conditional field omission rather than changing the shared save fingerprint helper. Prove this with literal old create/correction hashes captured before implementation, plus lost-response replay tests. Old pending frontend bodies must still display and retry unchanged.
- Extend existing expense JSON/report/XLSX/CSV rows with Paid from, add source subtotals and keep total business costs unchanged. Unknown sources remain a separate subtotal. Do not subtract personally paid costs from shop cash or invent a till deposit. Daily-close calculations/withdrawals/reimbursement remain the next increment.
- Apply UI/UX Pro Max to the existing form/history/help: clear nearby labels, required choice, 48px controls, visible unknown state and pending-save explanation; no new workflow or dependency.

## Verification and release

1. Tests first: source choices/invalid values/Owner-only permission; original history and old request replay; old correction preserves known funding; PostgreSQL concurrent source corrections/replay; repeated migration preserves old rows/history; frontend choice and legacy pending display; report subtotals/export contents.
2. Full disposable PostgreSQL tests, migration/reapplication and encrypted separate-database restore. Prove the field survives recovery; keep runtime history immutable and browser roles denied.
3. Fictional phone-sized create/correct/unknown/history and spreadsheet review, full frontend tests/lint/build, exact candidate CI and secret scan.
4. Actual pre-migration cloud backup; apply only 026 to the verified pilot schema; verify metadata/grants/count preservation and old API readiness, then deploy exact API candidate. Upload/activate paired frontend and run shared live asset/route/readiness/anonymous-denial smoke. No fictional live costs.
5. Handoff includes actual frontend/API/schema versions, safe rollback, screenshots, skill effects, limits and deep-review backlog. Release this increment before daily-close implementation.

## Other work

Phone sign-in is already deployed and live-verified (875eeb1). Backup catch-up implementation/cloud qualification is deployed; natural-trigger timing remains an external observation, explicitly open while this next prerequisite proceeds. Do not claim that an unobserved schedule ran. Keep the independent missed-run monitor armed. Demo/OAuth drafts and the unrelated save-rejection edit remain parked/preserved.

## Skills

Superpowers bounded design/TDD/verification protects money, historical truth and lost-response compatibility. Ponytail reuses the existing expense/report/correction paths and installed serializer. UI/UX Pro Max informs phone labels/help/targets. Supabase guidance applies to the additive checked column, unchanged restricted roles and rehearse-before-live release.
