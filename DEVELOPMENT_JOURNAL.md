# QLMS development journal

Start here for the development story, proof and short LinkedIn ideas. Drafts stay here until reviewed; nothing is posted automatically.

- Screenshots: [existing evidence folder](docs/diagrams/evidence/).
- Build priorities: [Qinetra pilot and commercial roadmap](IMPLEMENTATION_ROADMAP.md).
- Browser checks: [navigation guide](docs/navigation-usability-check.md).
- Support reference: [error codes and failure review](docs/support-codes.md).
- Study and demo detail: `LEARNING_NOTES.md` and `PRESENTATION_NOTES.md` in this checkout.

## Writing standard

Use a concrete problem as the hook. State two or three changes. End with a lesson or the next test.
Aim for 50–90 words. Keep only facts that help explain the improvement.

Apply [ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) principles: direct instructions, short sentences, consistent terms and clear actions.
Keep procedural sentences within 20 words. Treat laundry and product terms as defined terms, not interchangeable synonyms.
Use the official rules and dictionary for a formal language review. These drafts are not certified as fully STE-compliant.

Use plain first-person language for posts. Avoid claims such as “seamless”, “game-changing”, or “users love it” without evidence.
Do not invent time savings, customer reactions, uptime figures, revenue or deployment results.
The hook/change/conclusion structure is our editorial choice, separate from the STE specification.

## Evidence rule: one image, one useful point

Keep an existing image when it already proves the point. Do not create another screenshot just to complete a numbered checklist.
Add an image only for a distinct behaviour or a meaningful before-and-after comparison. Record what it proves and its limits.
Keep historical images in place; link to them instead of copying them into another folder.
Store genuine QLMS milestone evidence in `docs/diagrams/evidence/`. Use `screenshot/` only for edited public-post copies with documented provenance.
Use test data for public examples. Check for names, phone numbers, passwords and tokens before sharing an older image.

| Evidence | Story it supports | Limits and next action |
| --- | --- | --- |
| [34 — Employee Home](docs/diagrams/evidence/34-employee-home-navigation.png) | Three daily tasks and a secondary Add customer action | User-supplied image inspected. No customer data visible. Menu is closed; it does not prove sidebar links or task completion. Keep it. |
| 35 — Stage filter selected (pending) | A control that previously looked like a label now shows a clear action and selected state | Capture one selected stage and its matching test order. This replaces the generic tracking capture brief. |
| 36 — Connection advice (optional, pending) | Technical errors translated into a staff action and support code | Capture one local simulated connection failure. Do not repeat it on every screen or describe it as a production outage. |
| [40 — Clothing record receipt](docs/diagrams/evidence/40-clothing-record-receipt.png) | Saved tally and dry-cleaning condition details on one fictional order | Student-supplied local evidence inspected. It proves the saved screen record; student confirmation establishes that both unsent drafts matched. |

Older captures remain in the evidence folder. They document earlier designs and may contain personal data or outdated wording.
Review each selected image before a public post; the folder is not a ready-to-publish gallery.

## 9 September 2026 — Make daily work easy to find

**Problem:** Orders opened creation, Customers opened registration, and tracking had no sidebar entry.

**Changes:** Added Home, New order, Track orders and Customers as shared destinations. Kept the owner's Finance landing page.
Home now offers three main shortcuts and Add customer. Saved order details highlight Track orders.

**Proof:** Commit `094b654`. Lint, production build and isolated API access checks passed. Image 34 shows the new Home.
Uncoached user testing remains pending. This was a local change, not a deployment.

**Learning:** `/orders` opens creation. `/orders/1` opens the saved record with database ID 1, regardless of its date.

**LinkedIn draft:**

> A menu label can send someone to the wrong task.
>
> In QLMS, Orders opened a new order form. Customers opened registration. Tracking needed its own link.
>
> I separated New order from Track orders and made Customers open search. I also added three daily shortcuts to Home.
>
> The code checks passed. Next, I need someone unfamiliar with QLMS to try these tasks without help.

## 9 September 2026 — Make controls and errors understandable

**Problem:** The stage filters worked, but the user did not recognise them as interactive. Connection errors used developer terms.

