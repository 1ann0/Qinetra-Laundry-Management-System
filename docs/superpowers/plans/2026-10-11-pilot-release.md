# Core Qinetra Pilot Implementation Plan

> For agentic workers: execute inline with Superpowers executing-plans. The user explicitly requested implementation of the reviewed plan; one active agent is the preserved execution method.

**Goal:** qualify the already-uploaded HTTPS frontend/API and complete private account/recovery prerequisites before real-data cutover.

12 October continuation: user-approved public backup disclosures/pages are implemented and locally verified. Image `65d380728a9d9d81130d730b99e73eae890928fa95244ebd651decc7c6d1900e` includes the search/help increment; 90 tests/lint/19-page export, strict offline upload dry-run, 60-file source comparison, 124-asset manifest and twelve anonymous route/phone-width checks pass. [Private upload guide](../../pilot-backup-pages-upload.md) replaces the usability-only candidate. Connected-plugin readback still serves `c622e581` at 100%. No upload, activation, schema change or actual Google publication occurred. Scope/domain/production-consent/runner grant and recovery/retention/alerts/schedule remain open.

**Architecture:** reuse the native static frontend, restricted FastAPI deployment, existing private bootstrap and backup tools. Humans alone load real credentials. Additional business features follow this release, using the approved design.

**Tech Stack:** Next.js 16.3.6, FastAPI, PostgreSQL 17, Cloudflare Workers Free, Render Free, Supabase, Python operations tools.

**Spec:** ../specs/2026-10-11-pilot-owner-controls-design.md

## Global constraints

- No real private file/credential/log reads or credential-loading execution by the agent.
- Catalogue-only pilot; original practice records untouched; no live fixture seeding.
- Preserve docs/save-rejection-check.md and original pending-save scopes.
- No spend, account reconnection, paid fallback or premature backup activation.

## Review focus

- Wrong runtime project/schema/administrator account must block private first-owner creation.
- A misleading 200 page must not pass without private headers and the expected API origin.
- Credential/driver failures must not print a private URL or entered password.
- Connected Drive plugin access is not an unattended grant; recovery/schedule proof remains required.
- Browser/cold-start/network failures must be distinguished from successful interactive acceptance.

## Task 1: activate the reviewed HTTPS version

- [x] Read public binding and previous deployment via Cloudflare plugin.
- [x] Deploy cc0b8f7c-bce5-48b2-a4d4-f57521e1e205 at 100%; record readback.
- [x] Verify public login/readiness headers and 200/ready.
- [x] Verify protected shells, anonymous denial, CORS and compiled API origin; retain public evidence.
- [ ] Complete signed-in/browser/device qualification without observing private credentials.

## Task 2: safe private first-owner handoff

Files: backend/ops/pilot_owner_setup.py; backend/tests/test_pilot_owner_setup.py; docs/pilot-owner-setup.md; operations/runbook/handoff notes.

Interfaces: validate_runtime(settings), load_settings(directory), check_database(engine), prepare_database(), run_bootstrap(), main(). The wrapper imports database/auth only after setting validated runtime values and disabling implicit dotenv loading; it calls the existing create_owner.main() rather than introducing a public bootstrap API.

- [x] RED: tests.test_pilot_owner_setup fails with missing module.
- [x] GREEN: seven new and ten existing tests pass with fictional settings; reject wrong project/role/schema/TLS/weak secret, unexpected actual role/privileges/operational records, noninteractive entry and secret-bearing exceptions.
- [x] Save private instructions and request only PASS/FAIL and password-free acceptance results.
- [x] Human creates the first Owner; metadata confirms one active Owner and no operational data.
- [ ] Human signs in privately and creates named Employee accounts.

## Task 3: operational recovery and schedule

- [ ] Verify remaining unattended OAuth/key/retention/alert prerequisites from source and existing evidence.
- [ ] Complete justified core tooling gaps with fictional tests before the private handoff.
- [ ] Human qualifies authenticated export/upload/readback/separate restore/key recovery and real archive size.
- [ ] Qualify 90-day retention against 5 GB and hosted execution with PC off; delivered failure/missed-run alerts.
- [ ] Activate only after those gates pass; no silent default-branch merge.

## Task 4: final handoff/cutover

- [ ] One fictional staff/device session: intake/garments/holds/outsource/payment/refund/collection/closing/role denial.
- [ ] Exact frontend/API/schema pairing and tested rollback; coordinated final address and original-service handling.
- [ ] Owner go-live review and ten receipt-backed trading days.
- [ ] Continue approved Android demo/dashboard/reports, money controls, memberships in order.

## Execution ledger

