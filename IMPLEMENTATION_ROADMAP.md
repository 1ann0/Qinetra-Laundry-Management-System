# QLMS implementation roadmap

Updated 5 October 2026. This is the canonical plan for the Qinetra pilot and later development. It replaces the older phase-status summaries in this file. Historical test runs remain in the development journal; current continuation instructions are in [the handover](docs/pilot-handoff.md).

The user approved implementation of the Qinetra-first plan. Their 5 October instruction batches the essential pilot work: build small changes and run developer checks, then hold one final staff acceptance session before deployment. Do not stop for separate quizzes or per-feature approval. Preserve unfinished work; later features remain conditional on their stated gates. No purchases or unqualified cutover are authorized. Truthful refunds retain their earlier approval.

## Approved decisions

- Qinetra is the family business and first beneficiary. Prove easier daily work before marketing software or focused solutions to other businesses.
- Spend nothing now. Retain Render for the API and Supabase PostgreSQL while validating the product. Do not migrate to Railway, buy credits or enable paid resources by default.
- Qualify Cloudflare separately with fictional data; preserve Next.js and current order URLs. An unqualified free deployment is not a production guarantee.
- Use a separate Supabase project within the available free allowance for Qinetra's real dataset. Do not silently fall back to the old public/demo schema if capacity is unavailable.
- Employee discounts have an owner-configured whole-order percentage ceiling, initially 0%. The backend enforces the combined discount across lines.
- Recovery target: daily encrypted exports with an independent copy, up to one day reconstructed from retained receipts, restored operation within four working hours. Prove these targets before claiming them.
- First trial: ten trading days alongside existing receipts, with daily reconciliation. The shop does not become dependent on free hosting without a further reliability/funding decision.
- Google sign-in follows a stable pilot and session hardening. It can precede multi-business features and billing.
- QLMS becomes Qinetra's main record after the launch gates pass; receipts remain the transition/recovery fallback. Other clients can use fictional-data practice and an agreed parallel-entry period before cutover.
- Approved report direction: Excel workbook plus CSV, daily control first, and AI-assisted reviews prepared and checked by the founder. These additions do not postpone essential pilot work; see the reporting/AI section below.

Product intent is in [PRD.md](PRD.md), technical decisions and their short outline in [ARCHITECTURE.md](ARCHITECTURE.md), data/recovery requirements in [DATA.md](DATA.md), and controls/gaps in [SECURITY.md](SECURITY.md). These documents distinguish requirements from implemented behavior.

## Outcome and scope

Make the daily loop dependable: find the customer, receive the right laundry, quote correctly, record clothes and money, complete work, return the right clothes and reconcile the day. The owner should find an answer without rebuilding it from paper receipts.

Start with one laundry and one location. The previously confirmed working volume is about 10 orders daily, occasionally 20 at peak; confirm it during the pilot. Staff may share a screen but use individual accounts. Prioritise correctness and simple recovery over a large feature list.

Keep a stable released version in use while improvements are developed against fictional data. Do not test on real customer records or deploy an unfinished branch merely because a local feature passes. The first release requires S0, C1/C2/C2p, S1a-c, C3, O1a, D1, R1 and P1. S2, O1b and optional growth are separate; bring a specific item forward only when launch checks expose an unacceptable risk or unusable workflow.

After that baseline, release small verified improvements to the pilot without waiting for the later roadmap. Prioritise work that saves staff time, prevents money/data errors or removes a launch blocker. Run checks proportional to the changed behavior; repeat wider suites only for new code, failures or unresolved risks. Keep detailed evidence in the relevant check record and link it from brief handover/learning notes instead of copying it. The 29 September refund-form follow-up addresses an observed wrong-action selection; it is not a reason to expand refund scope.

5 October release decision: real-data pilot before updating the fictional online demo, preserving existing records. After free-slot/cost verification, `QLMS-Qinetra-Pilot` was created in `1ann0's Org` and its empty schema protected. No real records, login credentials, cloud folder, paid resource, push or deployment were added. The independent cloud destination is still unanswered. Recheck frontend commercial-use eligibility; the Cloudflare prototype has build evidence but failed local browser qualification. Render Free remains a supervised-trial limitation. See [current essentials evidence and remaining gates](docs/pilot-essentials-check.md), and [skill triggers](docs/skills-workflow-guide.md).

The first coding increment is [Nairobi ready-time correctness](docs/ready-time-check.md): form, suggestion, validation, review and request conversion share an explicit Nairobi interpretation. Existing UTC/legacy saved times and pending saves retain their contracts. Staff acceptance and all real-data release gates remain separate.

## Evidence and boundaries

