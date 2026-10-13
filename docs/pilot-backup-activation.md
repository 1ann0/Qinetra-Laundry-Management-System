# Finish backup automation — private qualification

13 October 2026. The human reports actual Drive consent, encrypted backup/upload/readback and separate copy-key restore PASS. Archive size is 103,411 bytes; 90 equal-size copies total 9,306,990 bytes (9.31 MB). The full restore result line was not supplied, so its exact duration/table count is not recorded. Do not repeat those completed checks or generate another recovery key.

## What is prepared

- Explicit 90-day expiry is off by default. It runs only after a new backup is uploaded and authenticated. The complete listing and deletion plan must pass first. Only canonical QLMS filenames with authenticated schema/project/timestamp/hash and private owner/parent/deletion permission can expire; the exact 90-day boundary, fresh backup and unrelated names are preserved. Fresh and selected expired archives are rechecked before each deletion. DELETE is permanent and is never blindly retried. A failed cleanup retains the new verified backup reference but records cleanup incomplete and fails the job.
- The independent Healthchecks monitor receives only empty POST start/success/fail signals. No customer data, logs, archive, key or Google credential is sent. The ping URL is a private credential. Redirects and unexpected hosts are blocked; a 200 `OK (not found)` or rate-limit response is not success. Signal acknowledgment alone does not prove an email arrived.
- GitHub's manual qualification and daily schedule have separate disabled switches. The protected environment has no PR/fork execution, caches or archive uploads. Daily execution additionally requires retention qualified. Start is signaled before dependency installation; failed/cancelled jobs signal failure where possible, while the independent monitor catches missing signals when the job never starts or the runner cannot signal.

Current provider qualification: [Healthchecks' free plan](https://healthchecks.io/pricing/) supports 20 checks; its [failure/missing-run behavior](https://healthchecks.io/docs/configuring_checks/) supports this one monitor. [Standard GitHub-hosted runners are free for public repositories](https://docs.github.com/en/billing/concepts/product-billing/github-actions). The connected repository is public and defaults to main. [Scheduled GitHub jobs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) can be delayed and public schedules can be disabled after 60 inactive days, so the independent missed-run alert is required. No paid plan or card is needed for the proposed configuration; the actual hosted run remains pending.

## 1. Email qualification

The human confirms the free monitoring account is ready. In its private dashboard create one check named **QLMS backup qualification**, temporarily with Simple schedule, Period **1 minute**, Grace time **1 minute**, and the agreed company-email integration enabled. Save its Ping URL privately in the existing `.env.pilot-hosted-backup` as `QLMS_BACKUP_MONITOR_URL=...`. Never put the filled URL in chat, a public file or a screenshot. The monitor has no access to Drive.

In your own PowerShell outside Codex, run separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.qualify_backup_alerts
```

The terminal guides the test:

1. Type `TEST ALERTS` only when the temporary schedule and company email are set.
2. Wait for the deliberate failure email. Only after reading it in the company inbox, type `RECEIVED`. If it does not arrive, do not confirm; report that delivery failed.
3. The helper waits 130 seconds with no pings. Wait for a **new** Down/missing-run email, distinct from the first email; then type `RECEIVED`.
4. Send only the final PASS/FAIL line. PASS records human-confirmed delivery, not an agent mailbox inspection. No database or backup operation runs.
5. Immediately rename the check **QLMS daily backup** and change its schedule to Cron, `0 22 * * *`, timezone **Africa/Nairobi**, Grace time **2 hours**. This accounts for delayed GitHub execution; it is not an exact-22:00 guarantee. Confirm these final settings privately. Do not leave the 1-minute test schedule active. Actual daily scheduling remains off.

## 2. Retention qualification

In the same private PowerShell run:

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.qualify_retention
```

Type `TEST RETENTION` when asked. This creates a uniquely named private **child folder** under the approved backup destination. It uses a new disposable fixture key in memory, not the real recovery key, and uploads only encrypted fictional old/fresh/unrelated fixtures. It checks that only the 91-day-old fixture expires, that fresh/unrelated fixtures survive, and that the old fixture no longer appears. Finally it removes only that verified generated folder with recognized fixture contents. An unknown file/response or failed cleanup is a FAIL requiring private inspection before retrying. It never exports a database, reads the real recovery key, selects real backup IDs for deletion or enables daily cleanup.

Send only its final PASS/FAIL line. Preserve the existing private key copies and actual archives. After PASS, the same 90-day policy may be enabled for the hosted candidate through its protected variable; the local private flag remains false until deliberately changed.

## 3. Hosted release boundary

The prepared workflow currently requires main. The repository's older default branch can trigger original Render/Vercel integrations; do not silently merge the entire app branch to install a scheduler. Decide and verify the exact publication boundary, protected environment and integration behavior first. No remote workflow, secret, variable, merge or schedule was changed by this local increment. Source-only publication never includes the private config, downloaded Google client, key or archives.

Once the reviewed workflow/code is on its qualified default branch, the human installs the existing secrets privately in environment `qinetra-pilot-backup`: restricted DB URL, key base64, Drive account/folder and three OAuth grant fields, plus the monitor URL. Project ref is a protected nonsecret variable. Never paste or reread secrets through the agent. A prepared helper may reduce this handoff; it must be tested with fictional values first.

Use `QLMS_BACKUP_QUALIFICATION_ENABLED=true` only for the reviewed manual qualification; keep `QLMS_HOSTED_BACKUP_ENABLED` unset/false. After retention proof, set `QLMS_BACKUP_CLEANUP_ENABLED=true`. Dispatch qualification on the reviewed default branch; verify completion metadata and receive actual mail alerts. Then demonstrate an independent hosted run while the shop laptop is off. Only after those pass may the separate daily switch be enabled. Record the workflow commit/run, monitoring schedule, delivery evidence and the first scheduled run. Keep the independent monitor armed and investigate missing runs, quota failures and revoked grants.

## Developer checks

286 full backend tests passed against disposable PostgreSQL (95.831 s), with migrations/reapplication/empty restore and 22-table fictional recovery in 38.9 s for the full rehearsal. After the final fresh-copy recheck was added, all 52 focused retention/transport/monitor/qualification/recovery/budget tests passed (0.882 s). Both workflows pass actionlint. The pinned test image now matches the restore helper, and test execution disables implicit application dotenv loading. No real private configuration, Google grant, key, email or database row was opened by the agent. This evidence does not substitute for the private delivery/deletion or hosted runs above.
