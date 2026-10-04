# QLMS premortem and acceptance register

Updated 4 October 2026 against the working tree and approved Qinetra-first decisions. This is a planning and verification register, not a claim that every scenario was tested or every risk has been removed. The [implementation roadmap](../IMPLEMENTATION_ROADMAP.md) owns sequencing and status; this file owns failure scenarios, safeguards and exit evidence.

## Confirmed operating boundaries

- Spend nothing now; retain Render/Supabase while validating Qinetra. Cloudflare frontend qualification uses fictional data and does not authorize a paid plan or framework replacement. Railway remains an alternative, not a required migration.
- Use a separate free-allowance Supabase project for real records; do not silently substitute the existing schema when capacity is unavailable.
- Employee discount ceiling is an owner-configured whole-order percentage, initially 0%; test split-line bypass and accepted replays after a policy change.
- Daily encrypted exports and an independent copy must prove the targets of one day reconstructed from receipts and four working hours to restore. Confirm destination, retention, keys and recovery owner before data entry.
- Ten trading days run alongside existing receipts with daily reconciliation. Pause entry on money/data disagreement or failed recovery. Measure task times and errors before claiming savings; revenue effects need longer observation.
- The dependency patch has local test evidence, not a whole-system security clearance. Track unresolved browser findings in [the patch record](security-patch-check.md).

## How to use this register

- **Observed** means a source or project record shows the gap. **Hypothesis** means a plausible failure to test, not an incident that occurred.
- Likelihood (L) and impact (I) are qualitative High/Medium/Low judgements, not measured probabilities. A low-frequency event can still stop release if it loses money, data or access.
- **Launch stop** means resolve the issue or agree a specific, tested restriction before the affected real workflow starts. **Feature gate** means the risk becomes blocking when that later feature is introduced.
- Tests below are proposed acceptance checks unless linked evidence explicitly records a pass. Run them with fictional customers and isolated PostgreSQL; production acceptance uses only separately authorised real transactions.
- For money examples, use a fictional KES 1,000 order with a KES 1,000 confirmed payment. Additional fixtures should state their rates, dates and expected totals explicitly.
- Recovery should retain evidence and customer history. Do not delete a suspicious transaction, erase an audit entry, repeat an uncertain payment, or restore over live records without a reviewed reconciliation plan.

## Launch and daily operation

### 1. A delayed reply creates a second order or payment

- **Basis/priority:** Observed recovery work exists; interrupted and concurrent writes remain a regression risk. L Medium / I High; launch stop if duplicates or unexplained outcomes remain.
- **Early sign:** Staff press Save again, create a second ticket, or cannot tell whether money was recorded.
- **Prevention:** Preserve the original request and save reference for unknown outcomes; clear only known rejected writes. Keep atomic writes, replay validation and PostgreSQL locking.
- **Acceptance:** Submit the same order/payment twice concurrently and hide one successful reply. Refresh, reauthenticate as the same user and retry: exactly one saved event and the original result. Different data with the same reference must be rejected. A stale rejected edit must unlock without adding history.
- **Recovery/stop:** Keep the pending reference, inspect the saved record and reconcile once. Stop affected writes if duplication occurs. Existing evidence: [transaction safety](transaction-safety-check.md), [save recovery](save-rejection-check.md).

### 2. A refund changes money but invents debt or garment movement

- **Basis/priority:** Observed current adjustment/refund limitations; truthful refunds are approved in the [handover](pilot-handoff.md). L High / I High; launch stop for refund use.
- **Early sign:** A refunded collected order becomes unpaid, or staff reverse collection solely to correct payment history.
- **Prevention:** Separate an entry mistake, service-charge reduction and return of excess payment. Preserve originals; save linked monetary events atomically with owner permission and replay protection.
- **Acceptance:** Refund KES 200 of the paid KES 1,000 service: net charge 800, retained money 800, debt 0, status still Collected. Reduce a paid charge to 800: refund due 200; return that excess without reducing charge again. Reject concurrent over-refunds and replay without duplication. Receipt, Finance and CSV must agree.
- **Recovery/stop:** Pause refund entry on disagreement; reconcile against the actual returned money and original payment. Never infer the purpose of historical refund entries during migration.

