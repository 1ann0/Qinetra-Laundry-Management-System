# QLMS: Qinetra pilot and commercial roadmap

Prepared on 9 September; execution plan updated on 15 September 2026 after the business, architecture and dashboard review.
This is the working plan for future phases. It does not authorize deployment, purchases or all future features at once.

**Phase 3A1 accepted locally.** The shared saved-data formatter, receipt tests and representative disposable catalogue are implemented. On 15 September, all 37 frontend tests, lint and the production build passed. The student created a fictional mixed order and confirmed both WhatsApp drafts match the saved clothing record. [QINETRA_PILOT_START.md](QINETRA_PILOT_START.md) records database/release status. The application has not been switched to the fresh schema or deployed.

## Confirmed operating decisions and boundaries

- Qinetra handles about 10 orders daily, occasionally 20 on a peak day. Wrong or missing garment records are the primary problem.
- Staff can use a shared shop screen. Each staff member still needs an individual account for attributable actions.
- Clothing checks usually happen before washing, after drop-off. Receipts must show when the clothing check is pending; never imply the customer witnessed a later check.
- Physical separation practices vary. Agree how ticket references follow bags/baskets and how identity survives shared processing. The user accepts simple physical references for outsourced garments, alongside descriptions; agree the actual labelling method with the cleaner.
- Confirm available care options with the team. Do not offer fragrance/softener choices or make skin-related promises before the process supports them.
- Retain Next.js, FastAPI, PostgreSQL and the current daily navigation. Split large modules only while making a relevant change. No rewrite, new state library or microservices programme.
- Treat each milestone below as a reviewed increment, not permission for a combined release. Phase 3A1 already has approval. Later phases require their own bounded implementation review.

## Next change: Phase 3A1 implementation contract

**Outcome:** The customer's receipt draft contains the same saved clothing record as the order screen. Local implementation, automated checks and student browser acceptance passed on 15 September.

- Update the disposable local catalogue to expose Quick tally and Individual garment details. Preserve existing test orders; do not invent historical clothing records.
- Add a small pure formatter in `frontend/src/lib/order-receipt.js`, used by the new-order and saved-order pages. Keep phone handling and opening the draft in the UI; no automatic sending.
- Build the text from the saved response: customer, ticket, order date, services, counted pieces, garment descriptions, damage/stain notes, total, paid, balance, ready time and current status. Keep existing ready-message behaviour.
- Show pending checks explicitly. Missing historical detail means not recorded, not zero pieces or confirmed absence of damage. Keep the fallback for older single-service orders.
- Add focused formatter tests for mixed services, saved conditions, pending checks, old orders and ready status. Run the frontend suite, lint and production build.
- Browser check: create one fictional mixed order, save, refresh and compare both drafts with its saved clothing details. Do not send either draft. Capture one distinct evidence image only after verification.

**Files:** shared formatter/test, both order pages and the ignored local fixture. **API/schema change:** none. **Learning point:** reuse one saved record to keep different receipt views consistent. Phase complete locally; no live cutover.

## The business objective

Make Qinetra's daily work dependable: receive the right laundry, quote correctly, find each order, record money and complete handover.
Give the owner figures they can trust without reconstructing the day from receipts and spreadsheets.

The pilot must prove that staff use QLMS and the owner receives enough value to keep using it.
A larger feature list does not prove demand. Start with one laundry, one location and the existing owner/employee roles.

## What is already built

Source checked: backend models, routes, auth, pricing logic, migrations, frontend pages and the development journal.
15 September checks: Render still reports live backend commit `5da24e5`; `/docs` and `/openapi.json` respond. The live order contract does not yet require the local branch's save-reference header. Database queries confirmed nine fresh-schema tables and zero users, customers, orders and payments there. These are targeted checks, not a new complete security or operational audit.

