# Start Qinetra with real business data

Status: 15 September 2026. Fresh database prepared and legacy Data API exposure fixed. The student confirmed owner login and an existing receipt work on 11 September. The live application has NOT been switched to the fresh schema. The user prioritises getting Qinetra operational with small, maintainable changes.

Delivery order and acceptance gates now live in [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md). This file tracks setup/release status. Targeted 15 September checks confirmed the old Render backend version and zero users, customers, orders and payments in the nine-table fresh schema; no new full security audit or test run was performed.

## Completed

- Supabase project: `Qinetra-Laundry-Management-System` (`owetwiekmoycshdijmtl`).
- Created the private `qinetra_live` schema through remote migration `create_private_qinetra_live_baseline`, using the current backend models, including transaction-safety fields.
- Nine empty tables: users, customers, services, clothing_item_types, orders, order_service_lines, order_items, payments and ticket_counters. All foreign keys stay within the new schema.
- Verified: nine tables, nine with RLS enabled, zero rows, zero cross-schema foreign keys, and no schema/table access for anon or authenticated. PUBLIC and service_role grants were also revoked from the new schema, tables and sequences. No browser-facing RLS policies were added: the frontend uses FastAPI, not the Supabase Data API.
- Preserved existing public data: 11 customers, 17 orders and 10 payments. No customers, orders, credentials or catalogue data were copied. No new paid project, application deployment or credential change was made.
- The baseline is recorded in Supabase migration history. The compilation helper is local-only at `tmp/prepare-qinetra-live.py`; it reads model metadata without connecting to the shop database.

## Legacy database access: fixed and confirmed

Before the fix, the eight public application tables had RLS disabled and anonymous read/write privileges. This included the users table containing password hashes; no credential values were fetched. There is no evidence here establishing whether anyone accessed the data.

Applied remote migration `20260911122502_restrict_legacy_qlms_data_api_access`. Enabled RLS on the eight public QLMS tables and revoked PUBLIC/anon/authenticated table and related sequence access. Restricted postgres-created future public table/sequence defaults. Preserved postgres and trusted service_role access. No application code, credentials, records or deployment changed.

Verification: all eight tables have RLS and no anon/authenticated read/write grants. All eight zero-row HTTP requests with the public API key returned 401 / PostgreSQL permission-denied code 42501. The security advisor now has no ERROR or WARN findings; 17 no-policy INFO findings are intentional for backend-only access. Counts remain 3 users, 11 customers, 17 orders and 10 payments.

The confirmed Render workspace is My Workspace (`tea-d9bkeej7uimc73amhpn0`), service qlms-backend (`srv-d9bkpgfavr4c73aukk20`), URL https://qlms-backend-7fum.onrender.com. Render reports deployed commit `5da24e5`. A nonexistent-user login probe before and after the change returned the expected 401, exercising the deployed user lookup without reading a password hash. A new postgres/Supavisor connection appeared after the probe; postgres owns the tables and bypasses RLS. An unauthenticated order request remained blocked. The student subsequently confirmed that owner login, Track orders and an existing receipt work.

References: [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api), [no-policy advisory](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy). No broad browser policies are needed for this FastAPI access model. The fresh schema is still empty and not yet usable by staff. A restricted runtime database role remains work for the fresh-schema connection phase.

## Remaining setup and release checklist

Before cutover, complete the roadmap's pilot prerequisites: finish the student browser check for 3A1 receipts, then separately review 3A2 pre-wash checks/history, 3B outsourcing accountability, 3C customer intake, 4 controlled corrections and 5 owner oversight. The checklist below is not permission to skip these workflows.

1. **Access fix complete.** Automated permission checks passed, and the student replied "works" after the owner login/Track orders/receipt check. Provision appropriately restricted backend access when connecting the new schema; keep credentials out of frontend code and screenshots.
2. **Accept the clothing/receipt change.** The local test catalogue now exposes tally and detailed garment entry. Both WhatsApp drafts use one formatter for saved counts, descriptions, damage/stain notes and pending checks. All 37 frontend tests, lint and production build passed on 15 September. The student mixed-order browser check remains; do not claim laundry condition exceptions or outsourced tracking already exist.
3. **Configure real operations.** Confirm Qinetra's current prices and clothing list; enable Quick tally for ordinary wash services and Individual garment details for dry cleaning. Create the real owner/staff accounts securely. Do not reuse fixture credentials or import sample customers/payments. Agree how to enter any real outstanding orders without double-counting money.
4. **Connect and verify the app.** Current backend queries use unqualified table names; creating qinetra_live alone does not route them there. Add explicit schema routing without fallback to public, check raw SQL as well as ORM queries, and validate with the deployed database role. Coordinate backend/frontend versions with the transaction-safety contract. A new owner must be able to log in, register a customer, save a mixed order, read its clothing receipt, record payment and find the same record after refresh. Confirm public data is unchanged.
5. **Prepare recovery and start a controlled pilot.** Verify a backup and restore process, set up the requested UptimeRobot alerts, keep a brief paper fallback and reconcile orders/payments at day end. Start with one trained staff member and review discrepancies daily. No deployment or full manual acceptance is recorded yet.

Keep subscriptions, Google OAuth, microservices and AWS migration out of this launch step. Description-only outsourced identification is the current practice; the user accepted simple physical references on 15 September, subject to agreeing the method with the cleaner. Sent/returned reconciliation remains unbuilt. The new schema separates test and business records within one database; it is not a separate backup, a separate project or multi-business isolation.

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