### 3. An owner correction changes the wrong record or a terminal order

- **Basis/priority:** Observed owner corrections exist; clothing replacement currently blocks Ready/Collected but does not explicitly name Cancelled. That is a test candidate, not a reproduced defect. L Medium / I High; launch stop if confirmed.
- **Early sign:** Cancelled laundry can still be edited, garment counts no longer explain charges, or an owner changes the wrong customer's ticket.
- **Prevention:** Apply consistent terminal-state rules to every mutation. Keep reason, actor, before/after values and stale checks. Item/pair corrections must preserve physical references and sent/returned links.
- **Acceptance:** Exercise each order mutation on Received, In Progress, Ready, Collected and Cancelled fixtures. Reject disallowed writes with no history change. Reassign one ticket: payments remain attached and customer history follows the corrected link. Test a two-piece suit whose billed unit is one; no reference may be duplicated or reused.
- **Recovery/stop:** Preserve the mistaken event and make an authorised correction. Until item/pair correction exists, agree a specific operational restriction or correction procedure before accepting that workflow; do not quietly change kg logic to handle pieces.

### 4. Digital garment records are correct but the wrong clothes leave

- **Basis/priority:** Physical attachment method remains an operating decision; reference, hold and outsourcing code exists locally. L Medium / I High; launch stop for outsourced work without an accepted identification process.
- **Early sign:** Detached tags, ambiguous descriptions, shared baskets without identifiers, or staff count a suit as one physical piece.
- **Prevention:** Agree durable ticket/piece references with the cleaner; check all physical pieces before handover and on return. Keep customer-reply holds and unresolved condition issues visible.
- **Acceptance:** Send a jacket and trousers as one billed suit; return one piece only. Ready must remain blocked. Return the second with an issue: still blocked until authorised resolution. Compare physical labels, register and receipt after realistic handling; every piece must be identifiable.
- **Recovery/stop:** Hold the order, reconcile with the cleaner and contact the customer through the agreed process. Never mark a missing piece returned merely to progress status. See [clothing review](clothing-intake-review.md).

### 5. Staff use paper because the digital workflow slows the counter

- **Basis/priority:** Hypothesis requiring representative staff observation; developer checks alone cannot prove adoption. L Medium / I High; launch stop for tasks staff cannot complete reliably.
- **Early sign:** Re-entry, abandoned forms, coaching on every order, or later transcription from scraps of paper.
- **Prevention:** Keep essential fields first, inline customer selection, clear saved-receipt handoff, search and actionable errors. Fix observed friction before adding optional modules.
- **Acceptance:** An unfamiliar staff member completes a returning-customer order and a new-customer mixed order with deposit/pending clothing check on the actual device. Refresh/navigation must preserve the right draft. Propose a customer/ticket lookup target of 30 seconds and agree it before measurement.
- **Recovery/stop:** Record the exact blocking step, simplify that step and repeat the task. During the pilot, record omissions for reconciliation; do not present unmeasured time savings as results.

### 6. Customer contact changes or a shared phone disclose another person's receipt

- **Basis/priority:** Shared-number choice and wrong-ticket-customer correction exist; contact editing is unfinished. L Medium / I High; launch stop for broken recipient selection.
- **Early sign:** Staff choose the first phone match, a customer receives the wrong ticket, or corrected contact details disappear after refresh.
- **Prevention:** Distinguish people who share a number, confirm the selected recipient and complete attributed contact correction. Keep internal notes out of customer drafts. Do not silently merge customers.
- **Acceptance:** Save two fictional customers sharing a number, retrieve each by name and select the intended receipt. Change only a name on a shared number, then change the phone; verify expected confirmation behaviour and one audit event. Reassign a ticket and check the warning about an earlier receipt already sent.
- **Recovery/stop:** Correct the link/contact with history, stop further sharing, and handle any actual disclosure through the agreed incident procedure. No automated resend to an unverified recipient.

### 7. The owner cannot reconcile receipts, refunds and Finance

