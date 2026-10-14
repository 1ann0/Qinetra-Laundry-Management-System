# Finish backup automation — private qualification

**14 October current state:** private installation passed by human report; actual cloud qualification 38456601715 succeeded and the daily switch is verified enabled. The user-approved alternative proves laptop independence through the real hosted runner and inspected inputs rather than a physically powered-off test. The first scheduled run remains unobserved. [Current proof and operating instructions](pilot-cloud-backup-qualified.md) supersede historical pending/disabled statements below; do not repeat completed setup or rehearsals.

13 October 2026. The human reports actual Drive consent, encrypted backup/upload/readback and separate copy-key restore PASS. Archive size is 103,411 bytes; 90 equal-size copies total 9,306,990 bytes (9.31 MB). The full restore result line was not supplied, so its exact duration/table count is not recorded. Do not repeat those completed checks or generate another recovery key.

## What is prepared

- Explicit 90-day expiry is off by default. It runs only after a new backup is uploaded and authenticated. The complete listing and deletion plan must pass first. Only canonical QLMS filenames with authenticated schema/project/timestamp/hash and private owner/parent/deletion permission can expire; the exact 90-day boundary, fresh backup and unrelated names are preserved. Fresh and selected expired archives are rechecked before each deletion. DELETE is permanent and is never blindly retried. A failed cleanup retains the new verified backup reference but records cleanup incomplete and fails the job.
- The independent Healthchecks monitor receives only empty POST start/success/fail signals. No customer data, logs, archive, key or Google credential is sent. The ping URL is a private credential. Redirects and unexpected hosts are blocked; a 200 `OK (not found)` or rate-limit response is not success. Signal acknowledgment alone does not prove an email arrived.
- GitHub's manual qualification and daily schedule have separate disabled switches. The protected environment has no PR/fork execution, caches or archive uploads. Daily execution additionally requires retention qualified. Start is signaled before dependency installation; failed/cancelled jobs signal failure where possible, while the independent monitor catches missing signals when the job never starts or the runner cannot signal.