**Changes:** Added bordered stage buttons, View orders, a selected-state label and View all orders.
Added plain error instructions, support codes and a 30-second request deadline. Saves are not automatically repeated.
Tracking now separates a load failure from an empty result. Corrected Staff text to describe the actual inactivity rule.

**Proof:** Local commit `01a2fa3`. Sixteen request/message tests, frontend lint and the production build passed. Hands-on review remains pending.
Read-only fixture checks also passed for both roles, owner reports, employee restrictions and wrong-password advice.
Images 35/36 remain pending. No claim of reduced support calls, faster staff work or prevented outages is supported yet.

**LinkedIn draft:**

> A button can work and still look like a label.
>
> That was the problem with the order stages in QLMS. I added visible borders, View orders and a clear selected state.
>
> I also replaced technical errors with a next action and a support code. If a save result is uncertain, staff must check the record before trying again.
>
> The next check is simple: can someone use this without an explanation?

## Add the next milestone here

- Date and problem: what happened, and who observed it?
- Changes: two or three concrete decisions.
- Proof: commit, completed checks and one existing or new image if useful.
- Limits: what is still local, untested or unproven?
- Post idea: hook, changes, conclusion; 50–90 words.
- Publication: draft / reviewed / posted, with the link only after publication.

## Implementation map for the feedback follow-up

All paths below are relative to the project root. Technical detail belongs here, not in the LinkedIn draft.

| Files | Purpose |
| --- | --- |
| `frontend/src/app/(protected)/orders/status/page.js` | Visible filter actions, selected labels, keyboard focus and a load-failure retry state |
| `frontend/src/lib/api.js`, `frontend/src/lib/user-messages.js` | Request deadline, safe error translation, support codes and uncertain-save guidance |
| `frontend/src/context/auth-context.js` | Plain sign-in and password re-entry messages; existing auth rules retained |
| `frontend/src/components/auth/auth-guard.js`, `login-form.js`, `session-reauth-dialog.js` | Plain access-check text and safe login feedback |
| `frontend/src/components/layout/page-tour.js` | Explain the visible stage actions and remove developer terms |
| `frontend/src/components/orders/service-item-entry.js` | Safe feedback when adding a clothing item |
| `frontend/src/app/(protected)/customers/page.js`, `customers/search/page.js` | Clear customer warnings, search feedback and safe failures |
| `frontend/src/app/(protected)/orders/page.js`, `orders/[orderId]/page.js` | Plain order instructions; avoid claiming an uncertain payment definitely failed |
| `frontend/src/app/(protected)/dashboard/page.js`, `finance/page.js` | Safe report and finance error messages |
| `frontend/src/app/(protected)/staff/page.js`, `settings/catalog/page.js` | Safe account/catalogue feedback and corrected inactivity explanation |
| `frontend/tests/api.test.mjs`, `frontend/package.json` | Sixteen focused tests; run `node --test tests/api.test.mjs` inside frontend |
| `docs/support-codes.md`, `docs/navigation-usability-check.md` | Support reference, failure review and exact student test steps |
| `DEVELOPMENT_JOURNAL.md` | Central story index and short post drafts |
| `docs/diagrams/evidence/34-employee-home-navigation.png` | Preserve the user's existing Home evidence |
| `LEARNING_NOTES.md`, `PRESENTATION_NOTES.md`, `docs/evidence-tracker.md` | Local study/demo notes and accurate evidence status; these stay out of Git |

Ignored helpers in `tmp/` support the local fixture server, read-only smoke checks and repeatable editing. They are not production features.

## 10 September 2026 — Recover a save without recording it twice

**Problem:** A save can reach the database even when its reply never reaches the employee.

**Local code:** `3275e35` on `codex/transaction-save-safety`. No push or deployment.

**Changes:** Keep the original save reference through refresh and retry. Save the order and initial payment together. Reject an old clothing edit and protect daily ticket numbering.

**Proof:** 32 frontend tests and 86 backend tests passed. The production build passed. Local browser failure tests recovered a KES 300 order with one KES 100 deposit, then one KES 200 final payment. [Recovery notice, image 37](docs/diagrams/evidence/37-local-save-recovery.png) and [payment history, image 38](docs/diagrams/evidence/38-local-recovered-payment-history.png) show distinct results using fictitious data.