- **Basis/priority:** Finance/export exist; scope definitions and forthcoming refund changes require reconciliation. L Medium / I High; launch stop for unexplained totals.
- **Early sign:** The owner rebuilds figures in a spreadsheet or sees receipts described as profit.
- **Prevention:** Name booking value, received money, returned money, remaining debt and refund due separately. Apply Nairobi dates consistently; align filters and exports. Add a daily-close record only if the existing views cannot support closure.
- **Acceptance:** Hand-calculate a fixture containing a deposit, later payment, discount, entry correction, service refund, excess-payment return and cancellation across two dates including Nairobi midnight. Match every displayed/exported total for identical scopes. Define whether top services means quantity, order count or booked value.
- **Recovery/stop:** Freeze the affected report claim, trace totals to records and correct the definition/query. Do not alter valid payments to make a chart balance. Profit reporting waits for agreed cost definitions.

### 8. Search becomes slow or exposes unnecessary detail as records grow

- **Basis/priority:** Observed customer/order/report paths load unrestricted result sets; list responses include nested detail. L Medium / I Medium; release concern and growth gate.
- **Early sign:** Large downloads, slow customer selection, query spikes or stale results mistaken for an empty shop.
- **Prevention:** Use bounded lists, compact response models, stable pagination and indexed filters. Fetch detailed history only when opened; show last successful refresh and errors explicitly.
- **Acceptance:** Seed a realistic larger fictional dataset and navigate every page/filter without missing or repeating records. Compare list and detail permissions; confirm search by supported phone formats. Failed refresh must show failure/staleness rather than zero customers/orders.
- **Recovery/stop:** Restore a bounded query path, inspect query timings and reduce response scope. Avoid introducing a cache or search service before ordinary database queries are measured.

### 9. A release writes real data to the wrong schema or uses incompatible code

- **Basis/priority:** Observed unqualified database setup and local/live divergence in project records; dated deployment facts must be rechecked at release. L Medium / I High; launch stop.
- **Early sign:** Empty users after deploy, demo records in the counter, missing-column errors or frontend/backend save contracts disagree.
- **Prevention:** Explicit production schema with no public fallback, restricted runtime role, migration preflight and exact frontend/backend release pair. Separate demo/test configuration visibly. Preserve existing records.
- **Acceptance:** Rehearse clean creation and upgrade from the deployed schema using intended runtime privileges. Assert the selected schema and required migration version before serving. Verify old schema records are unchanged, fresh catalog/accounts are approved, and unauthorized schema access fails. Exercise the planned deploy/rollback order.
- **Recovery/stop:** Stop writes on unexpected schema/version; inspect before changing configuration. Roll back only with a tested compatible code/schema plan. Do not remove columns or overwrite new records as an improvised rollback.

### 10. Opening records double-count money or omit laundry already in the shop

- **Basis/priority:** Hypothesis; actual opening orders/payments and current prices require owner agreement. L Medium / I High; cutover stop.
- **Early sign:** Day-one cash appears inflated, unpaid balances cannot be explained, or a physical bag has no ticket.
- **Prevention:** Inventory open laundry and verify original receipts/payments. Agree entry dates, opening-reference rules and what belongs in current-day receipts; seed no demonstration customers or payments.
- **Acceptance:** Reconcile every opening ticket to physical laundry and its verified paid/balance amounts. Compare the before/after opening inventory and financial baseline; totals must not count earlier money as newly received.
- **Recovery/stop:** Suspend cutover for unexplained differences. Correct opening entries with attributable history and owner review; preserve the original paper evidence.

### 11. Hosting, internet or power fails during a busy shift

- **Basis/priority:** Hypothesis; service-plan limitations and actual wake-up behaviour must be checked. L Medium / I High; launch stop without usable fallback.
- **Early sign:** Long first requests, repeated timeouts, frozen counter work or uncertainty after Save.
- **Prevention:** Agree dependable hosting and measure it on the shop connection. Provide temporary paper references and a re-entry/reconciliation procedure; distinguish an unsent paper order from an uncertain digital save.
- **Acceptance:** Interrupt connectivity before submission and after a server commit. Staff must select the correct fallback/retry action. Re-enter documented outage records once and reconcile money/tickets. Do not claim offline application support from draft storage.
- **Recovery/stop:** Use the paper process, retain pending save references and restore service before reconciling. A CDN or uptime ping does not replace application/database availability.