| Capability | Current evidence and limit |
| --- | --- |
| Customers and search | Registration, duplicate-phone warning, customer history and service history exist. Registration still needs a smoother path during order entry. |
| Orders and clothing | Mixed services, item counts and detailed garment condition notes exist. The test fixture hides clothing recording; WhatsApp receipt drafts omit item detail, tally condition capture and outsourced-garment tracking need work. See the clothing review. |
| Payments | Staff-confirmed payments, deposits and balances exist. This is manual recording, not Safaricom payment verification. |
| Tracking | Four stages, search, due/late/unpaid filters and collection checks exist. |
| Owner controls | Finance, order export, service/clothing lists and staff account controls exist. |
| Navigation and messages | Local commits `094b654` and `01a2fa3` improve daily navigation, stage controls and errors. The student reports the usability review is working; no independent timing data was supplied. |
| Verification | Prior records show 92 backend and 32 frontend tests passing; student order recovery passed, payment-recovery review was skipped and stale clothing-edit review remains open. No tests were rerun for this planning update. |
| Customer memory | No preference profile, care-note history or dedicated order/item care instructions exist. Implement Phase 8A after pilot accountability passes. |
| Platform admin | No separate platform-admin role or dashboard exists. Use hosting tools and monitoring for the pilot; build business administration in Phase 11. |
| Commercial features | No business/tenant, subscription, allowance, promotion-rule or transport-trip models were found. These remain new work. |

The README describes the original academic scope and is older than several implemented features.
Use this roadmap for prioritisation and the [development journal](DEVELOPMENT_JOURNAL.md) for completed work and evidence.

## Order of work

| Phase | Outcome | Priority/status |
| --- | --- | --- |
| 1 | Accept the current navigation and feedback changes | User reports usability review passed; no uncoached timing data recorded |
| 2 | Protect orders and payments from duplicate or conflicting saves | Automated checks and student order recovery passed; remaining manual scenarios open |
| 3A1 | Complete saved clothing receipt drafts | Accepted locally; 37 frontend tests, lint and build pass; student confirmed both drafts match the saved mixed order |
| 3A2 | Complete pre-wash checks, condition exceptions and history | Required pilot workflow; preserve original observations and block processing with incomplete checks/holds |
| 3B | Identify and reconcile outsourced dry-cleaning garments | Required before outsourced pilot work; simple references accepted, physical method to confirm |
| 3C | Complete customer intake without leaving the order | Required pilot workflow; preserve all clothing records |
| 4 | Correct mistakes with an owner-controlled history | Required pilot workflow |
| 5 | Provide actionable owner oversight, reliable figures and filtered exports | Required pilot acceptance; use supporting records, not invented metrics |
| 6 | Prepare clean production data, recovery and monitoring | Required before real-data cutover |
| 7 | Run and measure the Qinetra pilot | Prove value before wider rollout |
| 8A | Remember customer preferences and surface order instructions | First planned premium-service increment after the core pilot passes |
| 8B | Add offers and reusable customer messages | After costs and eligibility rules are agreed |
| 9 | Add Safaricom payment prompts and reconciliation | After merchant access is ready |
| 10 | Test profitable laundry memberships and trip allowances | After costs and rules are agreed |
| 11 | Isolate multiple businesses and add platform administration | Mandatory before a second business joins |
| 12 | Add QLMS software subscriptions, trials and controlled Google login | Commercial onboarding |
| 13 | Expand only where usage justifies it | Conditional roadmap |

Phases 8–10 are Qinetra growth options. Select the next one from pilot evidence; they need not all precede phase 11.
Do not onboard a second business before phase 11 passes its isolation tests.

## Phase 1 — Close the current usability phase

**Value:** Staff can find everyday actions and understand what to do when an action fails.

