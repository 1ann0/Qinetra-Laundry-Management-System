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
Use test data for public examples. Check for names, phone numbers, passwords and tokens before sharing an older image.

| Evidence | Story it supports | Limits and next action |
| --- | --- | --- |
| [34 — Employee Home](docs/diagrams/evidence/34-employee-home-navigation.png) | Three daily tasks and a secondary Add customer action | User-supplied image inspected. No customer data visible. Menu is closed; it does not prove sidebar links or task completion. Keep it. |
| 35 — Stage filter selected (pending) | A control that previously looked like a label now shows a clear action and selected state | Capture one selected stage and its matching test order. This replaces the generic tracking capture brief. |
| 36 — Connection advice (optional, pending) | Technical errors translated into a staff action and support code | Capture one local simulated connection failure. Do not repeat it on every screen or describe it as a production outage. |

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
- Browser inspection confirmed the same fictional saved record. The screenshot tool could not place the capture in the repository; save one manual capture as `screenshot/40-clothing-record-receipt.png` rather than adding redundant images.
- Optional LinkedIn draft: "A receipt is only trustworthy when it matches the saved order. I replaced two separate QLMS message builders with one formatter that includes clothing counts and condition notes. Tests now cover mixed orders, pending checks and older records. The next check is the real staff workflow."