### 12. Backups or monitoring exist but do not restore the business

- **Basis/priority:** Restore, database-readiness and alert-delivery proof remain launch work; the current root health route checks only the process. L Medium / I High; launch stop.
- **Early sign:** Green monitoring while queries fail, unread alerts, inaccessible backup credentials or no completed restore exercise.
- **Prevention:** Agree acceptable data loss/recovery time, restricted backup retention, database-aware readiness, alert contacts and incident ownership. Treat CSV as an export, not a full backup.
- **Acceptance:** Restore into a separate environment and compare counts, relationships, payment totals and readable orders. Simulate database failure: readiness fails without leaking details, the agreed recipient receives an alert and recovery notification. Time the recovery against the agreed target.
- **Recovery/stop:** Use the last verified backup plus an explicit reconciliation of subsequent records. Never restore over production casually. Record incident cause, response and missing transactions before resuming normal entry.

## Security, sessions and external identity

### 13. Shared-device access is untraceable or revoked staff retain access

- **Basis/priority:** Individual accounts and session-version revocation exist; shared-screen behaviour and discount authority need acceptance. L Medium / I High; launch stop for unauthorized access.
- **Early sign:** Everyone uses the owner account, an old token still works, or a different user sees the previous person's pending form.
- **Prevention:** Individual accounts, clear lock/switch behaviour, API-side role checks, least privilege and explicit discount/date permissions. Preserve last-owner access safeguards.
- **Acceptance:** Directly call owner routes with an employee token. Disable, reset or change a user's role and verify the previous token fails. Switch users with an unfinished order and an uncertain payment: neither user may submit the other's request. Test two owners attempting to remove final-owner access concurrently.
- **Recovery/stop:** Revoke the affected account/session and review attributable events. Use a controlled owner recovery path; do not share a permanent emergency password among staff.

### 14. Secrets, vulnerable dependencies or unsafe content expose records

- **Basis/priority:** Security patch work is authorized; login lacks throttling and the current CSV writer has no formula-safe transformation. Historical secret/data-access fixes are not proof of present safety. L Medium / I High; launch stop for material unresolved exposure.
- **Early sign:** Repeated login failures, scanner findings, credentials in logs/history, or user text interpreted as a spreadsheet formula.
- **Prevention:** Patch relevant dependencies; scan Python/JavaScript and secrets without printing values. Rotate exposed credentials before any approved history rewrite. Add server-side login limits, bounded inputs, safe CSV cells, security headers and private-response caching rules.
- **Acceptance:** Verify throttle behaviour for an account and source without permanently locking out legitimate staff. Export text beginning with `=`, `+`, `-`, `@` and control characters as literal text. Test stored markup as text. Verify no frontend bundle/log includes secrets and that rejected requests write nothing.
- **Recovery/stop:** Rotate/revoke compromised credentials, preserve incident evidence, patch the cause and review affected access. Do not call an exposure a confirmed breach or assert no breach without evidence.

### 15. A session-security improvement breaks recovery or introduces CSRF

- **Basis/priority:** Observed browser tokens use sessionStorage; cookies are a proposed bounded change, not already implemented. L Medium / I High; feature gate before session migration.
- **Early sign:** Login loops, requests fail between frontend/API hosts, silent renewed sessions or lost save references after reauthentication.
- **Prevention:** Design cookie domain/origin, HttpOnly/Secure/SameSite, CSRF controls, expiry, revocation and logout together. Choose deployment origins first; preserve pending-save user scope independently of tokens.
- **Acceptance:** Exercise login, idle lock, renewal, logout, account switch and disabled-user revocation across supported browsers. Reject a cross-origin state-changing request without valid CSRF protection. Lose a successful save reply, reauthenticate and recover exactly once.
- **Recovery/stop:** Roll back through the reviewed session migration path, invalidate affected sessions and preserve pending requests. Do not fall back to permissive CORS or insecure cookie flags to make tests pass.

### 16. Google identity grants access, links the wrong account or locks out the owner