- 12 October Google Cloud milestone: human-only setup returned final PASS; after restart the MCP is available and authenticated. Expected business account/project scope explicitly selected; project ACTIVE readback passed. Enabled only Google Drive/Picker APIs and verified each as ENABLED. The user subsequently confirms Branding created. No billing activation, paid resource, secret read or backup activation. Scope selection/production consent/Desktop client/private backup grant remain pending human steps; never repeat completed installation/sign-in/API/Branding setup.
- 11 October continuation: user reports existing cross-device workflow trials; do not repeat the whole rehearsal. Key creation returned private PASS; both separate private recoverable copies are now human-confirmed. Company email is primary for operational alerts, GitHub secondary. No actual grant/export/restore/delivered alerts/retention/PC-off schedule qualification yet.
- Local recovery tools: drive_authorize.py implements human-only narrow folder consent with PKCE/state/loopback/private status, and init_backup_key secures the empty file before key creation. Nine new consent tests/two key tests and existing regressions pass 35 focused checks; no real private files were read or used by the agent.
- Local usability pass is committed as `e6c7ec9` (operations preparation `dd0b1c1`). The final named-button image `sha256:76f34de9421592cef64aeafdf66cf214c023978c0c0376f56ac82caad1566f31` passed all 90 tests, lint, 16-page export and strict offline upload dry-run; 73 public source files matched. Final fictional 375 px login/session-reentry, history/filter/menu/help checks and evidence 60/61 passed. Earlier usage-review and native child-process limits no longer block this exact package. It remains unpublished/unuploaded; deployed pair is unchanged.
- OAuth clarification/design approval: user meant Owner Google login, not backup consent. Written Owner-only design approved; dedicated implementation plan saved. No public signup/role selection, employee Google identity or mailbox sharing. No Google login/client/linking deployed.

- 11 October: initial HEAD e1656a6; only protected save-rejection WIP. Its SHA256 is 1F583B4373FA978C253B86D833F1FE37E33715D0FC645D000CBECFD6316E17A1.
- Cloudflare deployment a4937381-539a-4ccc-81ff-40f31f05bb39, 13:34:17 UTC, verified 100% of uploaded HTTPS version. Render remains live dep-db5d3gt9fdbs73celc90 / 9768670.
- Fresh public login 200/private headers/expected CSP/HSTS; API readiness 200/ready. These do not prove signed-in acceptance.
- Ruling: reuse the user-reviewed complete plan as the approved written design rather than request its approval again. Preserve inline execution and financial-subsystem review/checks.
- Ruling: use a private fixed-project bootstrap wrapper; create_owner.py otherwise imports implicit local .env, risking the practice destination. Reuse its validation and transaction lock.
- Browser attempts: in-app attach timed out; dedicated Chrome call timed out/reset. No filled credentials or token tab observed. Public shell checks continue through read-only HTTPS.
- Tests: initial RED was missing module; first GREEN attempt hit Windows sandbox temporary-directory permission errors. Isolated tests with a fixed workspace temporary directory outside the sandbox pass 17/17. No actual credential file or database connection used.
- All 27 hosted JS assets matched the HTTPS manifest, protected shells/private headers and anonymous/CORS checks passed. Full disposable PostgreSQL suite passed 238 tests; encrypted separate restore passed in 6.8 seconds. These are developer checks, not shop recovery acceptance.
- Storage projection/quota guard: 24 focused fictional tests pass; reserve 20% of the approved 5 GB, refuse oversized projection/unknown quota/insufficient headroom before upload. Cleanup and hosted activation remain open.
- User reported a sign-in timeout and requested inline button feedback plus the simple address. Same Worker renamed to `qlms`; public page/CORS pass. API timeout reproduced independently; same-candidate redeploy recovered readiness. Root cause and idle startup remain unqualified. Three new frontend regressions failed before the fix; 31 focused checks pass. New frontend publication is pending the verified build/private upload boundary.
- Complete public frontend package passes 84 tests/lint/static export/offline strict upload dry-run; 108 assets/27 JS files contain the expected HTTPS API and no fixture URL. Fictional phone-width progress/error review passes, screenshots 58/59. Private upload instructions target the same renamed Worker and existing token file; no token read or loaded by the agent.
- User completed upload privately; version c622e581-6d12-45a9-b0d6-c07d8bf4bd36 was reviewed/activated/read back in deployment 5ca27a41-144c-494d-90ea-f4823ea535b8 at 100%. All 27 hosted JS hashes match source f42f7d8; eight public shell/payload/redirect/private-header checks pass. One idle wake-up took 34.377 seconds, then warm readiness 1.508 seconds. Actual credential-private device acceptance remains open. Owner/storage/UI increments are committed separately; complete nine-commit unpublished range passed secret scanning.