**Limits:** Not deployed. Six PostgreSQL checks remain blocked by a Docker startup failure. Earlier navigation usability passed according to the student; no uncoached timing data was supplied. [Check plan, file map and pre-mortem](docs/transaction-safety-check.md).

**LinkedIn draft — review before posting:**

> Did the save fail, or did the reply get lost?
>
> I tested that problem in QLMS with sample laundry orders. Each save now keeps a reference so a retry can recover the same record. The order and its first payment also save together.
>
> In the browser test, refreshing and retrying left one deposit and one final payment. PostgreSQL concurrency checks are still pending. That is the next gate before release.

**Learning agreement:** Google OAuth remains a guided phase. Configure it together and explain consent, redirects, identity, role checks and recovery using the real implementation.

## 10 September 2026 — First working Docker database

- Docker client and engine both report 29.5.2. The test runner downloaded `postgres:17` and created a temporary local database container.
- Latest result: 91 tests passed, one migration-test session error, no skips. Five PostgreSQL concurrency tests passed. The remaining test reused a User object after closing its session; correction and rerun remain open.
- Cleanup verified: no `qlms-save-test-` container remained. The PostgreSQL image stayed available for reuse.
- [Docker learning guide](docs/docker-learning-guide.md): commands to run a container, inspect logs, query the database and stop it; later lessons cover the API Dockerfile, Compose and an AWS sandbox.
- This was an agent-run demonstration. The student's first manual exercise is pending. No Dockerfile, Compose file or AWS deployment was created.
- Next evidence: one student-captured view of their named lesson container and ready logs. Do not claim QLMS is containerized yet.

**Short post draft:**

> I started learning Docker with a database my project already uses.
>
> A PostgreSQL container gave QLMS a separate place to test simultaneous saves. Five concurrency checks passed. One migration test exposed a mistake in its test setup, so the full check is still open.
>
> The container was removed after the run; its image remains available. Next, I will practise running it myself before packaging the API.

## 11 September 2026 — All PostgreSQL checks pass

- Corrected the migration test by loading its user into the newly opened database session. The application code did not need to change.
- Full backend suite: 92 passed in 17.458 seconds; no skips. All PostgreSQL concurrency and migration cases passed.
- The student supplied their own Docker screenshot showing qlms-docker-lesson running postgres:17. The visible logs do not include the readiness line; do not claim more than the screenshot shows.
- Phase 2 still needs the student's workflow acceptance. Next proposed phase: add customers without leaving an unfinished order and handle likely duplicates before saving.
- No production migration, deployment, QLMS Dockerfile or AWS resource was created.

**Student Docker evidence:** [Posting copy 39](screenshot/39-docker-lesson-redacted.png) covers the Windows username. The original screenshot remains unchanged. [Editing notes](screenshot/README.md) distinguish the enlarged posting derivative from original terminal evidence. This confirms student practice running a container and inspecting logs; the cropped image does not show final database readiness.

**Short Docker post draft:**

> Today I practised creating a Docker container with PostgreSQL.
>
> I checked the running container with `docker ps` and read its logs. The distinction is clearer now: the image packages the software, and the container runs an instance of it.
>
> Next, I want to package the QLMS backend before learning to deploy it on AWS.

## 11 September 2026 — Student tests a missing save reply

- In the disposable local copy, the student saved a 3 kg order, saw the recovery notice, refreshed the same tab and recovered ticket 002. The receipt showed KES 450 total, one KES 100 deposit and KES 350 balance.
- The student then recorded the final KES 350 normally. Browser verification found two payment rows, zero balance and no extra order after retry. The student final-payment recovery scenario was skipped; stale clothing-edit acceptance remains open.
- The previous receipt stayed visible while another order was being prepared. This is a recorded usability concern, not a change made during testing.
- No redundant screenshot was added. Existing recovery images 37 and 38 show the same types of state; this entry records the separate student session. No live shop record changed.

## 11 September 2026 — Clothing accountability takes priority

