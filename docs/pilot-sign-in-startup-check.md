# Phone sign-in and on-demand startup — deployed

Released at **23:11:49 Nairobi, 15 October 2026**, at [QLMS sign-in](https://qlms.qinetra.workers.dev/login).

## Release pair

- Frontend source **`875eeb146ae86562b4fdef5f309e9ffb580879a9`**, exact [CI 38798349381](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38798349381): Backend/recovery and Frontend tests/lint/build succeeded. Optional hosted smoke was not requested on that ordinary push.
- Production image **`sha256:9c61f85cd813a7d8e8caad6fcc633d5dc6f02f9708c3937e015332f681ea4683`**. Public runtime sources were compared byte-for-byte against the image before its asset manifest was produced. Fixture API URLs were rejected from production scripts.
- Cloudflare version **`176a1032-8573-4288-8a57-bd122c478a35`**, version 11, 1ms Worker startup; deployment **`f0e8d2cd-e7c6-47df-b0b1-87806554a40f`**, independently read back at 100%.
- Backend remains the expense release **`e6d9d2bb68ae8224e311c15e3a4232057bc7d6bb`**, service deployment **`dep-db881ass728c738hggvg`**. Schema remains **025**, 24 restricted application tables. No API release, migration, staff/customer/financial write or credential-file access was needed.
- Worker module etag is unchanged (`7fe25e4609a7bfdccd22633ad4107b07c26ab4fa29c974ec2d243158beedeea0`). Uploaded security-header text, routing, compatibility policy and only ASSETS/public API bindings were read back exactly before activation. The existing ephemeral encrypted asset-grant method uploaded 79 unique changed assets in three buckets (202/202/201); temporary grant/key references were cleared. No persistent account token was read or created.

## What changed

- `frontend/src/app/globals.css` compacts branding only at phone widths. The Qinetra logo, heading, clear labels and password toggle remain; desktop retains its two columns.
- `frontend/src/components/auth/login-form.js` starts a public readiness check when the signed-out form opens, while staff type. It shows connecting, possible waking after eight seconds, ready or unavailable text beside the form. Leaving aborts the check; it never blocks the existing credential submission.
- `frontend/src/lib/api.js` reuses the existing fetch/retry/deadline client. Login and public readiness have a two-minute allowance; ordinary record requests stay at 30 seconds. The readiness helper accepts only an explicit ready reply. A readiness check may use the existing maximum three read attempts; there is no periodic or all-day keep-alive.
- `frontend/src/components/layout/request-status.js` explains that slow reads may involve a waking server or a slow connection. Pending save wording/references, identity checks, single-attempt writes and manual retry remain unchanged.
- `frontend/tests/startup-readiness.test.mjs` covers a sixty-second startup, the two-minute stop, cancellation and invalid readiness replies. The short design/next-close business rule is in [the plan](superpowers/plans/2026-10-15-sign-in-startup.md).

An always-awake pilot plus practice service would risk the shared free-hour budget. This increment deliberately uses on-demand startup; it does not promise instant free-tier availability.

## Fresh verification

- Test-first: the new test file failed because the helper did not exist, then all four readiness checks passed after implementation.
- **111 frontend tests passed, zero failures/skips**, locally and inside the Linux production image; complete lint, static production build and strict offline Wrangler upload check passed. The first isolated build exposed a missing public workflow-YAML fixture, which was added to the build context; no application test was removed or weakened.
- Actual built fixture at **375×812**: Sign in moves from y=848 to **y=462**, button height 46px, text inputs and Show 51px. At **320×640**, button bottom is y=508 with no horizontal overflow. At live desktop width **1280**, two columns and 360px logo remain.
- Fictional delayed server: connecting → waking → ready was observed, with sign-in enabled. A fictional rejected login produced the existing understandable error and exactly one credential POST. An unavailable 503 readiness response used the bounded read retries, showed an unavailable message and left Sign in enabled. No real credentials or business records entered browser automation.
- [Public live smoke](diagrams/evidence/qlms-sign-in-startup-hosted-20261015.json), **23:13:53 Nairobi**: **135 asset hashes, 19 clean page routes, API readiness/contract and three anonymous denials passed**. [Approved manifest](diagrams/evidence/qlms-sign-in-startup-assets-20261015.json). Protected denial probes do not read record bodies.
- Actual released anonymous page at **375×812** shows ready feedback, no horizontal overflow and Sign in at y=462. Screenshot **76** is live; **74/75** are explicitly fictional local ready/waking evidence. Chrome control timed out once during final review; a fresh controlled tab recovered and the live review completed. This is phone-sized Chrome evidence, not a newly observed Android keyboard/login session.

## Rollback, remaining checks and skills

Restore Cloudflare version **`40566df2-8488-42ee-87a1-042fccf503ec`** to 100%; keep the backend and schema as they are. This removes only the startup/layout increment, without deleting records or pending-save storage. The prior version/deployment and its hashes were checked before replacement; production traffic was not deliberately rolled backwards for a drill.

Controlled live Render cold-start timing was not forced, and no new private Android sign-in was performed. The delayed fixture/deadline tests prove UI behavior while waiting, not a guarantee that Render always wakes within two minutes. Backup catch-ups remain a separate natural-trigger observation; see [backup checks](pilot-backup-catchup-check.md). Daily close has not been implemented.

Skills: Superpowers debugging tied the CSS change to measured live geometry; TDD and verification checked readiness validation, deadlines, cancellation and existing single-attempt writes. UI/UX Pro Max supplied task-first layout, readable waiting states, touch targets and responsive checks. Ponytail reused the existing form/API/CSS and kept new dependencies, authentication paths and polling out. Deep student review remains on the learning backlog.