- **Basis/priority:** Hypothesis for planned Google sign-in; no linked provider identity model currently exists. L Medium / I High; feature gate.
- **Early sign:** Any Google email can enter the shop, changed email creates duplicate users, or a shared browser selects the previous person's account.
- **Prevention:** Verified provider identity must link to an invited/approved QLMS user; QLMS membership controls authority. Use provider-stable identity, deliberate secure linking, minimal identity scopes, server verification and owner recovery. Configure with the student as agreed.
- **Acceptance:** Known, uninvited, disabled, wrong-provider/client and expired identity cases must behave correctly. A same-email identity cannot silently take over an existing account. Test cancelled login, replay/CSRF protections, shared-device account choice, unlinking and loss of the owner's Google account. Unknown Google users gain no customer access.
- **Recovery/stop:** Disable the affected provider/link, revoke QLMS sessions and use the verified recovery route. Google availability must not be the sole recovery path; do not request Drive/Gmail access for basic sign-in.

### 17. Cloudflare caches private records, blocks callbacks or leaves a bypassed origin

- **Basis/priority:** Hypothesis for optional edge adoption; no Cloudflare rollout is implied by this plan. L Medium / I High; feature gate before proxy/security-rule changes.
- **Early sign:** Another user sees a cached response, login/callbacks fail, clients share one apparent IP, or attacks continue through a public origin URL.
- **Prevention:** Select a specific need and supported hosting configuration. Exclude authenticated/API responses from public cache; verify TLS, origin access, client-IP trust, CORS/cookies and callback exemptions. Keep application auth and throttling.
- **Acceptance:** Two users request private pages/API data: no response crosses identities and private data is not publicly cached. Test direct-origin behaviour, spoofed forwarding headers, legitimate login bursts, expiry and provider callbacks. Verify a reversible DNS/proxy/rule rollback.
- **Recovery/stop:** Disable the offending rule/proxy change through the agreed rollback, preserve logs and retest privacy. Do not weaken backend permissions to accommodate the edge service. Optional edge work must not delay an otherwise safe pilot.

## Future features: risks become blocking when the feature is selected

### 18. Preferences, offers or messages promise something the team cannot honour

- **Basis/priority:** Hypothesis; profiles, offers and reusable templates are future work. L Medium / I Medium; feature gate.
- **Prevention/early sign:** Unsupported care requests, contradictory notes or unexplained discounts require clarification. Snapshot agreed instructions/offers on each order, separate permanent preferences from one-off choices and internal notes, and define eligibility/stacking.
- **Acceptance:** Edit a profile after an order: its saved instructions stay unchanged. Test no profile, item exception, unsupported request, expired offer, duplicate benefit and missing template fields. Preview contains only the intended recipient's data; automatic sending requires separate consent/channel/cost approval.
- **Recovery/stop:** Hold unclear care work, withdraw an invalid offer without rewriting old prices and stop misdirected sending. No medical/allergy guarantee or automatic customer messaging is inferred from a free-text preference.

### 19. An M-PESA prompt is counted as payment or a late callback duplicates money

- **Basis/priority:** Hypothesis; current M-PESA entries are manual confirmation, not provider verification. L Medium / I High; feature gate.
- **Prevention/early sign:** Separate attempt state from the payment ledger; unexpected amounts, unknown results and unmatched references need reconciliation. Confirm merchant access and the selected provider's current security contract at implementation.
- **Acceptance:** Test denied/cancelled/failed/unknown attempts, wrong amount/order/business, repeated and out-of-order callbacks, late success after a manual entry and provider lookup failure. One verified receipt is recorded once. A phone prompt alone never marks Paid; a different payment phone does not change customer contact.
- **Recovery/stop:** Stop automatic credit for unresolved references, query/reconcile with the provider and record the owner's resolution. Never collect a customer's PIN or retry an uncertain money movement blindly.

### 20. Laundry memberships, business packages or transport lose money

