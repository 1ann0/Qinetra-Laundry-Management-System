# Start Qinetra with real business data

Status: 11 September 2026. Database preparation complete; the live application has NOT been switched. The user prioritised getting Qinetra operational and conserving remaining usage.

## Completed

- Supabase project: `Qinetra-Laundry-Management-System` (`owetwiekmoycshdijmtl`).
- Created the private `qinetra_live` schema through remote migration `create_private_qinetra_live_baseline`, using the current backend models, including transaction-safety fields.
- Nine empty tables: users, customers, services, clothing_item_types, orders, order_service_lines, order_items, payments and ticket_counters. All foreign keys stay within the new schema.
- Verified: nine tables, nine with RLS enabled, zero rows, zero cross-schema foreign keys, and no schema/table access for anon or authenticated. PUBLIC and service_role grants were also revoked from the new schema, tables and sequences. No browser-facing RLS policies were added: the frontend uses FastAPI, not the Supabase Data API.
- Preserved existing public data: 11 customers, 17 orders and 10 payments. No customers, orders, credentials or catalogue data were copied. No new paid project, application deployment or credential change was made.
- The baseline is recorded in Supabase migration history. The compilation helper is local-only at `tmp/prepare-qinetra-live.py`; it reads model metadata without connecting to the shop database.

## Critical finding before real use

The existing public tables have RLS disabled. Direct privilege checks confirmed anon SELECT and INSERT rights on users, customers, orders and payments. The security advisor reports eight exposed public tables. This includes the users table containing password hashes; no credential values were fetched in this review. There is no evidence here establishing whether anyone accessed the data.

Existing-table permissions have not been changed. First verify the database role used by the deployed FastAPI backend. Then restrict public Data API access and enable appropriate RLS without breaking backend login or saves. Verify with the actual backend account and an unauthorised request. Do not copy this exposure into the new schema or add permissive browser policies to make an error disappear.

References: [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api), [RLS-disabled advisory](https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public). The nine new-schema no-policy notices are intentional while no application role has been provisioned; the new database is not yet usable by staff.

## Remaining work, in order

1. **Secure access.** Fix the confirmed public-table exposure after verifying the backend role. Provision appropriately restricted backend access to the new schema. Keep database credentials out of frontend code and screenshots.
2. **Finish the approved clothing/receipt change.** Enable representative tally and detailed garment settings for testing, and include saved counts, descriptions, damage and stain notes in both customer receipt drafts. Phase 3A1 was approved but is not implemented. Do not claim laundry condition exceptions or outsourced tracking already exist.
3. **Configure real operations.** Confirm Qinetra's current prices and clothing list; enable Quick tally for ordinary wash services and Individual garment details for dry cleaning. Create the real owner/staff accounts securely. Do not reuse fixture credentials or import sample customers/payments. Agree how to enter any real outstanding orders without double-counting money.
4. **Connect and verify the app.** Current backend queries use unqualified table names; creating qinetra_live alone does not route them there. Add explicit schema routing without fallback to public, check raw SQL as well as ORM queries, and validate with the deployed database role. Coordinate backend/frontend versions with the transaction-safety contract. A new owner must be able to log in, register a customer, save a mixed order, read its clothing receipt, record payment and find the same record after refresh. Confirm public data is unchanged.
5. **Prepare recovery and start a controlled pilot.** Verify a backup and restore process, set up the requested UptimeRobot alerts, keep a brief paper fallback and reconcile orders/payments at day end. Start with one trained staff member and review discrepancies daily. No deployment or full manual acceptance is recorded yet.

Keep subscriptions, Google OAuth, microservices and AWS migration out of this launch step. Description-only outsourced identification is the current business practice; permanent references and sent/returned reconciliation remain planned improvements. The new schema separates test and business records within one database; it is not a separate backup, a separate project or multi-business isolation.

## Resume without redoing work

### Confirmed future account model

- Preserve Caroline's existing account and its employee accounts for a separate demonstration environment. Review/sanitise customer names, contacts, payments and other personal data before showing that environment to prospects; do not assume every existing record is fictitious.
- Add platform-admin business onboarding: create the business, provision its data boundary and invite its owner. Google OAuth later provides identity only. A verified business membership determines access; signing in with Google must never automatically grant ownership.
- Owners invite employees and assign explicit permissions, such as order intake, clothing checks, status updates, payment recording and report viewing/export. Enforce them in FastAPI as well as hiding inaccessible navigation/actions. Staff must not grant themselves permissions or access another business by changing a URL or business identifier.
- Future multi-business design: businesses plus user memberships and permissions. Prefer shared business-scoped tables with enforced isolation when commercial onboarding is implemented, unless a physical database per business is justified. qinetra_live is currently a single-business schema, not an implemented tenant boundary for multiple businesses.
- Keep demo and real-business credentials/configuration separate now. Test cross-business access, invitations, revoked membership, exports and restricted employee actions before onboarding a second business. Configure Google OAuth together with the student as agreed.

- Read this file, then `docs/clothing-intake-review.md` for the approved 3A1 scope.
- Existing checks: 92 backend tests passed previously, including PostgreSQL concurrency; the recent clothing audit reran 25 existing tests successfully. Student order recovery passed. Student final-payment recovery was skipped and stale clothing-edit acceptance remains open.
- Do not recreate the schema, clear public data, seed demo accounts into qinetra_live or switch the live connection without completing the configuration and release checks above.