- The student could not see the clothing tally in the test copy. Source review found the feature intact: the simplified fixture had set Wash & Fold to No clothing list and contained no garment catalogue.
- Existing detailed garment records include descriptions, damage and stain notes, and the on-screen receipt displays them. Both WhatsApp receipt drafts omit those details. Laundry tally condition capture, permanent garment tags and outsourced handover records remain gaps.
- The 25 existing detailed-order tests passed against disposable data. No application or live catalogue change was made during this audit.
- [Audit, phased implementation plan and pre-mortem](docs/clothing-intake-review.md). Clothing intake and receipt completeness now precede the customer shortcut. The student confirmed outsourced garments are currently identified by descriptions without numbered tags; permanent physical references remain a proposal.
- No screenshot of missing or unbuilt functionality was added. Capture a representative clothing record and matching receipt when the approved phase is implemented and verified.

## 11 September 2026 — Prepare clean Qinetra business tables

- Created nine empty tables in a private qinetra_live schema in the existing Supabase project. Verified RLS on all nine, no anonymous/signed-in Data API access and no foreign keys into the old data. Existing customer, order and payment counts stayed unchanged.
- Found existing public tables with RLS disabled and anonymous read/write privileges. This remains a launch blocker. The app has not been connected to the new schema; owner accounts and the confirmed catalogue are not configured there.
- [Pilot start record and remaining priorities](QINETRA_PILOT_START.md). The approved clothing/receipt change remains pending. No claim of production readiness or live customer onboarding.
- Future requirements confirmed: Caroline's accounts remain a separate demo; new businesses receive their own authorised memberships/data access; owners can delegate explicit employee permissions. Google sign-in does not itself choose a database or confer ownership. These are recorded requirements, not implemented features.

## 11 September 2026 — Close direct database access

- Enabled row security and removed public browser-role grants from the eight older application tables and their sequences. Preserved backend access and all record counts. Migration: 20260911122502_restrict_legacy_qlms_data_api_access.
- Each of eight zero-row requests using the public API key was denied. Supabase reports no remaining security ERROR/WARN findings. The deployed login lookup still returns the expected response for a nonexistent user; successful owner login and receipt reading await the student's check.
- No application rewrite, deployment or new screenshot was needed. [Small-change maintenance standard](docs/engineering-guidelines.md) records the user's code-quality requirement.
- Student subsequently replied "works" after checking the deployed owner login, Track orders and an existing receipt. The security change's manual check is complete; this does not confirm fresh-schema setup or cutover.

## 15 September 2026 — Put garment accountability before expansion

- Reviewed the customer-experience ideas against the source, live backend version and fresh-schema counts. Confirmed about 10 daily orders, checks before washing and a shared work screen; simple outsourced garment references were accepted.
- Consolidated delivery order and completion checks in [the roadmap](IMPLEMENTATION_ROADMAP.md), including the exact next 3A1 receipt change. Updated the pilot checklist and clothing review to match current decisions.
- Added owner action lists, clear reporting scopes and refresh behaviour to pilot requirements. Customer memory follows the core pilot; platform administration precedes a second business.
- Documentation only. No code, database, deployment, new test result or screenshot. Previous tests and manual acceptance remain separately recorded.
- Optional LinkedIn draft: "What happens when two similar shirts leave the shop? That question helped me prioritise QLMS. I reviewed garment records, receipts and handovers, then planned small changes with a check for each one. The next step is to make the customer receipt match the saved clothing record."

## 15 September 2026 — Build customer drafts from saved clothing records

- Added one shared receipt formatter used after order creation and from saved order details. It includes saved clothing counts, descriptions, existing damage, stain notes and pending checks while preserving older orders without invented information.
- Updated the disposable local catalogue to demonstrate Quick tally and individual Dry Cleaning details. No application database, backend API, live data or deployment changed.
- Verification: five focused receipt cases and all 37 frontend tests passed; lint, production build, fixture syntax and local catalogue checks passed. The first sandboxed build could not download the configured Google font; the permitted network rerun passed.
- Student mixed-order browser acceptance passed. Both drafts matched ticket QL-20260915-001: two shirts, one trouser and a described dry-cleaning shirt with saved tear/stain notes. The student explained that one formatter prevents inconsistent information and standardises confirmation. No WhatsApp message was sent.
- Browser inspection confirmed the same fictional saved record. [Evidence 40](docs/diagrams/evidence/40-clothing-record-receipt.png) was supplied by the student and inspected; it contains no password, token or real customer record.
- Optional LinkedIn draft: "A receipt is only trustworthy when it matches the saved order. I replaced two separate QLMS message builders with one formatter that includes clothing counts and condition notes. Tests now cover mixed orders, pending checks and older records. The next check is the real staff workflow."

