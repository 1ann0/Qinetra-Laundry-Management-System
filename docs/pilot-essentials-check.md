# Pilot essentials — 5 October 2026

Local implementation and provider setup evidence, not authorization for real-data entry. The roadmap owns scope and priorities. Finish the approved essentials as one batch, then run one final staff acceptance session before release.

## Implemented

| Control | Source / behavior |
|---|---|
| Login protection | `backend/login_throttle.py`, `models.py`, migration 023: database-backed five-minute windows shared across workers. Limits: 50 per peer IP, 30 per account, 10 per account/IP; attempts include successful and rejected logins. Keyed hashes replace raw identifiers; old buckets expire after 24 hours. Exhausted IPs cannot create additional account buckets. |
| Credential boundaries | `backend/auth.py`, `main.py`, `create_owner.py`: 72 UTF-8 byte bcrypt boundary without truncation, generic login failures, bounded login body, private terminal password entry and serialized first-owner creation. Production requires a strong signing secret. |
| Private responses and logs | `backend/response_security.py`, `main.py`: no-store API responses, safe validation errors and headers. Unhandled errors expose neither SQL parameters nor customer content. Stream failures rethrow a sanitized error. Release start command must also disable Uvicorn access logs, which otherwise include search query strings. |
| Spreadsheet protection | `backend/response_security.py`, CSV route in `main.py`: neutralize formula/control prefixes in untrusted text; numeric money stays numeric. |
| Browser protection | `frontend/next.config.mjs`: restricted CSP origins, framing/content-type/referrer/permissions headers and private responses. Inline hydration scripts remain permitted; HttpOnly cookies/nonces remain a separately reviewed increment. |
| Session recovery | `frontend/src/context/auth-context.js`, `components/layout/app-shell.js`, receipt page: first protected-page reads wait for a valid sign-in. Later locks keep the mounted draft. Receipt reads resume after password entry without resetting a payment draft. Late responses from another identity are discarded. |
| Same-account tab logout | `frontend/src/lib/logout-event.js`, auth context: BroadcastChannel sends only account/API scope, no token/password. Same-account tabs log out together; different accounts/API scopes are ignored. This is not global server-side logout or device-wide token revocation. Older browsers without BroadcastChannel require closing other signed-in tabs. |
| Database configuration/readiness | `backend/database.py`, `main.py`, `.env.example`: explicit schema/search path; production rejects local/plaintext/public-schema connections and a login mismatching the configured expected role. `/health/ready` checks connection, configured role/schema and required columns; failure is generic 503. Actual role privileges are verified separately by the operations rehearsal and provisioning checks. `/` stays liveness. |
| Recovery tools | `backend/ops/`, `requirements-ops.txt`: complete migration/schema rehearsal, authenticated AES-GCM exports, verified second copy, separate-target restore guards, private key generation and daily-task tooling. No automatic deletion. |

## Current evidence

- 198 backend tests passed with disposable PostgreSQL enabled and no skips. Full migration application, repeat application and empty schema restoration passed.
- The expanded operations rehearsal initially rejected a clothing correction. It then passed after allowing deletion of only mutable `order_items`/`order_item_exceptions` rows, preserving their snapshots. The final rehearsal took 4.5 seconds and covered contact correction, clothing history, collection, a KES 1,000 payment, a KES 200 refund/replay, encrypted export, separate-database restore, login hash and Finance: KES 800 retained/net charge, zero debt. This is a local fictional exercise, not proof of four-hour operational recovery.
- 75 frontend tests, lint and the production build passed after the final session/logout changes.
- Browser regression: an expired remembered session reopened receipt #7 after password entry without another refresh. Revoking the fictional employee session blocked a KES 250 payment; reauthentication retained the draft and original save notice without adding money. Explicit retry added exactly one payment, leaving KES 750 due. Fixture now has seven orders/four payments. Screenshot: `diagrams/evidence/54-session-recovery-preserved-payment.jpg`.
- Same-account two-tab logout passed in the production-built local frontend; employee logout left the different owner account signed in. A controlled 12-second password reply was interrupted by logout in the other employee tab; both returned to login and stayed there after the late reply arrived. The final context also ignores renewal failures belonging to a replaced token.
- Local response inspection confirmed CSP/no-store/framing/content-type headers on the receipt and no-store headers/200 on readiness. No console CSP errors were observed in the receipt recovery check. This does not verify deployed HTTPS/proxy headers.
- Current pip-audit found no reported vulnerabilities in the pinned backend/operations requirements. npm production audit found zero. The full npm audit reports five affected dependency entries from one unpatched braces advisory in the ESLint chain. Do not downgrade Next.js automatically or claim a clean full audit. Trusted local lint patterns do not provide a demonstrated public request path to this tool. Track [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm).
- Checksum-verified Gitleaks v8.30.1 scanned Git history: three findings in historical account-safety test code were reviewed as variable references, not embedded credentials. This does not prove that a previously exposed credential was rotated; do not reuse old credentials for the new pilot.
- Redacted staged scans passed for all three code increments, committed locally as `313791e` (security/readiness), `e8ab9ae` (schema/encrypted recovery) and `469af9f` (session recovery/logout). No push/deploy. The pre-existing `docs/save-rejection-check.md` draft remains outside these commits.