- Use the [existing browser checklist](docs/navigation-usability-check.md) on desktop and a narrow screen.
- Check New order, Track orders, customer search, saved details, Back, refresh and keyboard focus.
- Ask an unfamiliar user to select a stage without Page tour or coaching. Record hesitation and wrong selections.
- Confirm that a load failure shows recovery advice, not an empty-shop result.
- Confirm employee restrictions by direct links as well as hidden navigation.
- Fix only failures found in this review. Preserve screenshot 34; add one stage-filter image only if it proves the improvement.

**Main files:** app shell, tracking page, shared messages and the browser checklist.

**Exit gate:** Staff complete the three daily navigation tasks and stage filtering without coaching. All reported blockers have a verified fix.
Passing automated checks alone does not close this phase.

## Phase 2 — Make saves and ticket numbers dependable

**Value:** A busy counter or lost connection must not create duplicate orders or payments.

**11 September status:** Local implementation and recovery evidence are in [the Phase 2 check record](docs/transaction-safety-check.md). All 92 backend tests passed, including the six PostgreSQL cases. Student order recovery passed; payment-recovery review was skipped and stale clothing-edit review remains open. Nothing has been deployed.

- Replace or protect the count-plus-one ticket calculation. Test two staff creating orders at the same time.
- Add an idempotency key for each order/payment submission: a repeated request returns the original result instead of saving twice.
- Keep the key through a retry of the same attempt. Reject reuse with different details. Issue a new key for a new transaction.
- Preserve the existing payment balance lock. Test concurrent partial payments, not only a full-balance overpayment.
- Test stale status updates and simultaneous edits. Reject conflicting changes with an instruction to check the current record.
- Confirm saved service prices remain unchanged when the owner later changes the service list.
- Test rounding, Nairobi dates, daily ticket boundaries and the sequence after cancelled orders.
- Keep pending/unknown results visible. Do not turn an uncertain save into a false success or definite failure.

**Main files:** `backend/logic.py`, order/payment routes in `backend/main.py`, models, migrations, contract tests and order forms.

**Exit gate:** Duplicate-request, concurrent-save and interrupted-reply tests pass against isolated PostgreSQL.
SQLite checks alone are insufficient to prove database locking. No unexplained duplicate ticket or payment remains.

## Phase 3A and 3B — Clothing records before customer-intake expansion

The student confirmed clothing tallies, garment identification, existing damage and serious stains are essential. Prioritise [the clothing intake review and phased plan](docs/clothing-intake-review.md) before the customer shortcut. The existing tally was hidden by the disposable fixture, not removed from the code. The review identifies real receipt, condition-history and outsourcing gaps; it does not claim the live catalogue was checked.

Start with the 3A1 contract above. In 3A2, require an explicit completed check before washing or outsourcing, record author/time and retain corrections. A nonempty partial tally is not proof that the full check is complete. Provide a customer-reply hold for unresolved issues. In 3B, use stable physical references accepted by the user; confirm the safe labelling method with the cleaner. Track physical pieces separately from billed units (for example, a suit jacket and trousers), partial returns, return checks and authorised handover. References must survive edits. Do not mark Ready while required pieces or final checks remain outstanding.

## Phase 3C — Finish the customer intake workflow

**Value:** An employee can serve a new or returning customer without losing an unfinished order.

- Add a small Add customer action inside order entry. Return the saved customer to the open order automatically.
- Preserve services, clothing details and price choices while adding the customer.
- Protect an unfinished draft when navigating away; existing uncertain-save recovery only protects a submitted request. Make the saved receipt and starting the next order visually distinct.
- Normalise supported Kenyan phone formats for search and duplicate checks.
- Before saving a likely duplicate, show existing customers and a clear choice. Do not silently merge people who share a number.
- Keep the essential fields first: customer, services, quantities, clothing check, ready time and payment choice.
- Make unpaid, deposit and full payment easy to distinguish. State that manual M-PESA entries require confirmation of received money.
- Check that the receipt identifies the customer, laundry, price, paid amount, balance and promised ready time.

**Main files:** new-order and customer pages, customer API/schema, shared clothing entry and receipt views.