| Area | Dated evidence (local status updated 5 October) | Limit |
| --- | --- | --- |
| Live backend | Render reports live commit `5da24e5` from 10 August; its OpenAPI endpoint responded HTTP 200 during this task | It lacks the newer local correction/recovery routes. Vercel's exact deployed revision is not independently verified |
| Real-data area | New `QLMS-Qinetra-Pilot` (`istweeaqtykwfuhntgik`) has all 20 application tables and zero users/customers/orders/services; full migration/reapplication/restore rehearsed locally | Runtime/backup roles remain NOLOGIN; actual connections, owner and catalogue still required. No old project was changed |
| Database protection | All 20 new tables have RLS; browser schema usage denied; separate restricted runtime/read-only backup roles; security advisor has no findings | Narrow clothing-replacement DELETE grant is locally tested but remotely blocked pending explicit approval. FastAPI authorization remains necessary |
| Existing product | Customer and service histories, search, mixed orders, pricing snapshots, garment checks/references, outsourcing, holds, manual payments, owner Finance/catalog/staff controls exist in local source | Some staff scenarios remain unaccepted. Existing code must be verified rather than rebuilt from this plan |
| Save recovery | `d6559aa`: developer and student two-tab and lost-reply/refresh/retry acceptance recorded; isolated commit had 134 PostgreSQL-backed checks, frontend had 50 tests | These are prior results, not tests rerun for every later change. Explain-back remains a learning task, not a new release blocker |
| Contact editing | Backend, owner editor/history and migration 020 were locally verified on 29 September; see [the contact checks](docs/customer-contact-check.md) | Student acceptance remains pending; no production migration or deployment |
| Employee discount authority | Locally verified on 4 October; migration 022, owner setting/history, whole-order API ceiling and replay tests; student reports functional completion | Explain-back and release remain open; see [the discount checks](docs/discount-policy-check.md) |
| Order/request feedback | Locally verified 4 October: visible allowance, inline/focused errors, shared animated wait status and bounded read-only retries; 66 frontend tests, lint/build and desktop/phone checks; student reports functional acceptance 5 October | Independent tab-return evidence, accessibility and broader session review remain open; see [the feedback checks](docs/order-feedback-check.md) |
| Dependencies | Next.js/eslint-config-next 16.3.6; current production npm and pinned Python/operations audits report zero findings | Full npm audit has one unpatched braces advisory affecting five development dependency entries; no whole-system security claim |
| Sessions/security | Shared DB login limits, password/input boundaries, safe CSV/private headers and expired-receipt/payment-draft recovery implemented; 198 backend tests with PostgreSQL and 75 frontend tests, lint/build passed | Cookie/nonce migration remains separate; proxy/HTTPS and final staff acceptance are open |
| Operations | Readiness/schema/role checks and encrypted separate-database restoration passed locally, including clothing/contact histories and payment/refund totals | Real export/cloud upload, task/key recovery, alerts, hosting, exact release pair and operational recovery targets remain unproved |

The live metadata above is a dated read-only observation. Recheck configuration at release. Do not copy sample customers or credentials into the new dataset. Preserve old records until the owner identifies which are genuine and approves their treatment.

## Architecture essentials

- Keep Next.js/React/Tailwind, a small fetch helper, FastAPI, SQLAlchemy and PostgreSQL. No new state framework, microservices, empty scaffolding or forced cloud migration.
- Browser access to data goes through application authorization. Never add a Supabase public key/client merely to follow a generic checklist.
- FastAPI validates the current active user and role for every protected action. Hiding a frontend button is not authorization.
- Money uses decimal calculations and saved prices. An original payment, an entry correction, a returned payment and a reduced service charge are different facts.
- Preserve original observations and attributed corrections. Garment custody is independent of payment corrections.
- Unknown save outcomes retain the original request/key. Only recognized definite not-saved responses clear that attempt. New proxies, auth flows and integrations must preserve this.
- Real-data connections select an explicit approved schema and fail closed on a mismatch. Runtime access cannot create/drop schemas or reach unrelated application datasets. Migrations use a separate privileged path.
- Current authentication is local bcrypt passwords plus 30-minute bearer JWTs stored in sessionStorage. Secure cookie/session changes and Google identities below are proposed work, not current capabilities.
- Single-shop scope is current. Tenant isolation is mandatory before a second business, not a hidden assumption about today’s records.
- Prefer additive migrations and compatible API changes. Rehearse upgrade, release order and rollback before applying them to production.

## Execution order and starting conditions