- **Basis/priority:** Hypothesis; example package prices are not approved offers. L Medium / I High; feature gate before sale.
- **Prevention/early sign:** Cost full usage, external boda trips and capacity. Record separate allowances and usage/reversals; define reservation/consumption, overages, rollover, pause/expiry and discount stacking. A bag may be one-time; pickup and return are two trips.
- **Acceptance:** Simultaneously consume the last allowance, cancel and reverse it, cross a period boundary, overlap packages and exceed kg/trips. No benefit is consumed twice or silently renewed. Business terms can differ from individual terms. Compare trial usage costs against approved pricing before wider promotion.
- **Recovery/stop:** Suspend new package sales when costs/rules fail; honour existing commitments through an owner-approved resolution. Preserve the allowance ledger instead of overwriting remaining balances. Do not build driver-fleet software for occasional external trips.

### 21. A second laundry accesses Qinetra data or support access becomes unrestricted

- **Basis/priority:** Observed no multi-business model; current single-shop access is not tenant isolation. L Medium / I High; mandatory gate before the second business.
- **Prevention/early sign:** Derive business scope from verified memberships; scope queries, linked records, unique keys, exports, jobs and callbacks. Platform support access requires owner approval, expiry and audit; templates never overwrite live prices.
- **Acceptance:** With two fictional businesses, attempt guessed IDs, cross-business foreign links, exports, invitations, revoked memberships, background jobs and payment callbacks. All unauthorized paths fail without data disclosure/write. Template updates leave existing services/prices and old orders intact.
- **Recovery/stop:** Stop onboarding and revoke support access on isolation failure; investigate scope and affected records. Rehearse migrating Qinetra into its business record with a verified rollback before changing production.

### 22. Software trial/billing rules trap records or grant repeated free access

- **Basis/priority:** Hypothesis; QLMS software subscriptions are separate from laundry customer memberships. L Medium / I High; feature gate.
- **Prevention/early sign:** Agree exact trial start/end, limits, billing/reconciliation, grace, suspension, read/export and recovery rights. Detect duplicate/replayed billing events without treating a new signup as automatic trial eligibility.
- **Acceptance:** Start, convert, renew, expire, suspend and reactivate a business at boundary dates; replay payment events. No duplicate charge/extension, lost records or cross-business access. An expired subscription retains the explicitly agreed viewing/export/recovery options.
- **Recovery/stop:** Resolve disputed billing through an attributable admin action and preserve business records. Do not hard-delete customer history because software access expired.

### 23. Later expansion adds complexity or misleading financial claims

- **Basis/priority:** Hypothesis for expenses/profit, B2B credit/invoices, transport, consumables, equipment, deeper reporting, automatic messages, branches or a portal. L Medium / I Medium; individual feature gates.
- **Prevention/early sign:** A repeated operational need and clear data owner precede each module. Expenses alone support cash movement, not necessarily profit. Define credit/collection rules, scheduling/capacity, inventory units, maintenance responsibility and message consent before automation.
- **Acceptance:** Each feature has a representative success case, correction, permissions, concurrent use and historical-data case. Reconcile cost/report definitions; test overdue credit and invoice adjustments. Branch/portal access requires its own isolation/privacy design; offline synchronization requires conflict/replay design.
- **Recovery/stop:** Disable the optional workflow with preserved records and return to the documented manual process. Do not add microservices, a general rule engine or predictive charts solely to make the architecture look advanced.

### 24. Docker/AWS learning disrupts the shop or creates uncontrolled cost

- **Basis/priority:** Guided learning is approved as a separate track; no production migration is implied. L Medium / I Medium; learning/deployment gate.
- **Prevention/early sign:** Use disposable data, explicit budget/region, least-privilege credentials and cleanup ownership. Package the existing app before considering infrastructure migration; never bake secrets into an image.
- **Acceptance:** Student explains image/container, ports, volumes and secrets; rebuilds/tests the API and frontend; proves browser-reachable API configuration and readiness. Before AWS, verify budget alerts, teardown and a separate data environment. Any later production move requires migration/restore/rollback proof.
- **Recovery/stop:** Stop/remove only verified lesson resources, preserve real records and inspect unexpected bills. Follow the [Docker learning guide](docker-learning-guide.md); the shop need not move to AWS to benefit from the lesson.

### 25. Downloaded spreadsheets become a competing record or misleading report