## Release checks — 5 October continuation

Added `.github/workflows/verify.yml` for standard Ubuntu PostgreSQL/recovery and frontend jobs, with pinned official Actions, read-only permissions and no live secrets, caches or uploaded artifacts. The repository connector confirms public visibility; standard runner time is free. actionlint v1.7.12, downloaded from its official release and checksum-verified, accepts the workflow. Fresh local execution passed 198 backend tests with no skips, 75 frontend tests, lint and a production build using the workflow's fictional API origin. Migration/reapplication/schema restore and restricted-role encrypted recovery passed; this run's recovery took 16.5 seconds. Restoring the local practice build's original API origin is a separate housekeeping step. No GitHub-hosted job has run yet; syntax/local checks do not establish Linux CI success.

Read-only Render inspection confirms automatic deployment on `main` commits, root `backend`, start command without `--no-access-log` and health path `/`. Coordinate these changes only with the qualified candidate: disable access logs, use `/health/ready`, and prevent deployment before checks/paired configuration are ready. The Vercel dashboard browser check failed to attach; plan eligibility remains unverified. No provider configuration, push, deployment, credentials or grant changed. [pilot-release-runbook.md](pilot-release-runbook.md) records release order and recovery; August code is not a safe rollback after new refund/correction records. `QINETRA_PILOT_START.md` now directs continuation to the current October records before its preserved historical setup.

## Separate pilot project

Created the free-plan `QLMS-Qinetra-Pilot` project in the approved organization: `istweeaqtykwfuhntgik`, Frankfurt. Applied the verified schema-only snapshot and server/backup access policies. All 20 tables have RLS; anon/authenticated schema usage is denied. Initially all catalogue/operational tables were empty. The subsequent owner-confirmed catalogue copy below added 22 services/30 garments; accounts/customers/orders/payments remain zero. Security advisor returned no findings; 16 informational missing-FK-index findings remain for measured query review. Unused indexes in a small database are not evidence to remove them.

`qlms_runtime` and `qlms_backup` are separate restricted NOLOGIN roles, without superuser/create-role/create-database/RLS-bypass privileges. Credentials, actual pooled connections and owner accounts are not configured. The runtime can change ordinary application records; immutable histories cannot be updated, and core records cannot be deleted. Backup access is read-only.

Automatic approval review rejected the follow-up `GRANT DELETE ON qlms.order_items, qlms.order_item_exceptions TO qlms_runtime`. The exact permission was tested locally, but **remains unapplied remotely pending explicit user approval**. Do not work around that rejection or enable real clothing corrections before resolving it.

### Owner-confirmed catalogue copy

The owner supplied https://qinetra-laundry-management-system.vercel.app/ and clarified that August prices/garments/setup are real/current; customers, orders and payments are practice records. The live sign-in page opens; its password/login was not tested. The old project's matching supplied owner account is active, but no password/hash was read or copied.