**Exit gate:** Staff complete representative new-customer and returning-customer orders without abandoning or re-entering the form.
Test one mixed-service order with a deposit and pending clothing details. The receipt must match the saved record.

## Phase 4 — Handle mistakes without hiding history

**Value:** A wrong customer, amount or status must have a controlled correction path.

- Agree which changes employees may make and which require the owner.
- Add the smallest useful set of owner corrections: customer details, incorrect order details, cancellation and payment correction.
- Record who changed what, when and why. Retain the original value and link each correction to its order or payment.
- Use linked reversals/adjustments for payment mistakes. Distinguish correcting a record from actually returning money to a customer.
- Prevent edits that would leave impossible balances, duplicate reversals or inconsistent collected orders.
- Provide an explicit owner path for an accidental stage change. Do not turn the ordinary forward-stage button into unrestricted editing.
- Keep cancelled tickets in history. Exclude or identify them consistently in active work and reports.

**Main files:** order detail, owner controls, models, migrations, correction routes and contract tests.

**Exit gate:** Correct a wrong quantity, cancel an unpaid test order and reverse an incorrect payment in the test environment.
The history and reports must explain every change. Employees must not gain owner correction rights through the API.

**Decision before building:** Agree the permitted corrections, refund handling and who approves each one.

## Phase 5 — Make the owner's daily review trustworthy

**Value:** The owner can explain the day's work, receipts and unpaid balances.

- Check the existing Finance figures against saved orders and payments before adding more charts.
- Show order value, money received, outstanding balances and cash/M-PESA breakdowns with clear dates.
- Carry phase 4 cancellations and payment adjustments into every relevant total and export.
- Make due work, late work and uncollected laundry easy to find from the owner view.
- Keep Finance as the owner's landing page. Add a compact Needs attention area linking to due/late orders, pending checks, customer holds, missing/late outsourced pieces, failed final checks, uncollected orders and unpaid balances as those supporting workflows are implemented.
- Clearly separate all outstanding debt from remaining balances on orders booked in the selected period. The current Finance and overview scopes differ; preserve correct definitions in labels and exports.
- Show the last successful update, provide refresh and reload when returning to the screen. Failed refreshes must not become zero activity; retain stale data only with a clear warning.
- Add filtered CSV exports for an individual customer, service and date range. Include the filters and column meanings.
- Define “top services”: quantity, number of orders or booked value. Keep the selected measure visible.
- Add a small daily reconciliation record if the owner cannot close the day reliably with the existing views.
- Avoid “profit” labels for receipts minus expenses. A later expense record can support net cash movement; profit needs proper cost definitions.

**Main files:** Finance/Dashboard, customer/service history, financial-summary and export routes, reporting tests.

**Exit gate:** Reconcile a fixed test dataset by hand, including deposits, later payments, discounts and corrections.
Screen totals and exported totals must match for the same definitions and dates. No unexplained difference is acceptable.

## Phase 6 — Prepare real data, recovery and monitoring

**Value:** Qinetra can trust the records and knows what to do when the service is unavailable.

### 6A. Clean production setup

- Keep current demo records intact. An empty protected qinetra_live schema has now been provisioned in the existing project; it has not been connected to the app. A separate production project remains a stronger future environment boundary, subject to account capacity/cost review.
- Rehearse schema creation from versioned migrations in a fresh test database first.
- Seed only owner-approved service/clothing templates. Create real owner/staff accounts through a controlled setup process.
- Do not copy test customers, orders or payments into production.
- Identify genuine outstanding laundry at cutover. If any exists, agree a verified opening-record procedure rather than silently omitting it.
- Keep development, test and production configuration separate. Make the test environment visibly identifiable.
- Review database permissions, exposed Data API objects, secrets, TLS, CORS and role restrictions.
- Keep the browser talking to FastAPI. Do not expose database credentials or give the browser direct table access.