Current provider qualification: [Healthchecks' free plan](https://healthchecks.io/pricing/) supports 20 checks; its [failure/missing-run behavior](https://healthchecks.io/docs/configuring_checks/) supports this one monitor. [Standard GitHub-hosted runners are free for public repositories](https://docs.github.com/en/billing/concepts/product-billing/github-actions). The connected repository is public and defaults to main. [Scheduled GitHub jobs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) can be delayed and public schedules can be disabled after 60 inactive days, so the independent missed-run alert is required. No paid plan or card is needed for the proposed configuration; the actual hosted run remains pending.

## 1. Email qualification

**Actual email qualification passed on 13 October.** With explicit permission to use only the stored monitor URL locally, the agent sent empty success/failure pings; the human confirmed a new Down email. A recovery ping was acknowledged at about 16:19 Nairobi, no pings were sent for over two minutes, and the human confirmed a new missing-run Down email. A final recovery ping was acknowledged at about 16:23. The URL was never displayed or saved in output; the temporary monitor-only runner was removed and this exception is closed. No Google credential, database password or recovery key was used. [Safe qualification record](pilot-monitor-qualification-20261013.md).

The human confirms final settings saved: **QLMS daily backup**, Cron **`0 22 * * *`**, timezone **Africa/Nairobi**, Grace time **2 hours**. This replaces the temporary 1-minute setting; it is human-confirmed rather than an agent dashboard read. No new check or Ping URL is needed. Daily backup execution remains off, so the monitor is not evidence that a backup job is running. Actual retention rehearsal has also passed by human confirmation. Next: qualified hosted installation/execution. The following commands describe the reusable human-only test; do not repeat the completed delivery proof.

In your own PowerShell outside Codex, run separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.qualify_backup_alerts
```

The terminal guides the test:

1. Type `TEST ALERTS` only when the temporary schedule and company email are set.
2. Wait for a new deliberate failure email. Only after reading it in the company inbox, type `YES` and press Enter. If it does not arrive, type `NO` to stop and report that delivery failed. A typing mistake asks again without sending another ping; the previous `RECEIVED` confirmation is also accepted.
3. The helper acknowledges the recovery ping and waits 130 seconds with no further pings. Wait for a **new** Down/missing-run email, distinct from the first email; then type `YES` and press Enter. An Up email means recovery and is not the required new Down email. Do not confirm an earlier email again.
4. Send only the final PASS/FAIL line. PASS records human-confirmed delivery, not an agent mailbox inspection. No database or backup operation runs.
5. Immediately rename the check **QLMS daily backup** and change its schedule to Cron, `0 22 * * *`, timezone **Africa/Nairobi**, Grace time **2 hours**. This accounts for delayed GitHub execution; it is not an exact-22:00 guarantee. Confirm these final settings privately. Do not leave the 1-minute test schedule active. Actual daily scheduling remains off.

## 2. Retention qualification

**Actual rehearsal passed by human confirmation on 13 October. Do not repeat it.** The command below is retained for recovery documentation. It did not activate real-folder expiry or the daily schedule.

In the same private PowerShell run:

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.qualify_retention
```

Type `TEST RETENTION` when asked. This creates a uniquely named private **child folder** under the approved backup destination. It uses a new disposable fixture key in memory, not the real recovery key, and uploads only encrypted fictional old/fresh/unrelated fixtures. It checks that only the 91-day-old fixture expires, that fresh/unrelated fixtures survive, and that the old fixture no longer appears. Finally it removes only that verified generated folder with recognized fixture contents. An unknown file/response or failed cleanup is a FAIL requiring private inspection before retrying. It never exports a database, reads the real recovery key, selects real backup IDs for deletion or enables daily cleanup.

Send only its final PASS/FAIL line. Preserve the existing private key copies and actual archives. After PASS, the same 90-day policy may be enabled for the hosted candidate through its protected variable; the local private flag remains false until deliberately changed.

## 3. Hosted release boundary

**Installed on main, still inactive:** commit `d6766d1ee2249e0616cb1389d1420933c4ea799c` adds only this workflow file. The source pin is `c06dc6290394d607dccc927c2046a2a2bb77d104`; fresh full CI run 38452241420 passed both jobs after correcting a Windows-platform test mock that broke Linux path handling. Actionlint passes. Remote commit/file readback confirms the one-file boundary; no PR was created because the connected integration denied write access, so existing Git authentication performed a checked fast-forward. Private secrets/variables and actual hosted run remain human installation/qualification work. Scheduled jobs cannot run without their separate enabled variable.

The workflow requires main but checks out a pinned, separately published operations candidate. Publish only this one workflow file to main; do not merge the application branch or unfinished reports. The 13 October Render read confirms pilot auto-deploy off and the original service rooted at backend. [Render's root-directory rule](https://render.com/docs/monorepo-support) excludes the workflow-only change from that service's deployment trigger. No application source, requirements, schema or build settings on main need change. Read back the exact main diff and deployed pair after publication. Source-only publication never includes the private config, downloaded Google client, key or archives.

Once the reviewed workflow/code is on its qualified default branch, the human installs the existing secrets privately in environment `qinetra-pilot-backup`: restricted DB URL, key base64, Drive account/folder and three OAuth grant fields, plus the monitor URL. Project ref is a protected nonsecret variable. Never paste or reread secrets through the agent. A prepared helper may reduce this handoff; it must be tested with fictional values first.

The job-admission switches `QLMS_BACKUP_QUALIFICATION_ENABLED` and `QLMS_HOSTED_BACKUP_ENABLED` must be **repository variables**: [GitHub environment variables arrive after the job starts](https://docs.github.com/en/actions/reference/workflows-and-actions/variables). Secrets, project ref and cleanup permission belong to the main-only environment. Use qualification=true only for the reviewed manual test; keep hosted=false. After the completed retention proof, cleanup may be true. The human-only installer validates the fixed pilot, existing 32-byte key, reviewed workflow checksum, existing GitHub owner and main-only environment before transferring just eight allowlisted secrets through stdin. It never prints values, stages a plaintext file, runs a backup or enables daily scheduling; it refuses unexpected existing protections rather than weakening them.

Dispatch qualification on main; verify completion metadata and actual authenticated archive/readback. The human now requests a laptop-on alternative: inspect the GitHub-hosted runner, protected environment inputs and direct cloud connections to establish that no laptop service/file/tunnel participates. Combine that inspection with the actual hosted export/readback/retention/completion result; record it accurately rather than claiming an observed powered-off test. Only after those pass may the separate daily switch be enabled. Record the workflow commit/run, monitoring schedule, delivery evidence and the first scheduled run. Keep the independent monitor armed and investigate missing runs, quota failures and revoked grants. [Private installer steps](pilot-hosted-backup-install.md).

## Developer checks

Latest alert-prompt change: the original typo fixture failed before the fix; the helper now accepts `YES`, retains `RECEIVED`, reprompts on invalid input without another ping, and safely stops on No/cancellation. All 289 backend tests passed against disposable PostgreSQL (103.289 s), followed by migrations/reapplication/empty restore and 22-table fictional recovery/sequence comparison/cleanup (23.2 s for the full recovery rehearsal). All 8 named focused alert tests also passed (0.039 s). The earlier 52 focused retention/transport/recovery/budget checks and actionlint results remain recorded for the unchanged workflow. Actual delivery is qualified above; actual retention deletion and hosted execution remain separate gates. Google credentials, the real key, database passwords and customer records stayed outside agent use.
