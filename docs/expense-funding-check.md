# Expense funding before daily closing

Prepared 16 October 2026; not yet deployed. The Owner confirms that some shop costs are paid personally. Cash/M-Pesa describes how a cost was paid; Paid from identifies whose money was used. Both sources remain business costs. Daily closing and reimbursement are separate future controls.

## Implementation and compatibility

Additive migration 026 adds nullable checked `expenses.funding_source` (`shop` or `owner`), with no default, backfill, history rewrite or grant changes. Existing entries remain Not confirmed. The new form requires a deliberate choice for new expenses. The Owner may confirm an old source through the existing attributed correction; unknown may remain unknown rather than guessed.

The existing request reference, correction revision, original details, immutable events and Owner permission checks remain. Missing funding is omitted from serialization so literal pre-upgrade create/correction fingerprints stay unchanged. An older correction that omits the field preserves a source already confirmed by a newer screen. Report JSON, CSV and Excel share the existing backend calculations and add the funding column and three source subtotals; total business costs are unchanged. No service-level profit or till reconciliation is inferred.

## Developer evidence

- Test-first checks reproduced absent functionality before implementation. Full disposable PostgreSQL suite: **349 passed**, zero skipped; concurrent create/correction and replay, stale conflict, Employee denial, invalid values, literal old fingerprints, old correction after later classification, report/refund/reversal semantics, repeat migration and empty-schema restore passed.
- Restricted runtime/backup/browser permissions and encrypted separate-database recovery passed for **24 fictional tables and sequence values in 21.9 seconds**. Corrected funding survives restore while original details stay unchanged. Fixture archive sizes are not live storage forecasts.
- **113 frontend checks**, lint, Linux production static build and strict offline Wrangler upload check passed. Production image `sha256:a8fb12c9ba53188e5656fc5805bc98675046ed1b7a37a4ca383ccfabebe888fb` uses the actual HTTPS pilot API, not the loopback fixture.
- Actual local browser at 375px: required payer rejection saved nothing; old interface committed KES 60 with a lost reply, upgraded interface restored its unchanged pending body and retried to expense #1 with one original event. New interface committed KES 250.50 M-Pesa/Owner with a lost reply; previous interface restored and retried that exact body, yielding expense #2 once. Restoring the upgraded interface showed Owner funding retained. A third KES 50 shop-cash purchase yielded three expenses/three events.
- Hand-calculated report before classification: business costs **KES 360.50**, Cash **110**, M-Pesa **250.50**, shop funded **50**, Owner funded **250.50**, unconfirmed **60**. Both actual browser-downloaded CSV and XLSX contain the funding labels and selected fictional records; workbook ZIP integrity passed. The Playwright download observer stalled; subsequent ordinary browser controls downloaded the files, which were checked independently. No actual Android download is claimed for this change.
- Attributed correction of expense #1 confirms Owner funding while original Paid from stays Not confirmed. Phone inputs/selects measured 48px, submit controls 46px; no horizontal page overflow (375px viewport, 360px document content). Screenshots **79/80** show retained funding and original/correction history. Earlier Employee browser denial and current API permission tests remain applicable; no role rules changed.

## Release gates still open

Exact candidate CI and staged secret scan; actual pre-migration cloud backup; pilot-only 026 migration with metadata/count/grant checks and previous API readiness; exact Render deployment; approved static asset manifest and Cloudflare upload/activation; paired public live smoke; post-migration cloud backup. Do not claim the feature live until these are recorded. Never add fictional expenses to the live ledger.

## Rollback and limits

Restore previous frontend Worker **176a1032-8573-4288-8a57-bd122c478a35** while retaining the funding-compatible API and migration 026. Do not drop the column or restore API e6d9d2b while new bodies may be pending: its strict input rejects the added field. Keep compatibility handling in any backend hotfix. The actual fictional frontend rollback replay passed. The previous frontend cannot show funding and renders additional report subtotals without labels; use the current verified exports and correct forward rather than treating that older display as a reconciliation.

Actual Android expense save/correction acceptance remains separate; the human previously confirmed only that both existing expense screens open clearly. No expenses are automatically classified, no reimbursement is created and no daily closing is implemented here. Backup execution/deduplication/email alerts are verified but the 22:00 operating-window target remains missed; see the dated scheduled-backup evidence.

Skills: Superpowers bounded design, TDD, systematic debugging and verification protect monetary history, replay compatibility and release claims. Ponytail reuses the existing expense/report/save paths and installed serializer, with no dependencies. UI/UX Pro Max informs nearby required labels, plain payer wording, visible legacy state and phone controls. Supabase guidance supports a rehearsed additive checked column and unchanged restricted roles; the project's existing numbered migration chain is retained rather than introducing a parallel CLI migration system. Render/Cloudflare skills govern existing-service deployment and exact provider verification.
