# Qinetra release procedure

This is the first real-data cutover procedure, not a deployment record. Use [pilot-essentials-check.md](pilot-essentials-check.md) for verified setup and open gates. Keep the August demonstration database and its practice records intact.

## Before publishing

1. Clothing permission was approved/applied on 8 October. Finish restricted runtime/backup logins and privately entered first-owner password. Verify actual TLS connections, selected `qlms` schema and browser denial. The copied 22 services/30 garments are verified; do not import practice accounts or transactions.
2. Qualify independent encrypted backup upload/readback, restoration, key recovery, daily schedule and delivered failure/missed-run alerts. Agree the closing time and alert recipient. Local restore timing alone does not qualify the shop's recovery target.
3. Finish one fictional-data staff acceptance session covering customer lookup/contact correction, intake/garment references, holds, outsourcing, payment/refund, collection and daily close. Match receipts, Finance and CSV to hand-calculated figures.
4. Qualify the actual commercial frontend plan, HTTPS, CORS, trusted proxy/IP behavior and readiness monitoring. Use a fresh pilot frontend origin so old demonstration drafts cannot attach to matching account IDs in the new database. An existing origin requires tested dataset isolation instead; do not clear an uncertain save to bypass it.
5. Choose a full Git commit SHA for both frontend/backend. Check its schema/migration manifest and secret/dependency review. Record the intended project, API/frontend origins and provider deployment IDs privately, without credentials. Use the same candidate throughout; any code change needs the relevant checks again.

## Automatic checks

`.github/workflows/verify.yml` checks pushes to `main`/`codex/**`, pull requests into `main`, and manual runs. Two standard Ubuntu jobs use Python 3.12 and Node 24. The backend runner creates its own PostgreSQL 17 container, runs the backend suite, reapplies migrations, restores the schema and rehearses encrypted record recovery with restricted roles. The frontend job installs the lockfile, tests, lints and builds using a fictional API origin.

Actions are pinned to verified official commit IDs, checkout does not retain credentials, and the workflow has read-only permissions. It uploads no artifacts, uses no package cache, and has no live database/deployment secrets. Obsolete checks on the same ref are cancelled. Standard runners on this public repository are free under [GitHub's billing rules](https://docs.github.com/en/billing/concepts/product-billing/github-actions); reconsider the allowance before changing repository visibility or runner type.

A local command or workflow syntax check is not a passed GitHub run. Before releasing, require both jobs to pass for the exact candidate SHA. The workflow does not enforce branch protection or stop provider deployment. Configure required checks in GitHub after the first successful run and qualify that rule separately.

## Publish the qualified pair

1. Keep real entry closed and take a verified pre-release encrypted export. Pause provider automatic deployment during coordinated configuration; record existing settings privately. Do not accidentally update the demonstration service's database while it still runs August code.
2. Configure the candidate API's private runtime connection, `QLMS_ENV=production`, `QLMS_DB_SCHEMA=qlms`, `QLMS_DB_USER=qlms_runtime`, fresh signing secret and exact HTTPS `ALLOWED_ORIGINS`. Privileged migration and read-only backup connections stay out of the running API. Do not display credentials in logs, tickets or screenshots.
3. The API start command must be `uvicorn main:app --host 0.0.0.0 --port $PORT --no-access-log`. Use `/health/ready` for the deployment health check once the candidate is running; August code does not provide it. `/` remains process liveness. Independently verify proxy trust before relying on login/IP limits.
4. Publish only the reviewed candidate through GitHub `main` after its checks and the release gates pass. Deploy the backend candidate and verify database readiness before opening its paired frontend. Build the frontend with the final `NEXT_PUBLIC_API_URL`; rebuilding is required when that public build variable changes. Verify both provider commit IDs rather than assuming automatic deployment selected the right SHA.
5. Before staff entry, check HTTPS/security/private-cache headers, authorized owner/employee login, denied owner actions, direct receipt links, refresh and logout. Any authorized hosted test writes must use a clearly marked fictional environment. Do not manufacture transactions in the real pilot or silently delete test history.
6. Record actual revisions, deployment time, readiness/alert evidence and approval in the release record. Then open the ten-trading-day receipt-backed trial. Stop new entry on money disagreement, failed recovery or unreliable hosting; preserve records and uncertain save references.

## Recovery and rollback

- Before any real entry, a failed pilot candidate can be closed while the unchanged August demonstration remains available. It is a practice system, not a recovery source for pilot transactions.
- After real entry, stop new work and capture the current database/export and pending-save state before changing deployments. Keep the pilot database and its histories. Never redirect staff to the practice database as if it contained their work.
- Roll code back only to a previously qualified frontend/backend pair compatible with the current schema and record meanings. Do not run reverse migrations, `--clean`, or restore an older backup over live records. August Finance ignores new refund/correction semantics and is not a compatible rollback target.
- For this first release there is no previously qualified modern pilot pair. A failed cutover therefore uses retained receipts while the candidate is repaired. Restore an encrypted export into a separate approved target, verify customer/order/money histories and role configuration, then reconstruct later receipt-backed events under owner review. Do not replay unknown writes with new references.
- A later migration must document which earlier pair remains compatible before it is released. Rollback is an operational rehearsal, not a promise inferred from additive SQL or a Git revert.

## Current blockers

Authenticated Vercel inspection on 8 October confirms Hobby, which is restricted to non-commercial personal use. Production frontend remains `5da24e5`; automatic feature-branch preview `1bfdf4a` is Ready but does not qualify the pilot pair. The approved Cloudflare/OpenNext experiment now needs actual account/free-runtime qualification; do not upgrade, replace the framework or promote the preview. See [frontend-hosting-check.md](frontend-hosting-check.md). This supersedes the plan-unknown observation in the following dated checkpoint.

The exact candidate `1bfdf4a3b607a3349769fe3c4b46c64e0fb1790b` was published with explicit user approval to `codex/transaction-save-safety` on 8 October. [GitHub run 37808811073](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/37808811073) passed both jobs. Remote CI is no longer a blocker for that SHA. Fresh reads still show `main`/Render at `5da24e5`, zero pilot staff and both restricted roles NOLOGIN. Render's access-log start command and `/` health check are unchanged. The Vercel dashboard requires sign-in; actual plan remains unverified. [Current release status](pilot-release-status.md) owns the remaining work and fresh observations; the checks do not activate backups or authorize cutover.

Retention/custody/execution decisions received on 8 October: keep 90 days of daily copies; owner and user as technical maintainer hold the recovery key in separate private locations; execute at 22:00 Nairobi with the shop PC off. The [disabled hosted candidate](hosted-backup-check.md) is locally verified. Actual unattended authorization, pilot key/offline-copy exercise, alerts and retention handling remain unqualified.

As of 8 October: clothing permission is approved/applied; approved Drive identity/private folder and encrypted disposable upload/readback are verified ([storage check](drive-storage-check.md)). Private destination is selected; initial daily time/recipient choices are recorded. Runtime/backup roles remain NOLOGIN in the latest database check. Actual offline-key/database recovery and delivered alerts remain open. Private passwords, final staff acceptance, actual cloud backup and operational rollback remain open; frontend hosting and the exact deployed pair remain unverified. Render inspection on 5 October found automatic deployment of every `main` commit, start without `--no-access-log` and health-check `/`; recheck and coordinate these settings for the candidate, not blindly while old code serves the demonstration.