## 15 September 2026 — Protect the pre-wash clothing check

- A quick tally can now attach a separate damage or serious-stain note to an affected piece. The note does not add another item or change the service price.
- New clothing checks record the employee and time. Later changes require a reason and retain immutable versions; the first correction to an older order also preserves the record that existed before history was added.
- The API now blocks Received → In Progress while any required clothing check is pending. Staff get the direct instruction to complete the check before washing starts.
- Added migration `011_add_item_condition_history.sql`. It creates indexed exception/history tables, protects them with row-level security and denies browser database roles.
- Verification: 29 focused clothing tests, 96 full backend tests, 37 frontend tests, lint, Python syntax and the production build passed. The production build needed network access only to fetch the configured Geist font.
- PostgreSQL verification completed after Docker Desktop was started: the disposable PostgreSQL 17 run passed all 102 current backend tests with no skips, including repeated migrations and concurrency cases. Browser acceptance and the next genuine evidence image remain pending.
- Next useful evidence: one fictional saved tally showing a counted item with a condition note, the employee/time, and two visible history versions after a reasoned correction. Save it only under `docs/diagrams/evidence/`.

## 15 September 2026 — Add a customer-reply hold

- Staff can pause a Received or In Progress order when a clothing decision needs the customer. The reason, employee and time stay on the order.
- Track orders removes the forward-stage action and links staff to Record customer reply. Closing the hold requires a note explaining what the customer confirmed; closed holds remain readable in the order history.
- Added migration `012_add_customer_reply_holds.sql` with indexed ownership fields, one active hold per order, row-level security and no browser-role grants.
- Verification: 30 focused clothing/hold tests, 37 frontend tests, lint and the production build passed. The later disposable PostgreSQL 17 run passed all 102 current backend tests with no skips, including repeated migrations 010–012 and concurrency cases.
- No live database, deployment, external message or evidence screenshot changed.

## 15 September 2026 — Keep customer intake in one workflow

- Replaced separate registration logic with one customer form shared by Add customer and New order. The inline path selects the saved or matched customer without clearing services, clothing details or payment choices.
- Added one normalised Kenyan mobile column and migration 013. Staff still see the familiar local number. Likely duplicates are shown before saving, and shared family numbers require an explicit separate-record choice.
- Added staff-scoped unfinished-order drafts and a leave-page warning. After a confirmed save, the receipt replaces the form and Start next order opens a clean entry screen.
- Verification: 8 focused phone tests; 105 SQLite tests with 6 expected skips; 105 PostgreSQL 17 tests with no skips; 44 frontend tests; full lint and production build passed. Nothing was deployed and no live database changed.
- A disposable browser smoke test passed exact matching, the explicit shared-number choice, draft restoration and the receipt handoff. It exposed a three-hour promised-time display error; the shared Nairobi formatter fixed New order, tracking, order details and receipt messages.
- Evidence: none added. The later browser review may justify one fictional image that shows the inline match choice while entered order details remain visible; save it only in `docs/diagrams/evidence/`.
- Optional LinkedIn draft: "Customer registration should not make a busy employee restart an order. I moved it into the QLMS order flow, added consistent Kenyan phone matching and protected unfinished work through refresh. The result is fewer repeated entries and a clearer handoff from form to receipt."

## 16 September 2026 — Separate price from physical garment identity