| ID | Small outcome | Start / approval status | Main code or configuration | Exit evidence |
| --- | --- | --- | --- | --- |
| S0 | Patch affected frontend dependencies | Locally verified 28 September; not deployed | frontend package manifests/lockfile and patch check record | 50 tests, lint/build and ordinary browser smoke passed; retain the broader session-recovery review |
| C1 | Truthful owner refunds and payment corrections | Locally verified; student service-refund repeat passed 29 September; not deployed | backend models/schemas/routes/migration 021; receipt, order, Finance/export views | [Refund evidence and exact checks](docs/refund-check.md); 146 backend and 52 frontend checks, lint/build, refund browser recovery and reporting |
| C2 | Complete essential customer contact correction | Locally implemented and developer-verified; student check pending | migration 020, customer correction routes and owner UI | 156 backend tests including PostgreSQL, 52 frontend tests, lint/build and browser checks; details in docs/customer-contact-check.md |
| C2p | Enforce employee discount authority | Locally verified 4 October; student reports completion; explain-back and release pending | migration 022, backend discount policy, owner setting and order entry | 171 backend tests with no PostgreSQL skips, 55 frontend tests, lint/build and fictional browser checks; docs/discount-policy-check.md |
| S1a | Login and request protection | Implemented/developer-verified 5 October; actual proxy configuration still open | auth/login, migration 023, security tests | Shared PostgreSQL throttle, safe password bounds, generic errors and login body bounds; current check record |
| S1b | Safe exports and private responses | Implemented/developer-verified 5 October; deployed headers still open | CSV route, response policy, Next/API configuration | Text formula neutralization, private headers/cache rules and sanitized failures; current check record |
| S1c | Secret/dependency review and current-session safety | Local scans/session recovery/logout verified; actual credential/proxy configuration and final acceptance open | auth/session helpers, scans/CI | Redacted scans, rotation evidence where needed, expiry/revocation/logout/recovery and user-switch tests; explicit residual-risk assessment |
| C3 | Close daily-work correctness and staff acceptance | Reuse accepted tests; exercise only remaining scenarios and new findings | item/status/outsourcing routes, audit records and relevant screens | Terminal-state matrix, physical labels, collection/returns and final-payment recovery pass |
| O1a | Trustworthy daily close and usable existing retrieval | Required for launch; bring forward only demonstrated retrieval/privacy failures | existing financial summary/export/query contracts and owner/customer/tracking pages | Hand-calculated fixture matches screens and supported CSV scope; customer/ticket lookup works on the expected pilot dataset |
| D1 | Prepare Qinetra's real dataset | Empty separate project/schema created; restricted roles still NOLOGIN; limited grant approval, credentials/catalogue/accounts open | database config, migrations, provisioning/verification scripts, DATA.md | Explicit schema/restricted role, upgrade rehearsal, approved catalogue/accounts/opening records; old data untouched |
| R1 | Prove recovery and release operation | Local schema/encrypted restore/readiness passed; real cloud/schedule/alerts/hosting still open | readiness route, hosting settings, backup/alert/runbooks | Actual backup/readback, operational recovery, alerts, paired versions, rollback and outage reconciliation demonstrated |
| P1 | Start controlled daily pilot | Exact cutover approval required after preceding gates | reviewed release pair and signed-off dataset | Train staff, supervised start, daily reconciliation and proposed ten trading-day review |
| S2 | Secure cookie/session migration | Separate approved increment after the pilot, before A1; move earlier if S1c finds an unacceptable session risk | auth/session helpers and reviewed same-origin server boundary | Cookie/CSRF, expiry, revocation, logout, browser compatibility, identity switching and uncertain-save recovery pass |
| O1b | Better filters, compact lists and owner work lists | After pilot evidence; specific O1a failures move ahead of launch | query/response models, pagination, filtered exports and Needs attention UI | Screen/export filters agree; larger-data search is bounded; staff can act on useful exceptions |
| A1 | Optional Google sign-in | After S2 and stable pilot; can precede multibusiness/billing | linked identities, auth routes, login UI and Google project config | Guided setup; unknown/disabled identities denied, safe linking/recovery and shared-device tests |
| G1 | Customer care/preferences that reach workers | Pilot evidence and supported care options | customer profile/order snapshots/instructions/notes | Current profile and saved order instructions remain distinct; no history rewrite |
| G2 | Offers and reusable message templates | Approved eligibility, stacking and channel rules | offer rules, saved application records and manual preview UI | Correct eligibility/prices; no wrong-recipient or internal-note disclosure |
| G3 | Verified M-PESA workflow | Merchant/Daraja access and reconciliation owner ready | payment attempts/callbacks/reconciliation + UI | Failure/unknown/duplicate/late result tests; approved live payment and reconciliation |
| G4 | Costed laundry memberships/B2B packages and trips | Costs, capacity and rules agreed first | separate benefit/usage ledger, packages/trips | Concurrent consumption/reversal/boundary tests; small viable paid trial |
| M1 | Multiple businesses, invitations and platform administration | Only when preparing another laundry | business memberships, all scoped data paths and admin UI | Adversarial two-business isolation tests before the second business joins |
| M2 | QLMS software subscriptions/trials | M1 and commercial rules ready | software plans, trial/entitlement/billing events | Start/convert/renew/expire/reactivate without duplicate billing or trapped records |
| E1+ | Conditional operating improvements | Repeated measured need; separate increment per item | See future inventory below | Outcome-specific acceptance and owner value, not feature count |
| L1+ | Docker/AWS learning | Parallel learning using disposable resources and agreed budget | Docker guide; later Dockerfile/Compose/sandbox | Student can explain/run/restore the sandbox; shop deployment unaffected |

S1 is three implementation reviews, not a combined security rewrite. O1a/O1b and R1 likewise split into small changes when implementing. S2 is not silently required to launch: S1c must assess the JavaScript-readable token risk and existing controls; an unacceptable finding changes the release decision explicitly. A1/G1/G2 can be chosen by demonstrated benefit after the pilot; their ordering is not a promise that every growth feature will be built.

## C1: truthful refunds — local implementation and acceptance

- Owner-only partial/full service refunds, including after collection, with original payment, reason, actual returned date/method and confirmation that money really returned.
- Keep original payment and price history. A service refund reduces charge and retained money. Returning excess payment reduces retained money without reducing the charge again.
- Add `POST /orders/{order_id}/refunds`, refund purpose/charge reduction and `net_charge`/`refund_due`. Preserve older payment-adjustment replays; do not infer historical refund purpose.
- Debt = max(net charge - net payments, 0); refund owed = max(net payments - net charge, 0). A collected, paid KES 1,000 order with a KES 200 service refund stays Collected, charge/retained money become KES 800 and debt is zero.
- Allow valid kg corrections to create an excess payment to return. Allow entry corrections after collection without lying about physical custody.
- Use locks, atomic writes and idempotency; update receipt, Finance, outstanding figures and exports together. Test separate booking/payment/refund dates and Nairobi boundaries.
- No automatic transfers, store credit or compensation exceeding the service charge in this increment.

## C2/C3: finish corrections and physical accountability

- Finish owner name/phone correction with attributed before/after history; test name-only edits where the phone is already shared. Do not silently merge customers.
- Retain wrong-customer ticket reassignment, kg correction at saved rates, cancellations and one-step stage reversal. Only reverse Collected when the clothes really remain at the shop.
- Review every mutation against cancelled/collected states, not only the status endpoint. The current clothing-edit guard names ready/collected but not cancelled: this is a source-review concern requiring a route test.
- Decide the smallest attribution for normal status/collection actions; current owner corrections have actors, but ordinary stage changes do not have equivalent event history.
- Item/pair billed-quantity correction remains explicit deferred work: it must preserve garment identity, counted pieces and sent/returned records. Before accepting that workflow, implement the bounded correction or agree a truthful audited restriction. Never instruct staff to delete/recreate paid tickets or invent custody.
- Complete remaining staff checks for clothing edits, final-payment recovery, holds, outsourced partial returns and reauthentication. Do not repeat already accepted kg checks without a regression reason.
- Physical labels must stay with bags/garments through processing and cleaner handover. Agree the attachment method with the cleaner; a database reference alone cannot identify an unlabelled garment.
- Partial collection, credit collection, duplicate-customer merge and a partner portal are not assumed requirements. Record observed need and design each separately.

## S1/S2: security controls fitted to this codebase

