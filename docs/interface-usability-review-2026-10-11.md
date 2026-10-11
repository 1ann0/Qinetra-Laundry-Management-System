# Interface usability review — 11 October 2026

Purpose: let busy Qinetra staff find the right person or ticket, understand the next action, and recover safely on a phone. Use short familiar English, labelled controls, predictable navigation and help where a decision has consequences. “A ten-year-old can understand it” is a plain-language design target, not a usability result claimed without testing.

Method: Superpowers brainstorming/systematic debugging/verification and focused UI/UX Pro Max searches for mobile navigation, onboarding freedom and consistent help. Review the actual Next.js screens and shared components against the existing FastAPI contract. One active agent; no new library, stack or database changes. Private filled forms, sessions and customer records are excluded from agent observation.

## Screen inventory and findings

| Screen | Existing strengths | Finding / action |
| --- | --- | --- |
| Sign in and password reentry | Inline loading, bounded wait, visible labels; reentry protects drafts | Preserve the deployed feedback. A phone-width fixture is not a real child/employee comprehension test. |
| Shared navigation | Text labels, active route, Owner-only management links | Add consistent Find and Help, skip-to-content, and mobile Escape/keyboard focus handling. Check 320/375 px and landscape. |
| Home | Plain daily task shortcuts | Add a shared search for customers, tickets and services with direct links. Distinguish failed sections from no matches. |
| Add customer | Phone keyboard, duplicate/shared-phone warning, original-save recovery | Add optional help about identity and shared numbers. More field-specific focus improvements remain for a later form pass. |
| Customer search/history | Search by name/phone, service and period filters, receipt links | Add direct customer-history/search links from Find and relevant help. Honour reduced motion when opening history. The service dropdown still needs a searchable-choice pass. |
| Customer contact correction | Owner guard, explicit confirmation/reason, attributed history | Help explains keeping the same record and checking shared phones. Preserve confirmations and uncertain saves. |
| New order | Existing customer/service searches, damage/custody details, ready time, payment preview and review | Keep the staged form. Shorten help around the important decisions and retry safety. Long garment choices still need a careful searchable-choice pass preserving selected items. |
| Track orders | Search, stage/focus filters, contextual next action | Preserve filters. Accept the central search link and explain current attention versus stage. |
| Receipt | Customer/clothes, holds, outsourcing, payments, corrections and refunds | Add visible-section help for ticket details, holds and confirmed payments. Do not hide holds or custody warnings to make the page look simpler. Financial forms still need their own comprehension review. |
| Dashboard | Current workload, current debts, CSV download | Explain current figures and downloads. The approved attention-first dashboard and wider reports remain a later release. |
| Finance | Period receipts/refunds, current balances, explicit definitions | Help distinguishes work booked, cash received and current balances. Receipts are not profit. The wide customer table still needs a phone presentation pass. |
| Staff | Own logins, active/inactive status, reset and role restrictions | Add username/role search and larger relevant targets. Help does not reset or disable an account automatically. |
| Shop setup | Service history links already exist; old records retain prices | Add service/clothing search and direct section links. Existing edit/history/deactivate targets need at least 44 px height. Large add/edit forms still precede the lists; progressive disclosure is a follow-up, preserving unfinished edits. |
| Discount / backup preferences | Explicit Owner controls, revision-aware saves, warns automation is not configured | Keep authority and recovery controls. Help must not imply a saved preference sends alerts or starts backups. |

## First implementation pass

- Shared Find uses existing authenticated GET endpoints. No new search API or browser database access. Customers and orders show explicit six-row previews with links to all matches; services open the existing history view. Search is submitted deliberately, rather than requesting on every keystroke.
- Catalogue and Staff filters keep original IDs, inactive records and full source lists for editing and counts. They do not remove records or allocate payments.
- Optional help covers the 11 protected screen paths, uses 2–5 short steps, skips unavailable sections, supports Back/Done/Close/Escape, returns focus to Help and respects reduced motion. It performs no business action.
- The mobile menu contains keyboard focus while open, closes with Escape and returns focus to its trigger. Reauthentication protection remains in place.

## Pre-mortem

| Failure | Proof required |
| --- | --- |
| Search changes records or crosses permissions | Assert existing read endpoints; fake role walkthrough and management denial. |
| A search failure looks like no customers/debts | Partial-failure test and separate visible error for the affected group. |
| Results are truncated without explanation | Display match count / first six and working all-matches links. |
| A history link loses the chosen customer/service/query | Actual fictional browser navigation from Find and Shop setup. |
| Help points to hidden or forbidden controls | Visible-section tests and loading/Owner-denial checks. |
| Menus or help trap people or lose keyboard focus | Escape/Tab/Shift-Tab/close checks; reduced motion; short landscape viewport. |
| Phone controls overlap or page scrolls sideways | Inspect 320 and 375 px, menu open and help open, on fictional data. |
| “Simpler” hides safety decisions | Retain payment confirmation, damage, holds, custody, roles and pending-save reference tests. |

## Remaining work and evidence boundary

### Current checks and continuation

- Final 12 October package passes all 90 Linux tests, clean lint, 16-page production export and strict offline upload dry-run. All 73 allowlisted public source files match its build context. Release image is sha256:76f34de9421592cef64aeafdf66cf214c023978c0c0376f56ac82caad1566f31, compiled with the existing pilot HTTPS API. The earlier Windows child-process restriction and automatic-review usage failure no longer block this completed build; they remain historical evidence.
- Fictional browser proof: customer and service results open their correct saved history; a ticket all-matches link retains the query; Employee Find works while its menu excludes management. Catalogue shirt search shows two of 25 entries, including inactive; clothing 32 selects one of 32 names. No-match and clear restore expected counts. History/edit/state actions measure 44 px.
- At 320 px the menu moves focus to Close, wraps Tab/Shift-Tab, makes content inert and returns focus on Escape, without horizontal overflow. At 640 x 320 help stays within the viewport with its own scroll area and Back/Next/Escape/focus return work. These are browser sizing checks, not Android hardware proof. Screenshot 60 uses fictional data.
- Browser discovery: inline status spans left login/reentry submit buttons without accessible names. Explicit state-dependent labels now pass in the rebuilt fictional fixture: Sign in to QLMS/Signing in and Continue where I left off/Checking are named and disabled appropriately. A revoked fictional Owner session triggers reentry; the same-account password succeeds and closes the dialog. Screenshot 61 captures the empty-password reentry view; no real credentials were observed.
- Source review, reports and evidence are verified locally; commit/release identities belong in the current handoff. No hosted publication, real-data cutover, live identity linking or actual backup activation is claimed by these checks.
- Cleanup: temporary browser viewport reset/tab closed and the owned frontend Docker fixture stopped. The fictional API's terminal session is no longer available; its shutdown is unconfirmed. Do not remove private files or stop unrelated processes.

The user reports trying the existing workflow on different devices; do not request another full rehearsal just because the agent did not watch it. Exact role-denial, refund and failure-scenario outcomes were not individually reported. New interface changes still need their own focused checks and publication. Screenshots must use isolated fictional data only.

Do not claim a complete interface audit based only on static source, automated tests or a resized desktop browser. Actual Android readability, downloaded-file handling, keyboard behaviour and staff understanding need their respective evidence. Finish the core backup/recovery/alert release gates before the separate demo and later business features.