The current application uses custom FastAPI authentication and direct SQLAlchemy database access.
Do not assume that a Supabase `auth.uid()` policy will automatically protect those connections.
Check the actual database role and Data API exposure. Supabase distinguishes table grants from row-level policies. [Security reference](https://supabase.com/docs/guides/api/securing-your-api)

### 6B. Recovery and support

- Define a backup frequency, retention period, acceptable data loss and recovery time with the owner.
- Configure the backup method supported by the selected plan. Rehearse a restore into a separate environment and compare records.
- Treat CSV exports as useful records, not a full database backup. Store backups with restricted access.
- Agree a real support contact, opening-hours response process and incident log.
- Write a short paper fallback for an outage, including temporary receipt references and later reconciliation.
- Preserve the ability to identify what was entered during the outage. Do not promise offline app operation in this phase.
- Verify actual hosting wake-up time and service limits. If they interrupt counter work, present a measured hosting change and cost for approval.

Backup features depend on the selected service plan; verify them before implementation. [Supabase backup reference](https://supabase.com/docs/guides/platform/backups)

### 6C. UptimeRobot and release checks

- Add a small readiness endpoint that checks database access without returning customer data or credentials.
- Monitor both the frontend and API readiness. The existing `/` endpoint only reports that the process is running.
- Set up UptimeRobot notifications to the agreed contact. Confirm that a controlled test alert is received and that recovery is reported.
- Document that periodic checks can miss brief failures and do not prove an order can be saved.
- Use existing hosting dashboards for deployment, errors and technical health during the pilot. A custom platform-admin dashboard is not a launch prerequisite. Retain useful error codes and incident records without exposing customer details in monitoring.
- Rehearse deployment, rollback and configuration checks before switching Qinetra to the new environment.

Verify UptimeRobot's current free-plan terms, check interval and alert options during setup. Use it for basic detection, not an instant-alert guarantee. [Official free-plan guidance](https://help.uptimerobot.com/en/articles/11604710-who-should-use-uptimerobot-s-free-plan)

**Main areas:** migrations, deployment configuration, health route, environment setup, backup/restore and support instructions.

**Exit gate:** Fresh production schema rehearsed; access tests passed; restore proved; alert delivered; rollback documented; opening records agreed.
Obtain approval for the exact cutover before changing live configuration or collecting real data in the new environment.

## Phase 7 — Run the Qinetra pilot and decide what earns its place

**Value:** Replace assumptions with observed shop use.

- Record a small baseline before cutover: intake time, order-search time, daily reconciliation effort and common corrections.
- Plan 10 operating days, including a busy day where possible; extend if there are too few orders to cover the workflow.
- Track intake time/hesitation, garment discrepancies, missed instructions, rewashes, promised-time performance, outstanding outsourced pieces and daily payment differences. Compare with the starting baseline; do not manufacture improvement percentages.
- Train staff on intake, tracking, payment confirmation, handover, corrections and outage handling.
- Deploy the approved release and check the exact deployed version. Use authorised real transactions for production acceptance.
- Review incidents daily during the first week. Fix blockers before adding features.
- Ask the owner which part they would miss if QLMS were removed and what they would pay to retain.

Suggested acceptance targets below are proposals, not measured results. Agree them before the pilot starts.

| Measure | Proposed gate |
| --- | --- |
| Correctness | No missing orders, unexplained balances or duplicate payments in the reviewed records |
| Daily use | All eligible new orders and payments captured, or listed for reconciliation after an outage |
| Independence | Staff complete ordinary intake, search and tracking without coaching |
| Search | Typical customer/order lookup within 30 seconds on the shop's actual device and connection |
| Daily close | Owner reconciles at least five consecutive trading days without rebuilding the figures in another spreadsheet |
| Resilience | Restore and alert drills pass; each incident has an owner and recorded resolution |
| Commercial value | Owner identifies a concrete recurring benefit and discusses willingness to pay; praise alone is not evidence |

**Exit gate:** Owner accepts the workflow and records. Critical defects are closed. Record actual results and a go/fix/stop decision.
If the pilot fails, repair the cause. Do not use more features to hide the failure.

## Phase 8A — Customer memory that reaches the worker

- Keep one optional current preference profile per customer. Start with team-confirmed presentation/care options; defer unconfirmed fragrance and softener choices.
- Surface preferences at customer selection; save the agreed values with the order. A later profile edit must not rewrite an existing order, and an order-only override must not silently change the profile.
- Keep current customer preferences, whole-order instructions, individual item instructions and internal care notes distinct. Item exceptions must not duplicate tally counts or charges.
- Show applicable instructions on the shared work screen and during final checking. Conflicting or unsupported requests require clarification, not automatic acceptance.
- Reuse customer order history. Give care notes author/time; retain only service-relevant information and exclude internal notes from customer receipts.
- Set view/edit/correction permissions in the bounded phase design using existing roles; require an explicit action for permanent preference changes. Do not introduce Google login as a dependency.
- Use additive, default-safe API/schema changes. Preserve older customers/orders without preferences, existing save protection and migration compatibility.

**Gate:** Test a new customer with no profile, a returning customer, an order-only override, an explicit permanent change, an item instruction and an attributed note. Refresh and verify that the worker sees the saved order instructions, old orders are unchanged, and unauthorised edits are rejected.

## Phase 8B — Offers and reusable customer messages

- Let the owner create a dated bundle, such as load wash plus duvet for 15% off.
- Show eligible offers in order entry for employees. Require a clear Apply offer action and show the saving before confirmation.
- Define quantities, exclusions and whether offers can combine with other discounts or memberships.
- Save the applied offer and price on the order so later rule changes do not rewrite old receipts.
- Add message templates with checked fields such as customer name, ticket, amount and ready time.
- Start with a preview and manual copy/share. Add automatic email/SMS/WhatsApp only after a channel, consent process and costs are agreed.
- Test missing fields, wrong recipients, expired offers and attempts to apply the same benefit twice.

**Gate:** An employee can explain the discounted total, and a message preview contains only the intended customer's information.

## Phase 9 — Safaricom payment prompts

- Confirm Qinetra's merchant/PayBill arrangements and Daraja production access before promising a launch date.
- Add a Request M-PESA payment action. Prefill the customer's phone and allow a different Safaricom number for that attempt.
- Keep the saved customer phone unchanged unless a separate customer edit is requested.
- Distinguish request sent, awaiting confirmation, paid, cancelled, failed and result unknown.
- Match confirmations to the correct business, order and amount. Deduplicate callbacks and provide a way to resolve missing results.
- A phone prompt or accepted API request is not proof of payment. Keep manual payment recording clearly separate.
- Never ask staff to collect a customer's M-PESA PIN.

**Gate:** Sandbox failure paths pass, then approved live acceptance and reconciliation pass. No duplicate or unmatched payment remains.
Verify the selected M-PESA product and callback/security contract against [Safaricom's official portal](https://developer.safaricom.co.ke/apis) during implementation.

## Phase 10 — Laundry memberships, business packages and transport

This is the laundry selling services to its customers. It is separate from businesses subscribing to QLMS software.

- First estimate laundry cost, likely usage, capacity, pickup cost and delivery cost.
- Let the owner set the price, included kg, dry-cleaning units, duvet washes, trip allowance, service windows and priority rules.
- Support individual and business customers. Do not assume a business package has the same allowance or payment terms.
- Track each allowance independently in a usage history. Do not overwrite a single remaining-balance field without a record.
- Agree when a benefit is reserved or consumed, and how cancellation or a correction returns it.
- Count pickup and return as two separate trips. Track external boda trips without building an employed-driver fleet.
- Treat a laundry bag as a one-time issued benefit when appropriate, not an automatically renewed monthly item.
- Show remaining benefits and thresholds, including one trip left and exceeded kg. Agree overage prices and whether work can proceed.
- Add customer notices through the approved message channel. Define renewals, expiry, rollover, pauses and overlapping discounts before sale.
- Test simultaneous usage, monthly boundaries and reversals. An allowance must not be consumed twice.

The KES 2,500 for 30 kg idea is an example, not an approved package. At full use, it allows about KES 83.33 per kg.
The code currently lists Wash & Fold at KES 150 per kg; confirm the shop's actual rate and costs before comparing margins.
Free trips and other benefits reduce the amount available to cover washing costs. Do not sell the package until its economics are acceptable.

**Gate:** Owner-approved costing and rules; accurate usage/reversal tests; a small paid package trial before broad promotion.

## Phase 11 — Add more businesses safely

- Introduce businesses and business memberships for staff. Separate platform administrator, laundry owner and employee permissions.
- Prefer shared tables with a `business_id` and enforced boundaries over a new set of tables for every business.
- Derive the business from verified access, not a freely supplied browser ID. Scope reads, writes, exports and linked records consistently.
- Scope ticket/service uniqueness and foreign-key links to the business. A valid record ID must not allow a cross-business link.
- Migrate Qinetra into its first business record through a rehearsed, verified migration with a rollback plan.
- Test two businesses, including guessed IDs, exports, background work and callbacks. Neither business may access the other's records.
- Add platform views for business status, subscription health and system usage. Do not expose named customer records by default.
- For support access to shop records, require owner approval, a time limit and an audit record.
- Offer service templates during onboarding. Each owner can change, disable or add services and prices.
- Platform template changes must not silently replace a laundry's live prices or change old orders.
- Provide a clear export/exit procedure and agree retention/deletion rules before onboarding others.

**Gate:** Cross-business tests pass before inviting a second laundry. A hidden menu alone is not isolation.

For the initial pilot, keep Qinetra on its own production dataset. Build tenant isolation only when preparing shared commercial onboarding.

## Phase 12 — QLMS subscriptions, trials and Google login

**Guided learning requirement (10 September 2026):** Set up Google OAuth together with the student. Explain each step before it is done. The student should be able to configure the consent screen, client credentials and allowed redirect URLs, and explain identity verification, account linking, role checks and recovery. Do not complete the provider setup unattended. Use the real implementation for a short explanation and test of success, denied access and failed sign-in. This is a later phase, not permission to add OAuth now.

This is your platform charging laundry businesses for QLMS access.

- Let the platform administrator create a business and grant its first-month trial.
- Agree whether “one month” means a calendar month or a fixed number of days. Record exact start/end dates.
- Define the trial's included users, orders, modules or other allowance. The “set number” in the original discussion is still undecided.
- Define software plans, invoices/payment confirmation, renewal, expiry, reminders, grace periods and suspension.
- Prevent trial resets through duplicate signups. Test date boundaries and repeated billing events.
- Protect the business's records when a subscription expires. Agree permitted viewing, export and recovery before enforcing restrictions.
- Keep platform software prices separate from each owner's laundry service and membership prices.
- Add Google sign-in for approved staff/admin accounts. Google identity must map to an authorised business role; it must not grant access by itself.
- Retain a secure recovery route for owners who cannot use Google. Do not create a customer portal as a side effect.

**Gate:** A business can start a trial, convert, renew, expire and regain access without losing or exposing records.
The first paying businesses must justify the support and hosting effort.

## Phase 13 — Expand from evidence

Consider these only when pilot/commercial use shows a repeated need:

- Expenses, rewash/damage resolution and cost-aware reporting.
- Business invoicing, approved credit limits and recurring business collection schedules.
- More detailed transport coordination, consumables or equipment maintenance.
- Further reporting, scheduled messages and integrations.
- Multiple branches or a customer portal only as separately scoped products.

Keep one Next.js frontend and one clearly organised FastAPI application for now.
Use feature modules inside the application; selectable modules do not require separate microservices.
Extract a service only when independent scaling, failures, deployment or ownership provide a concrete reason.
An AWS-style platform or infrastructure migration is not a prerequisite for proving Qinetra's value.

## Working agreement for every phase

1. Inspect the current implementation and confirm the phase's business outcome.
2. Present the files, approach, decisions and acceptance checks. Obtain approval for that phase.
3. Build the smallest complete change in isolated test data. Do not bundle the next phase into it.
4. Run relevant contract tests, frontend lint/build and migration/concurrency checks where applicable.
5. Guide the student through the important browser action and one explanation of how it works.
6. Record what passed, what remains uncertain, changed files and the commit.
7. Update this roadmap's status, the development journal, learning/demo notes and evidence index.
8. Add a screenshot only if it proves a distinct change. Write an optional short hook/change/conclusion post draft.
9. Stop for review. Deploy only the reviewed release after authorization.

## Decisions to settle at the relevant gate

| When | Decision needed |
| --- | --- |
| Before shop acceptance | Volume and primary problem are confirmed above; confirm actual shared device, staff accounts and physical identification procedure |
| Before customer memory | Which presentation/care choices staff and the external cleaner can reliably honour; who may edit permanent preferences |
| Before corrections | Who may correct each record; cancellation, refund and collected-order rules |
| Before cutover | Approved service prices, genuine open orders, production account/budget, backup targets and real support contact |
| Before payment prompts | Merchant arrangements, Daraja access and who resolves payment exceptions |
| Before memberships | Costs, allowances, benefit timing, overages, rollover, trip zones/windows and package pricing |
| Before commercial trials | Software plan prices, trial duration/limits, grace period, suspension and support access rules |

Do not invent these answers. Work that does not depend on them can continue within the approved phase.

## Pre-mortem: why the pilot or business could fail

| Failure | Early sign | Response |
| --- | --- | --- |
| Staff return to paper because intake is awkward | Re-entry, help requests or incomplete digital orders | Observe intake; remove the specific friction before expanding scope |
| Owner cannot trust money figures | Differences between receipts, payments and reports | Stop rollout; trace records and fix definitions or write logic |
| Repeated saves create duplicate records | Same customer/order/payment appears twice after a delay | Complete phase 2 before real-data use |
| Test records contaminate the pilot | Fake customers or unexplained opening balances | Use a clean production dataset and signed-off opening records |
| Hosting interrupts the counter | Long first request, repeated timeouts or missed alerts | Measure availability, prove alerts/recovery and approve hosting changes if needed |
| A backup exists but cannot be restored | No completed restore drill | Require a tested restore before cutover |
| “Free” memberships lose money | Trips and heavy users exceed the package margin | Cost benefits, cap allowances and trial a small cohort |
| One laundry can access another's data | Inconsistent business filters or export leakage | Block second-business onboarding until isolation tests pass |
| Support becomes unmanageable | Repeated incidents with no owner or resolution | Set a real support process; fix recurring causes before selling more accounts |
| More development produces no paying demand | Feature enthusiasm without regular use or commitment | Use the phase 7 value review to choose fix, proceed or stop |

**Next product action:** Plan Phase 3A2 pre-wash checks, condition exceptions and correction history as a separate increment. Phase 3A1 is accepted locally. Student order recovery passed; student final-payment recovery was skipped and stale clothing-edit acceptance remains an open release item. Do not start 3A2 without its short implementation review.

## Guided cloud-engineering learning track

The student wants to learn Docker and eventually deploy a containerized QLMS to AWS. Use [the Docker learning guide](docs/docker-learning-guide.md), starting with image/container inspection and one disposable database. Then write the API Dockerfile together, add Compose and frontend packaging, and plan an AWS sandbox with an agreed budget. This learning track does not authorize an unattended application conversion, live data migration or cloud deployment. Google OAuth also remains guided.