- **Basis/priority:** Approved later O1b report work; launch O1a still needs trustworthy existing totals. L Medium / I High; report gate.
- **Prevention/early sign:** One calculation contract for screen/XLSX/CSV; distinguish bookings, received/returned money and current attention outside the period. Mark generation time and definitions. Keep identifiers as text, money numeric and untrusted formula-like text literal. Edited downloads do not write to QLMS; CSV is not a backup.
- **Acceptance/recovery:** Reconcile a hand-calculated multi-date fixture including legacy unknown methods, corrections/refunds and older debt. Open exports in Excel/free reader, exercise large exports and permissions. Suspend a wrong export with records preserved; do not invite staff to correct live data in a spreadsheet.

### 26. AI gives plausible advice from wrong or identifying data

- **Basis/priority:** AI1 is optional reviewed assistance; AI2 remains later funded work. L Medium / I High; privacy/analysis gate.
- **Prevention/early sign:** Ordinary rules identify known exceptions. A separate approved aggregate pack excludes identifiers/free text and reviews sparse groups. Verify scope/dates/units, treat documents as untrusted data, distinguish facts from hypotheses and check recommendations before an owner acts. Do not turn client consent into blanket customer-data access.
- **Acceptance/recovery:** Test missing history, misleading aggregates, prompt injection and recommendations outside capacity/cost limits. Compare source figures and record review time/corrections for a brief of at most three actions. No autonomous price, refund, collection or message changes. Stop external analysis on uncertain permissions/disclosure; normal QLMS use remains available.

### 27. Reported value exceeds real savings or support cost consumes the margin

- **Basis/priority:** Founder-private V1 evidence and later commercialization. L Medium / I High; sales/measurement gate.
- **Prevention/acceptance:** Comparable timed intake/lookup/close samples, recorded errors/workarounds and honest baseline. Keep time released, extrapolated labour value, recovered debt and new sales separate; include onboarding, hosting and support effort. Founder-only access is server-side and tied to the approved account, not every owner. Do not claim causal revenue growth from ten trading days.
- **Recovery/stop:** Correct unsupported claims and stop an unprofitable optional service before adding automation to conceal its cost. Use anonymized evidence only with appropriate approval.

The 4 October discount check record verifies the whole-order boundary, split-line attempts, concurrent policy changes and accepted retry after reduction. Student acceptance is still open. C3 must also examine the observed order-form versus created-result promised-time display difference; no timezone fix is implied by this discount increment.

## Business decisions and evidence ownership

| Gate | Decisions needed from the owner/student |
| --- | --- |
| Daily-work acceptance | Real device/users, backdated-entry authority, physical labels/cleaner procedure, collection acknowledgement, any actual partial-collection or credit need. Discount ceiling is decided above |
| Corrections | Item/pair handling after outsourcing, refund/return exceptions, contact-edit/shared-phone behaviour; do not reopen already approved refund basics |
| Cutover | Catalog/prices, genuine opening laundry/money, free capacity, backup destination/retention/key recovery, support/alert contacts and export/deletion process. Zero spend and recovery/trial targets are decided above |
| Google/edge | Approved staff identities and recovery owner; actual Cloudflare problem, domain/hosting compatibility and configuration rollback |
| Care/offers/messages | Supportable care choices, editing permissions, offer eligibility/stacking and consent/channel/cost for any automated message |
| M-PESA/packages | Merchant access, payment exception owner, costs/allowances/trip zones/windows, benefit timing, overages/renewal/expiry and business terms |
| Commercial onboarding | Permission boundaries, approved support access, software prices/trial limits/grace and record access during suspension |

The person implementing an increment records automated evidence; the student/staff performs the important browser/physical workflow; the owner approves business rules and exact cutover. The release reviewer checks unresolved launch stops in this register. Do not substitute a screenshot or passing unit suite for the relevant acceptance gate.

Source pointers: [backend routes](../backend/main.py), [models](../backend/models.py), [auth](../backend/auth.py), [database setup](../backend/database.py), [save recovery helper](../frontend/src/lib/pending-save.js), [session context](../frontend/src/context/auth-context.js), [real-data setup record](../QINETRA_PILOT_START.md), [current handover](pilot-handoff.md), [maintenance standard](engineering-guidelines.md). Some setup records contain dated observations; verify current infrastructure at the release gate.