- Detailed dry-cleaning services now keep a charged quantity and a separate physical-piece list. This prevents a jacket and trousers from charging as two suits.
- Every physical garment receives a permanent ticket reference. Editing keeps existing references, replacements receive a new suffix and old suffixes are not reused. Detailed garment descriptions are required.
- The same reference appears on the saved receipt and WhatsApp draft. Internal cleaner information is not present because the handover register is the next unit.
- Verification: 32 focused and 107 full SQLite backend tests passed; the full run skipped six PostgreSQL-only cases. All 45 frontend tests, lint and the production build passed. Removed the Google-font download so builds work without external font access.
- PostgreSQL migration 014 verification remains pending because Docker Desktop's Windows service could not be started by this session. No live database, deployment or external message changed.
- Evidence: none added. Preserve the screenshot budget for a fictional partial return that leaves one garment visibly outstanding.

## 17 September 2026 — Reconcile outside dry cleaning

- Added one handover per detailed service with cleaner, expected return, sender and timestamp. Every referenced physical piece gets an independent return check.
- A partial return stays visible. Staff record any return issue; only the owner can close it with a reason while the original note remains. Ready is blocked until all sent pieces are returned and issues resolved.
- New dry-cleaning orders cannot skip the handling step: QLMS requires the outside handover or the owner's attributed in-shop explanation. Clothing edits lock after either choice.
- Verification: 36 focused and 111 full SQLite backend tests passed (six PostgreSQL-only cases skipped); 45 frontend tests, lint and production build passed. Disposable PostgreSQL migration 014–015 and locking checks, browser acceptance and the actual physical reference method remain open. No live deployment or data change.
- No new screenshot was added. The next distinct evidence should show one returned garment and one still outstanding on a fictional order under `docs/diagrams/evidence/`.
- Optional LinkedIn draft: "Two garments can leave the shop together and return on different days. I added a QLMS handover record that tracks each piece separately. A partial return now stays open, and a problem on return needs an owner-recorded outcome before the order can be marked ready. The next check is whether staff can use it quickly during a normal shift."

## 17 September 2026 — Start owner payment corrections

- Qinetra pilot decision: only the owner may correct saved payments. A recorded entry mistake and an actual refund use different linked events; both preserve the original payment and require a reason and explicit confirmation.
- The owner form shows the payment and its remaining correctable amount. An idempotency key protects against duplicate refunds after a lost network reply. Collected orders require a separate status correction first.
- Corrected receipts use the payment's original date; actual refunds use the day money went back to the customer. Finance separates payments received, refunds sent and cash after refunds. The CSV includes correction and refund totals.
- Five focused correction tests and 116 full SQLite backend tests passed (six PostgreSQL-only tests skipped); the updated receipt test and production build passed. Docker's Linux engine was not available, so migration 016 and concurrency checks remain unverified. No live database or deployment changed.
- Evidence: none added. After a fictional browser review, capture one clear owner correction-history screen under `docs/diagrams/evidence/`; avoid a second similar payment screenshot.
- Optional LinkedIn draft: "A payment mistake should not erase the original record. I added an owner correction that links back to the payment, and a separate refund record for money actually returned. The daily figures now show the difference. My next check is whether the owner can use the flow quickly during a normal shift."

## 17 September 2026 — Keep cancelled tickets and stage mistakes accountable

- Added an owner-only one-step stage correction. The saved event records before/after state, timestamps, reason, actor and any physical-item confirmation. Ordinary staff status updates still move forward one step.
- Added a narrow cancellation path for unpaid Received orders before work starts. The owner confirms all items were returned; active holds and dry-cleaner/in-shop handling block this cancellation path.
- Cancelled tickets remain searchable. Active work, outstanding debt and booked-value totals exclude them. Finance counts cancelled tickets for the selected booking period, and the CSV separates original price from effective value.
- Five focused stage/cancellation tests and the full 121-test SQLite suite passed, with six PostgreSQL-only checks skipped. All 47 frontend tests, lint and the final production build passed. Migrations 016–017 and browser acceptance remain open because Docker's Linux engine is unavailable. No live data or deployment changed.
- Evidence: none added. A fictional correction-history screen is useful only if it explains a distinct safeguard; save it in `docs/diagrams/evidence/` after browser verification.

## 17 September 2026 — Correct billed kg with the saved rate