- Retain bcrypt and backend-derived roles. Validate login byte/length bounds consistently: bcrypt 5 rejects passwords over 72 bytes and the current login path does not handle that safely. Never silently truncate.
- Add bounded login throttling using trusted client IP plus account limits; test shared-shop networks, expiry, generic responses and restart/multiple-worker behaviour. Do not introduce Redis solely for a one-instance pilot without evaluating a simpler bounded design.
- Employee discount ceiling is implemented locally as its own increment: migration 022, authenticated retrieval, attributed owner changes, combined whole-order enforcement and accepted replay before policy validation. See [the discount check record](docs/discount-policy-check.md) for dated checks and pending hands-on/release gates. Do not reimplement it during login hardening.
- Keep bound SQL parameters. Add finite/range/size limits where missing, including arrays and body/search sizes. Keep field allowlists; never accept browser-supplied actor, role, saved price or permission decisions.
- Escape spreadsheet formulas separately from CSV quoting. Preserve numeric money columns and legitimate phone text.
- Add tested CSP and security headers, production HTTPS/TLS settings, explicit CORS, and private/no-store policies. Inspect the deployed response, not just a config file.
- S2 preferred session direction: HttpOnly/Secure, appropriately scoped cookies through a reviewed same-origin boundary, with CSRF/origin checks. A small Next server proxy may keep the FastAPI token away from browser JavaScript; evaluate deployment/routing and keep business authorization in FastAPI. Do not bolt cookies onto the current cross-origin flow without designing both sides. Until then, explicitly record the residual JavaScript-readable-token risk and launch review outcome; a short token lifetime alone does not remove it.
- Preserve inactivity lock, server expiry, current-role lookup, account revocation, shared-screen logout/switching and uncertain-save recovery. Test old tabs, identity change and stale responses; do not expose another user's draft.
- Complete redacted current/history secret scans and Python dependency audit; verify rotation of previously exposed credentials. Rotate/revoke first; coordinated history rewriting is a separate reviewed action. Do not put scan findings containing credentials in commits or screenshots.
- Add repeatable dependency/secret checks for reviewed changes and regular maintenance. Triage actual reachability; absence of findings is not a penetration-test certificate.
- No public signup. Do not collect unnecessary personal information. Restrict logs, exports and backups, and agree retention/exit/deletion handling.
- No current upload feature: when one is approved, define authenticated access, file types/size, generated names, content checking and safe storage before accepting files.
- CAPTCHA/Turnstile is conditional on abuse after throttling, not a required step for every staff save.

## O1a/O1b: owner insight and customer retrieval

Improve the existing screens. Finance already distinguishes bookings from receipts and has service/customer rankings. O1a requires correct existing figures and usable existing lookup; O1b adds filters/work lists/pagination after pilot feedback unless a concrete O1a failure requires an earlier fix. Additional charts and a new dashboard are not launch requirements.

- Reconcile bookings, discounts, entry corrections, service refunds, overpayment returns, cancellations and outstanding debt. Label whether an outstanding figure covers orders booked in a period or all current debt.
- Add filtered customer/service/date exports matching the screen's definitions. Show filters and data freshness; do not show a failed load as zero activity.
- Make a short Needs attention list linking to due/late work, pending checks/holds, overdue collection, outstanding money and missing outsourced returns. Reuse existing filters.
- Add bounded pagination and compact order/customer list responses; fetch full details on demand. Use a larger fictional dataset and actual staff device to agree retrieval targets; profile queries before adding indexes/caches.
- Add an explicit daily reconciliation record only if the owner cannot close reliably with existing views.
- After useful real history exists, compare periods, service mix, repeat-customer activity, on-time work and correction/rewash rates. Define denominators and incomplete history clearly.
- Income or net cash movement is not profit. Expenses and cost allocation require their own definitions before margin/profit labels.

## D1/R1/P1: real records, recoverability and first release

1. Rehearse the exact current migrations on both an empty dataset and a representative prior schema. Do not substitute ORM create_all for proving the production migration path.
2. Configure an explicit production schema/role, fail-closed preflight and schema revision check. Test that the runtime cannot reach old/demo records or perform DDL. Apply migrations separately; RLS policies/grants must actually allow this intended server role.
3. Keep browser roles denied. Custom FastAPI JWTs do not automatically populate Supabase auth.uid(). Use the approved separate Supabase project within the available free allowance. Confirm allowance before creating it; stop provisioning if this would incur spending. The old protected schema and public records remain preserved, not a silent alternative real-data destination.
4. Create the real first owner through a safe private process, then individual staff accounts. Use hidden password input and the same validation as normal account management. Set owner-approved prices/clothing lists; no fixture credentials.
5. Sign off genuine opening orders, clothes in custody, amounts already received and remaining debt. Distinguish historical opening money from today's till receipts; avoid double collection or double-counted income. Preserve and classify legacy data before any import.
6. Implement daily encrypted exports with an independent copy, retained receipts, a target of at most one day reconstructed and restoration within four working hours. Confirm responsible person, storage destination, retention and key recovery before real-data entry. Restore separately, compare counts/relations/money and prove the restored application works. CSV is not a database backup; targets are not measured results.
7. Add database-aware readiness without customer data/secrets; keep liveness separate. Configure the requested frontend/API monitoring and prove an alert reaches the agreed person and recovery is reported. Monitoring is not a substitute for reliable hosting or an end-to-end save check.
8. Maintain the zero-spend constraint. Render Free can sleep and exhaust its shared allowance; Cloudflare does not remove that delay. Check allowances before and during the supervised trial. Qualify the frontend as below; do not use a noncommercial-only hosting tier for Qinetra business operations. Fund dependable hosting before shop dependence.
9. Review exact frontend/backend revisions, migration version, API URL, CORS, TLS and credentials. Rehearse compatible release order and rollback; rolling code back cannot undo real payments or safely reverse every migration.
10. Agree a paper outage procedure with temporary references and later reconciliation. Resolve uncertain online saves before re-entering an order. Offline sync is not promised.
11. Obtain approval for the exact reviewed trial release and real-data setup. Train one operator, retain existing receipts as fallback and reconcile every trading day for ten trading days. Extend observation if key workflows were not exercised. Do not treat this parallel trial as approval to discard manual records.
12. Record baseline and observed intake/search/closing time, missed garments/instructions, unexplained balances, duplicate saves and staff workarounds. No fabricated percentages. Stop expansion for missing records, cross-user disclosure or unexplained money; fix and verify before growing.