Source `owetwiekmoycshdijmtl` was INACTIVE and its read timed out. After confirming the free allowance (one active project; $0/month organization quote), restored the existing project and verified ACTIVE_HEALTHY. No upgrade or paid resource. Read its `public.services`/`public.clothing_item_types` and copied only those tables into the empty pilot in one guarded transaction. Preserved IDs, prices as decimal text, units, categories, recording modes, fixed garment links, turnaround times, active flags and creation timestamps; adjusted the two new sequences for subsequent catalogue edits. Invalid prices/missing links: zero. Independent source/target reads matched every copied field.

Source remains three accounts, 11 practice customers, 17 practice orders and 10 practice payments; record counts/catalogue were unchanged. Pilot has 22 services/30 garments, zero accounts/customers/orders/payments. There is no August discount-policy table; the pilot's employee ceiling stays at 0%. Subsequent permission check: 20 RLS tables, browser usage denied, both restricted roles still NOLOGIN, rejected clothing grant still unapplied. The ignored catalogue capture SHA-256 is `EB1583F0DDA19F851494809DFE2282B6C5B0363835945329E5EDCF15D5C2FD1E`; no business catalogue data or credentials were added to Git.

Creator requested technical/system administration rather than another shop Owner account. Current schema supports Owner/Employee only. Use private repository/provider dashboards for current operations; the roadmap retains a separate, bounded maintenance interface and platform permissions for later. No new admin role or maintenance console was implemented by this catalogue operation.

## Cloudflare qualification

An isolated Linux copy built with Next.js 16.3.6, OpenNext 1.20.7 and Wrangler 4.125.0. Dry-run upload: 1121.35 KiB gzip; only an ASSETS binding, no paid database/cache/image resource. The logo used unoptimized static delivery in this prototype. The runtime rejected the current-day compatibility date; pinning its supported 2026-08-27 date allowed local startup. Browser qualification then stalled; the local worker logged an approximately 85-second first login-page response. The test container was stopped and removed. No remote deployment, Cloudflare account/plan check, free CPU measurement or final release-pair qualification has passed. The prototype predates the latest logout changes and must not be described as the exact release candidate. Do not replace the framework or silently buy resources.

## Remaining cutover gates

1. Resolve the narrow remote permission approval; privately configure runtime/backup credentials and verify actual connections. Enter the first owner password in a private terminal, then approve/create staff accounts. The real catalogue is copied/verified; no re-entry is needed.
2. Confirm private cloud destination, closing time, retention/key recovery and alert recipient. Verify upload/readback from the cloud, schedule the tested job and demonstrate missed-run/failure alerts. A cloud-synchronized folder or success marker alone is not remote backup evidence.
3. Complete the remaining clothing/outsourcing/contact/daily-close staff scenarios in one final fictional-data acceptance session. Expired-session, pending-payment recovery and same-account/different-account logout have developer browser evidence; no quiz pause is required.
4. Qualify commercial frontend hosting, real HTTPS/CORS/trusted proxy behavior, readiness monitoring and alert delivery. Cloudflare has build evidence only; Vercel's actual plan is unverified.
5. Review accumulated commits, exact release pair and compatible rollback. A fresh pilot frontend origin avoids attaching old demonstration drafts/pending references to a new dataset. Reusing an existing origin/API/account-ID combination requires tested dataset isolation before cutover; do not discard an uncertain save as a shortcut. Never roll back to August code after entering new refund/correction records: old Finance ignores their meaning.

## Reproduce developer checks

```powershell
./backend/tests/run-postgres-tests.ps1 -PythonExecutable C:/Users/1ann0/qlms/tmp/test-venv/Scripts/python.exe
# -OperationsOnly repeats just schema, permissions and recovery rehearsal.
Set-Location frontend
node --test --test-reporter=dot tests/*.test.mjs
node node_modules/eslint/bin/eslint.js .
node node_modules/next/dist/bin/next build
```

The original backend virtual environment is broken; select a working interpreter with installed `backend/requirements-ops.txt`. The test runner accepts only disposable local databases, restores environment values and removes only its own container.

Final browser session uses the fictional `discount_owner` / `discount_employee` fixture, not real customer data. Verify expired-session direct links, same-account logout in two tabs, different-account isolation, owner contact correction and lookup, clothing/outsourcing/custody, payment/refund/CSV agreement and daily close. Existing detailed feature check records contain their fixtures; do not rebuild accepted features or add a quiz gate.