- Added an owner-only correction for Wash & Fold kg. The calculation uses the unit rate saved on the ticket, adjusts only the selected line in a mixed order and requires the owner to confirm the new fixed discount and reason.
- QLMS blocks a new total below recorded money, rejects stale quantities and recognises retry requests. Original and corrected quantities, discount and order total stay in the order's history and CSV.
- This intentionally does not change clothing counts or dry-cleaning item quantities. Those physical records need their own consistent correction path.
- Five focused quantity cases and the full 126-test SQLite backend run passed (six PostgreSQL-only skips). All 47 frontend tests, lint and the production build passed. Migration 018 and browser acceptance remain open. No live data or deployment changed.
- Optional LinkedIn draft: "A catalogue price can change after a customer leaves an order. I added a QLMS weight correction that uses the rate saved on that ticket, updates only the affected service and keeps the old figures in history. The next check is a real owner workflow on a fictional mixed order."

## 17 September 2026 — Correct a ticket linked to the wrong customer

- Added an owner-only reassignment to an existing customer. The ticket, service lines and payment events remain unchanged; before/after customer IDs and names, actor and reason are retained in history and CSV.
- Search and customer payment attribution now follow the ticket's corrected customer. The owner UI includes a reminder that a receipt already sent to the wrong person requires a real follow-up.
- Two focused reassignment tests and all 128 SQLite backend tests passed (six PostgreSQL-only skips). The frontend's 47 tests, lint and production build passed. Migration 019 and browser acceptance remain open. No live data or deployment changed.
- Optional LinkedIn draft: "I found that fixing a wrong customer name is different from fixing a ticket assigned to the wrong person. QLMS now moves only that ticket, keeps the original link in history and updates the correct customer's order view. It cannot undo a receipt already sent to the wrong phone, so the owner gets a clear follow-up reminder."

## 22 September 2026 — Verify rejected-save recovery in the browser

- The API explicitly distinguishes a known rejection from an uncertain result. Only recognized not-saved responses clear the pending attempt; missing replies and conflicting reuse keep the original reference.
- Local two-tab review passed on fictional ticket `QL-NAV-TEST-001`: 2 to 3 kg saved, the older 2 to 4 kg request was rejected without an event, then reload and 3 to 4 kg saved. A lost reply to 4 to 5 kg survived refresh/retry with exactly three accepted events overall.
- All 50 frontend tests and five working-tree signed-token HTTP cases passed again. The isolated commit candidate passed all 134 backend tests against disposable PostgreSQL in 27.795 seconds, with no skips or short-key warning; the runner removed its test container. The earlier 135-test log includes the unfinished contact draft. Local commit subject: `Recover rejected saves without losing uncertain requests`; contact-specific code/migration/tests remain unstaged.
- Evidence: `docs/diagrams/evidence/41-local-stale-save-rejected.png`, inspected for readable feedback and fictional data. Exact steps and file/commit boundaries are in `docs/save-rejection-check.md`. Initial receipt-load errors recovered on reload; their cause and the password-reentry load behavior need follow-up during staff rehearsal.
- Student hands-on acceptance and deep learning review remain pending. No production changes. Truthful refunds remain next; customer-contact editing is still an unfinished separate draft.

## 25 September 2026 — Student confirms the stale-save flow

- The student replied "it works" after the two-tab instructions and the request to confirm rejection, reload and resubmission. Mark that sequence as student-reported acceptance.
- Exact kg values, audit counts and a new screenshot were not supplied; existing image 41 remains developer evidence. The student's lost-reply/refresh/retry check and explain-back are next. No application code or production change.
- Subsequent lost-reply acceptance: the student confirmed refreshing the same tab, finding Retry previous save still present and clicking it. Read-only browser inspection verified exactly one 4 to 5 kg "lost reply test" correction, KES 750 and no remaining retry notice; three correction events in total. The one-use fault flag was consumed. Both functional scenarios now pass; explain-back remains pending. No new screenshot or deployment.

## 28 September 2026 — Local dependency patch and approved pilot plan