Develop later features on fictional data, with separate configuration and reviewed migrations. Keep production stable, label test environments clearly, release small compatible increments and retain a written version/rollback record.

## A1: Google sign-in — when, why and safe design

Add this after secure session/recovery work and a stable single-shop pilot, if staff would benefit. It can precede memberships, multi-business onboarding and software billing; the older plan unnecessarily bundled it with commercialization. It is not a launch prerequisite.

Use current **Google Identity Services, Sign in with Google**, and its supported FedCM browser experience. This is OpenID Connect identity, not a new “OAuth 3” version. Use official current GIS guidance rather than legacy gapi.auth2 examples.

Benefits: fewer extra passwords/reset requests, convenient identity for staff who use Google, and reuse of Google account protections. Do not claim every Google sign-in proves MFA. It does not grant QLMS roles or automatically integrate Gmail, Drive, Sheets or Calendar.

- Add a small external-identity mapping to existing users: provider, verified issuer/subject, linked user and audit information. Enforce uniqueness and safe concurrent linking.
- Verify signature, issuer, audience and expiry with a maintained Google verification library; verify nonce/CSRF protections appropriate to the chosen flow. Decoding is not verification.
- Authorize only an existing owner-approved account through authenticated linking or a narrowly scoped expiring invitation. Do not auto-create staff or auto-link solely by email.
- Issue the ordinary QLMS session afterward. Continue active-account, current role and token/session-version checks. A disabled employee remains denied even with a valid Google identity.
- On the shared counter, start with an explicit button/account chooser and automatic selection off. Clearly display the acting staff member. Test account switching and retained Google browser sessions.
- Preserve a tested owner recovery/local-login route initially. Do not allow unlinking the last usable identity or losing the only owner.
- No Google API scopes/tokens beyond what sign-in requires. Later integrations need a separate business purpose, consent, minimum scopes and token lifecycle design.
- Provider console setup remains a guided lesson with the student: authorized origins/redirects, consent configuration, client identifiers/secrets as applicable, identity verification, account linking and recovery. Do not configure it unattended.

Acceptance includes unknown Google user, disabled staff, changed role, wrong audience/issuer, expiry, duplicate links, reused invitations, cancellation, blocked scripts, Google outage, lost Google account and shared-device logout. Verify the selected GIS options against current docs at implementation time.