- Next.js/eslint-config-next are 16.3.6 with compatible lockfile fixes. The 26 September checks passed: 50 frontend tests, lint, build and zero npm audit findings. Exact scope and limitations are in `docs/security-patch-check.md`.
- Browser checks passed owner Finance/receipt, employee route protection and phone lookup. The old shared-connection SQLite fixture showed intermittent receipt-load failures. A fresh temporary-file fixture passed employee receipt first load and one fictional KES 100 payment on KES 300 work; refresh retained one payment and KES 200 balance. Broader interrupted-session review remains open.
- Preserved the old fictional receipt locally before restarting its disposable API. No real data, deployment or purchase changed. The backend contact-correction draft remains separate.
- Roadmap/premortem now record zero spending, separate free-allowance real-data project, whole-order employee discount ceiling initially 0%, recovery targets and ten receipt-backed trading days. Added PRD, architecture/essentials, data and security documents; README/handover link their distinct responsibilities.
- No redundant screenshot for an invisible dependency change. Developer verification is not student hands-on acceptance or production readiness. Truthful refunds remain the next approved product increment.

## 28 September 2026 — Truthful refunds verified locally

- Added owner-only explicit service/excess refund purposes, derived net charge/refund due and migration 021. Original payments, accepted save references and collection status remain intact; older refund purposes are not guessed. Corrected balances after collection can be settled by the owner without reopening clothing custody.
- Receipt, customer history, status work lists, Finance and CSV now distinguish billed work, service refunds, retained money and refunds still due. The refund form keeps its own recovery reference across refresh; earlier accepted adjustment requests still replay.
- Verification: 146 working-tree backend tests, 145 exact staged-backend tests without the separate contact draft, all including disposable PostgreSQL and no skips; 52 frontend tests, lint and production build passed. Concurrency, repeatable migrations, permissions, tampered fields and old replay are covered.
- Browser: a deliberately lost KES 200 refund reply recovered exactly once after refresh/retry; KES 1,000 became KES 800 charged/retained with no debt, still Collected. Correcting a second paid KES 300 ticket to KES 150 showed money owed back; its excess return kept charge KES 150. Finance and authenticated CSV matched KES 1,300 receipts, KES 350 returned and KES 950 retained. Employee saw history without owner controls.
- Local screenshots 42/43 and exact fresh/current-fixture steps are documented in docs/refund-check.md and the evidence tracker. Student actions/explain-back are pending. No production changes, real refunds, purchases or real customer entry. Contact-correction draft remains separate; launch gates still apply.

## 29 September 2026 — Student refund check requires a repeat

- Student reported completion. Read-only browser inspection found a KES 100 Entry mistake with reason "further refund test" on QL-REFUND-TEST-001, not a service refund. Net charge KES 800, retained KES 700, debt KES 100, existing service refund KES 200; Collected stayed unchanged.
- The saved figures match that operation, but the intended refund acceptance is not passed. Preserve audit history and repeat on a fresh fictional receipt. Record the ambiguous operation selection as a usability finding before shop use. No extra money event or deployment was performed.

### Refund form follow-up

- Removed default action/purpose, added outcome preview and action-specific confirmation, and reset confirmation on detail changes. Only frontend behavior changed; 52 frontend tests, lint/build and focused browser checks passed, including lost-reply refresh/retry with one refund. Details and student receipt 4 steps: `docs/refund-check.md`. Screenshot 44 records the preview. The contact draft is preserved; no deployment or real money movement.
- User requested less process overhead: prioritise daily-work value and launch blockers, reuse valid evidence and keep updates concise. Expired-session receipt refresh remains a separate launch check.
- Student refund repeat passed: receipt 4's one KES 60 service refund and KES 240 charge/retained, zero debt/refund due and Collected status were verified after refresh. Detailed acceptance is in `docs/refund-check.md`; no further save or deployment was performed.

## 29 September 2026 — Customer contact correction

- Completed the existing draft with an owner contact editor/history, name-only shared-phone handling, synchronized phone checks and input-tampering rejection. Customer IDs, order links and money remain unchanged. Contract/file inventory and evidence: `docs/customer-contact-check.md`.
- 156 backend tests passed including disposable PostgreSQL concurrency/migration checks; 52 frontend tests, lint and production build passed. Browser shared-number review, lost-reply refresh/retry, name-only change, lookup and existing receipt passed. Screenshot 45 records fictional audit history. Student customer #3 is ready; acceptance/deep review pending. No production migration, deployment or real customer data used.