References: [GIS overview](https://developers.google.com/identity/gsi/web/guides/overview), [backend ID-token verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token), [current JS/FedCM options](https://developers.google.com/identity/gsi/web/reference/js-reference).

## Hosting and Cloudflare qualification

Provider comparison was checked against official documentation on 27 September 2026. Costs below are planning reference points, not purchases, guaranteed bills or a substitute for checking current allowances at deployment.

| Component | Benefit | Cost/recovery tradeoff | Approved decision |
| --- | --- | --- | --- |
| Cloudflare frontend | Low-cost delivery and scaling | Workers Free has dynamic CPU limits; paid starts at USD 5 plus applicable usage; Next.js needs runtime qualification | Separate fictional-data experiment using OpenNext; no framework replacement |
| Railway API | Straightforward FastAPI and usage billing | Hobby minimum USD 5 includes USD 5 usage; actual bill may exceed it | Alternative only after representative cost/operation comparison |
| Render API | Already connected; avoids a migration | Free sleeps and shares 750 monthly runtime hours per workspace; unsuitable for permanent production reliance | Keep for supervised testing; assess funded dependable hosting before shop dependence |
| Supabase PostgreSQL | Existing code and operational familiarity | Free requires our own off-site export/restore procedure; paid starting cost is higher | Keep; prepare a separate free-allowance real-data project |
| Neon PostgreSQL | Database focus and scale-to-zero | Free compute/network exhaustion can suspend access; migration/restore work remains | Reconsider only if measured cost warrants it |
| Railway PostgreSQL | Private access near a Railway API | Standard templates are unmanaged; backup/maintenance/security are our responsibility | Do not move Qinetra's database now |

The Cloudflare experiment preserves order URLs and the current API boundary. Pin a compatible OpenNext version, verify on Linux and test login, direct receipt links, refresh, images, exports, user switching and uncertain saves. Check worker CPU/bundle limits with representative fictional traffic. Do not auto-create billable caches/buckets. If Free cannot pass, keep local practice and resolve funding before a remote trial; never silently buy a plan or use a noncommercial-only tier for shop operations.

Cloudflare's current general Next.js guide recommends vinext, but vinext's own compatibility guidance identifies OpenNext as the mature option. This existing application will be tested with OpenNext rather than replacing its framework to reduce hosting cost. No adapter has been installed and no qualification result is claimed yet.

Sources: [Railway pricing](https://docs.railway.com/pricing/plans), [Railway database responsibilities](https://docs.railway.com/databases), [Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [current Next.js guide](https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/), [vinext status](https://github.com/cloudflare/vinext), [OpenNext](https://opennext.js.org/cloudflare), [Render Free limits](https://render.com/docs/free), [Supabase backups](https://supabase.com/docs/guides/platform/backups), [Neon free limits](https://github.com/neondatabase/website/blob/main/content/faqs/free-plan-limits-and-quotas.md).

| Option | Timing and recommendation | Required check |
| --- | --- | --- |
| DNS/domain management | Optional during R1 domain setup; DNS-only for Vercel initially | Domain ownership/renewal/recovery, correct records and certificates |
| Proxy/CDN before Vercel | Do not enable by default; Vercel advises against this extra proxy | A demonstrated need and tested caching, traffic visibility, routing and rollback |
| API WAF/rate rules | Conditional protection for a custom Render API domain after application throttling | Direct-origin bypass, trusted client IP, CORS/cookies, real save/retry paths; verify plan limits/cost |
| Turnstile | Add if login abuse justifies it; proxying is not required | Server-side Siteverify, action/hostname, expiry/replay, provider outage behaviour and accessible staff flow |
| Access | Consider for staging or administrative tools, not a default second staff login | Validate Access JWT at the protected origin; do not trust an email header as authorization |
| Workers frontend qualification | Approved separate cost experiment; production migration remains gated | OpenNext/Linux and the full local workflow first; test real limits without customer data or purchases |

Do not cache login, authenticated API responses, receipts, Finance or exports publicly. Use explicit no-store/bypass rules and test two identities plus logout. Edge rules must not discard a pending idempotency key after a timeout or HTML error.

A public Render default domain can bypass custom-domain protection; disable or otherwise protect alternate origins only after custom-domain verification. Do not assume Cloudflare rules cover Vercel deployment URLs. Use verified origin certificates and Full (strict) when proxying is approved; rehearse DNS rollback. Keep backend authentication and rate controls.

Cloudflare cannot restore lost data, correct financial logic, prevent wrong garments being returned, or wake a sleeping origin instantly. DNS-only provides DNS management, not HTTP WAF/CDN protection.

References: [Vercel guidance](https://vercel.com/kb/guide/cloudflare-with-vercel), [DNS proxy status](https://developers.cloudflare.com/dns/proxy-status/), [Render Cloudflare setup](https://render.com/docs/configure-cloudflare-dns), [Full (strict) TLS](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/), [Turnstile validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/), [Access origin validation](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/).

## G1: customer memory and care instructions

- Optional current preference profile using only care/presentation options the team can actually honour. No unconfirmed fragrance, softener or skin/allergy promises.
- Show preferences when choosing a customer; snapshot agreed instructions on the order. Later profile edits do not rewrite old work.
- Separate permanent preference, order-only override, item instruction and attributed internal care note. Changes to a profile must be explicit, with permissions.
- Show saved instructions to the worker and at final checking. Clarify incompatible requests rather than silently accepting them.
- Reuse existing history. Exclude internal notes from receipts; retain only information useful to the service.
- Test no-profile customers, returning customers, overrides, permanent edits, item notes and unchanged historical orders.

## G2: offers and messages

- Owner-managed dated offers/bundles with clear quantities, exclusions, stacking with discretionary discounts and memberships, and an explicit Apply action.
- Snapshot eligibility/result/price on the order. Do not reprice old receipts when an offer changes.
- Reusable templates with checked ticket/customer/amount/ready-time fields; preview and manual copy/share first.
- Automatic email/SMS/WhatsApp only after a channel, consent/opt-out, recipient policy, delivery costs and failure handling are approved.
- Test expired/boundary/duplicate benefits, unsupported combinations, missing fields, wrong recipients and internal-note exclusion.

## G3: M-PESA automation and reconciliation

- Confirm merchant/PayBill arrangements and Daraja production access. Keep existing staff-confirmed cash/M-PESA records explicitly manual.
- Persist each payment attempt and distinguish requested, pending, paid, cancelled, failed and unknown. An accepted request or phone prompt is not proof of payment.
- Allow a different payer number without silently changing the customer profile; never collect a PIN.
- Verify callbacks according to the actual product contract, bind them to the right business/order/amount and reconcile exceptions. Do not invent a signature mechanism unsupported by the chosen API.
- Handle duplicate, late, missing and out-of-order results; use unique provider references and atomic ledger writes. Keep an accountable manual resolution path.
- Pass sandbox failure/replay tests, then separately approved live acceptance and reconciliation. Reference [Safaricom's official portal](https://developer.safaricom.co.ke/apis) during implementation.

## G4: laundry memberships, business customers and transport

This is Qinetra selling laundry services, distinct from M2 where laundries buy QLMS software.

- Cost washing, dry cleaning, capacity, pickup and return before pricing. Earlier package-price examples were ideas, not approved products.
- Owner sets price, kg, dry-cleaning units, duvet washes, trip allowance, service windows and priority rules. Business packages can have different terms.
- Keep independent benefit ledgers, reservations/consumption and reversals. Do not overwrite a remaining-balance number without history.
- Define consumption timing, correction/cancellation returns, overages and whether excess work may proceed.
- Pickup and return count as two trips. Coordinate external boda trips; do not build a driver fleet without a real need. An issued bag can be a one-time benefit, not a monthly renewal.
- Define expiry, renewal, rollover, pauses, overlapping offers and permitted notices. Show remaining allowances and warning thresholds.
- Test concurrent use, month boundaries, returns/reversals and double benefits; trial a small paid cohort before broad promotion.

## M1/M2: commercial platform

Before a second laundry joins a shared deployment, add businesses and explicit business memberships. Prefer shared tables with enforced business scope over duplicated schema sets per customer. For another type of business, establish the specific problem before offering full QLMS or a focused solution; do not build universal configuration in anticipation of unknown customers.

- Derive business scope from verified membership, not a browser-provided ID. Scope queries, writes, exports, jobs, callbacks, uniqueness and linked-record foreign keys.
- Rehearse migration of Qinetra into the first business record. Adversarially test guessed IDs and cross-business links with two businesses before onboarding others.
- Separate platform administrator, owner and employee permissions. Add a manager/report-only permission only when needed; financial viewing must not imply full owner power.
- Platform views show business status, service/subscription health and usage. No default browsing of named customer records. Support access requires owner approval, expiry and an audit.
- Onboarding service templates are editable per business. Platform template updates cannot overwrite live prices or saved order snapshots.
- Agree export/exit/retention/deletion rules before others entrust records.

Then add QLMS software plans and trials:
- Platform admin grants a first-month trial with exact start/end and a decided meaning of “month”; user/order/module allowances are still business decisions.
- Define plans, payment confirmation/invoices, renewals, reminders, grace, expiry and suspension. Keep software pricing apart from laundry prices and packages.
- Prevent duplicate trial resets and duplicate billing events. State what read/export/recovery access remains after expiry; never hold records hostage accidentally.
- Test trial-to-paid, renewal, expiry, reactivation, date boundaries and replay. First paying businesses must justify ongoing support and hosting costs.
- Optional Google sign-in remains A1 and can precede these commercial features.

## E1+: conditional future inventory

Keep these visible, but start only with a demonstrated need and a bounded design:
- Expense records, rewash/damage resolution and attributable costs; then defensible cost/margin reporting, not misleading “profit”.
- Business invoicing, approved credit limits, payment terms, recurring commercial collections and bad-debt handling.
- More detailed pickup/return scheduling, trip zones, capacity and transport coordination.
- Consumables/stock and equipment maintenance when omissions cause measurable cost or downtime.
- Period comparisons, deeper operational reporting and approved external integrations; protect access and data freshness.
- Audited duplicate-customer merge only if duplicates remain a practical problem after normalized intake/shared-number handling.
- Additional delegated permissions/invitations when the two roles are insufficient.
- Multiple branches, customer portal and full offline synchronization are separately scoped products, outside the current pilot; each adds its own privacy, custody and conflict model.

## L1+: guided Docker and AWS learning

Use [the Docker guide](docs/docker-learning-guide.md). Start with images/containers and disposable PostgreSQL, then a guided API Dockerfile, Compose, frontend packaging and repeatable tests. Plan any ECR/ECS/Fargate or other AWS sandbox with current documentation, cost limits, secret handling and teardown. No production migration is implied. Learning can proceed without disrupting the stable shop application.

## Retained pilot priorities and approved reporting/AI additions

This section incorporates the later business/reporting discussion without replacing the earlier inventory or claiming its implementation. Complete each small increment independently and release only compatible, verified changes. Qinetra's working pilot comes first; the retained A1/G1-G4/M1-M2/E1+/L1+ items above stay gated.

### Required before relying on QLMS daily

- Finish contact acceptance and this employee-discount increment, login/request protections, session/read recovery, CSV formula protection and private-response/header checks. Verify the full intake, custody, payment, refund, collection and daily-close loop; reuse valid evidence rather than repeating unrelated tests.
- Complete the separate real dataset, schema/runtime permissions, approved accounts/catalogue/opening records, independent encrypted daily backups and a timed restore. Keep the one-day reconstruction/four-working-hour recovery targets unproved until demonstrated. CSV is not a database backup.
- Qualify the frontend/backend release pair, HTTPS, readiness, alert delivery/recovery and rollback. Verify the actual frontend plan's commercial-use eligibility; if unsuitable, qualify Cloudflare/OpenNext on Linux with fictional data. Retain Render/Supabase unless a tested alternative gives a worthwhile advantage. No paid resources or framework rewrite by default.
- Start the ten trading-day receipt-backed trial after the concrete cutover review, with daily reconciliation and stop conditions. Complete compatible increments may then reach the pilot without waiting for every future feature.

### O1b: useful Excel/CSV reports after the baseline works

Bring forward only a report correctness/retrieval failure that prevents O1a daily closing. The approved first report is Daily control, available for daily/weekly/monthly date ranges from the existing Finance interface. Provide Summary, Money, Orders, Needs attention and Definitions worksheets; CSV sections use stable machine-readable headings and documented types.

- Summary and orders cover the chosen period; payments use received dates and real returns use return dates. Entry corrections restate receipts, rather than becoming new cash movements. Current attention lists include older unpaid/uncollected orders outside the chosen booking period and show their generation time. Do not invent historical debt from today's balance or label receipts/debt recovered as profit/new sales.
- Split cash/M-Pesa movement, identify unknown legacy refund methods and distinguish recorded money movement from physical cash-up. Owner review still reconciles receipts, counted cash and the M-Pesa statement; costs, floats and withdrawals are not silently inferred.
- Share one backend calculation/query layer across screen, XLSX and CSV, with a consistent snapshot, bounded queries/size and explicit oversized-export errors. Preserve phones/tickets as text, numeric KES values, filters, frozen headings and dated filenames. Escape formula-like untrusted CSV text; write XLSX text literally with formula/URL auto-conversion disabled. No browser database access or public caches.
- Proposed owner-only routes: GET /dashboard/reports/daily-control; GET /dashboard/reports/daily-control.xlsx; GET /dashboard/reports/daily-control/{section}.csv, with section orders/money/attention and shared start_date/end_date. Keep the existing export compatible. One pinned XLSX writer is justified when this increment starts; no new spreadsheet dependency is added by the discount increment.
- Downloads are review snapshots. Workbook edits do not update live records. Imports need a separately scoped validation, preview, permissions and audit workflow. Verify output in Excel and a free spreadsheet reader before promising usability.

### AI1: optional founder-reviewed business analysis

Use the existing/free chatbot allowance manually; the core application must work without it. First implement ordinary rules for debt, overdue clothing, missed promises and missing information. A model does not need to calculate these.

- Produce a separate approved analysis pack containing daily/period aggregates, service quantities with units, current queue/debt counts and data-quality limitations. Exclude customer/staff IDs, contacts, ticket references and free-text histories. Review sparse groups and identifying combinations; removing names alone does not establish anonymity. Do not send the ordinary owner workbook or a database dump to a chatbot.
- Preserve dependable dates, units, quantities, promises and attributed financial/custody events already recorded. New collection needs a defined decision and lawful purpose, not a speculative desire to collect everything. Add prospective aggregate snapshots when historical queue/debt trends are introduced; do not fabricate missing history. Cost/capacity definitions precede margin or membership recommendations.
- The weekly brief contains at most three actions, with source figures/period, observed facts versus hypotheses, effort/cost, responsible person and a review measure. The founder checks numbers and recommendations; the owner chooses actions. Record preparation time, corrections, chosen actions and observed outcomes to assess whether the service saves work.
- Before processing another client's data, agree purpose, provider, permitted exports/access, retention/deletion, controller/processor responsibilities and transfer safeguards. Owner approval does not waive customer privacy rights. Client opt-out must leave normal QLMS use available; no cross-client financial benchmarking or training use by default.
- Use research as evidence for an experiment, not a laundry ROI promise: [customer-support field study](https://arxiv.org/abs/2304.11771), [BCG decision/productivity study](https://www.hbs.edu/ris/Publication%20Files/dell-acqua-et-al-2026-navigating-the-jagged-technological-frontier_5c589c8c-fbb5-458f-b285-c944746cd717.pdf) and [retail field-experiment preprint](https://arxiv.org/abs/2510.12049). Forum stories inspire ideas but do not prove revenue or savings. Kenya's [ODPC principles](https://www.odpc.go.ke/rights-of-a-data-subject/) apply to personal-data handling.

### AI2: funded agents only after repeatable benefit

Begin with read-only, business-scoped report tools, explicit budgets/limits, provider/data review and audited access. Treat file contents as untrusted data, not instructions. Do not expose arbitrary SQL, secrets or unrestricted database credentials. Prices, refunds, collection records and sent messages remain human-approved actions with permission and idempotency checks. A paid chatbot plan is not an unlimited hosted API budget; verify product eligibility and billing separately. No chatbot UI scraping, borrowed accounts or silent paid fallback.

### V1: private evidence of value; B1: later sales presentation

The founder's value view needs a distinct server-side permission bound to the specifically approved Qinetra account; owner role alone is insufficient. Compare small, comparable timed intake/lookup/closing samples and errors/workarounds. Label extrapolated time or labour value; time released is not automatically cash saved. Separate recovered debt from new sales, and observe longer before claiming revenue/retention effects. Include onboarding/support effort in the service's economics.

Retain owner-editable catalogue names/prices now and owner-editable membership/offer names and rules when those modules are built. Laundry memberships and software subscriptions stay separate. Membership tiers need costs, capacity, allowances, renewal/pause/reversal/overage and trip rules; benefit-led names and optional demographic marketing ideas do not justify collecting sensitive profiling data.

Polish staff lookup/intake/closing for readability, keyboard use, mobile use and reduced motion before decorative work. Learn from existing laundry products' documented workflows, not copied feature lists or vendor revenue promises. A later separate public landing page can use authorized real photos and anonymized measured evidence; preserve staff app entry/direct order links and keep the private value API inaccessible publicly. Do not promise a universal solution before another business's problem is validated.

### Monitoring and efficient delivery choices retained

Qualify UptimeRobot for frontend/API readiness and backup heartbeats, with email as the initial alert preference pending a named recipient. Sentry is the initial error-tracking candidate after compatibility, quota and PII-scrubbing tests. Verify current free commercial-use terms at setup; do not purchase or repackage monitoring. Healthchecks.io is the backup-job alternative; later compare Better Stack or Grafana Cloud against measured support/retention needs and cost. A monitor on the shop laptop cannot be the sole external uptime check. Monitoring cannot fix free hosting sleep or provider allowances.

Use one active agent by default. GPT-6.1 Sol High suits monetary rules, permissions and concurrency; Medium suits routine implementation/testing and Low suits bounded documentation/copy/mechanical work. Raise effort for an unresolved risk, not by habit. Exact fixtures, ownership, acceptance criteria and relevant files belong in prompts; a fresh thread starts from the handoff/current Git state. Do not spawn overlapping writers or repeat a passed full suite without a relevant change or unresolved failure. No new instruction files, empty scaffolding or analytics framework solely for agents.

## Documentation without duplication

- This roadmap owns priorities, scope/status and gates. The [premortem](docs/pilot-premortem.md) owns risks, early signs, acceptance checks and stop/recovery conditions.
- The handover owns the next concrete task and unfinished work. The journal/check records own dated evidence; README should point to current documents rather than claim the whole backend is “complete”.
- [PRD.md](PRD.md) defines users/outcomes; [ARCHITECTURE.md](ARCHITECTURE.md) defines current components and boundaries with its essentials at the top. These concise documents exist; do not duplicate them in flow.md or another outline file.
- [DATA.md](DATA.md) records entity meanings, real/test separation and recovery requirements; D1/R1 must implement and prove them. [SECURITY.md](SECURITY.md) records controls and gaps; S1/S2 must implement the outstanding work. Written requirements are not evidence that controls already exist.
- Keep AGENTS.md as the instruction entry point and link the engineering guidelines. No duplicate flow.md rules or new scaffold solely for an AI workflow.
- For each verified increment update learning/presentation notes; capture a screenshot only for distinct meaningful behaviour with fictional data. Do not manufacture a screenshot for an invisible dependency version change.

## Decisions at the relevant gate

| Gate | User/owner decision |
| --- | --- |
| C2/C3 | Physical labels; valid item/pair corrections; normal collection attribution and any genuine partial-collection need. Discount authority is decided: owner-configured whole-order percentage, initially 0% |
| D1 | Actual owner/staff, catalog prices, opening clothes/debt/payments, treatment of legacy records and data retention |
| R1/P1 | Domain/support contact, backup destination/retention/key recovery and exact release window. Zero spending, daily backup/one-day reconstruction/four-working-hour recovery targets and ten receipt-backed trading days are decided |
| A1 | Who benefits from Google, account ownership on shared devices, linking and owner recovery |
| G1/G2 | Supported care choices, who edits preferences, offer stacking and message channel/consent |
| G3/G4 | Merchant access and exception owner; package costs/allowances/trips/overages/expiry |
| M1/M2 | Delegated permissions/support access, software prices/trial limits, expiry/export/exit rights |

Ask only decisions needed for the next increment; do not block unrelated approved work on all future answers. For each phase: inspect, explain the bounded files/data flow, resolve decisions, implement after approval, test, let the student do the important action, record evidence and stop before the next feature. Production change still requires the exact reviewed cutover.
