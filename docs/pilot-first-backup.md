# First encrypted pilot backup — human-only run

Prepared 13 October 2026. The user reports the folder-consent helper passed. No Google setup or consent repeat is needed. This first run uses the existing pilot-only restricted backup connection, selected private Drive folder and original recovery key. It does not enable a schedule, clean up archives, change the database or authorize real-customer entry.

## Ready checks

- The original Desktop client compatibility fix passed 24 fictional consent/storage checks. The user subsequently reports PASS from the actual helper; credential contents stayed private.
- Twelve fictional backup-job/storage-budget checks pass. They cover verified remote readback, capacity refusal, required settings, pinned export client and truthful success-marker ordering.
- Docker initially failed to start. A bounded restart timed out, but subsequent independent engine status and server readback show running / 29.8.0. The exact pinned PostgreSQL 17 image is present in Docker context `default`.
- These are tool checks, not a real archive or restore result. No real secrets or archive contents were loaded by the agent.

## Private path settings

In your own editor outside Codex, open the existing file:

`C:\Users\1ann0\qlms\backend\ops\private\.env.pilot-hosted-backup`

Set these nonsecret path fields, using the original existing recovery key:

```dotenv
QLMS_BACKUP_KEY_FILE=C:/Users/1ann0/QLMS-Recovery/backup.key
QLMS_BACKUP_LOCAL_FOLDER=C:/Users/1ann0/QLMS-Backups
```

If `QLMS_BACKUP_KEY_BASE64` is present, leave its value empty: the runner requires exactly one key source. Keep the existing database connection, account, folder, OAuth grant and other settings. Save and close the file privately. Do not send its contents or a screenshot. The encrypted work folder is outside the Git repository and separate from the recovery key.

## Run once

In your own PowerShell outside Codex, run these blocks separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
$env:DOCKER_CONTEXT = 'default'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.backup_job --config .\ops\private\.env.pilot-hosted-backup
```

The job refreshes the grant, checks the account/folder, exports through the restricted role, encrypts locally, checks the 90-copy projection and real Drive quota, uploads, downloads and authenticates the copy. It writes success only after those checks pass. Keys do not go to Drive. No scheduler or automatic deletion is enabled.

On success, send only the two safe lines beginning:

```text
Verified archive:
Encrypted Drive archive downloaded and authenticated.
```

The size line is needed for the actual storage estimate. It exposes no database rows or credential values. Keep local archives, remote IDs and private success markers outside chat.

On failure, send only the line beginning `QLMS backup failed`. Do not send raw Docker/PostgreSQL logs, URLs, key or token values. Do not retry blindly: a lost upload response can leave a remote archive despite local failure, and the runner deliberately does not repeat uncertain writes.

## Remaining qualification

A successful run proves unattended refresh and encrypted upload/readback for this snapshot, not operational restoration. Next is a fresh remote download and separate timed restore using a recoverable key copy. Preserve the pilot/practice datasets; no restoration into their existing schemas. Actual expiry cleanup, delivered failure/missed-run alerts and a hosted laptop-off run are still required before scheduling and real-data release.

The agreed ceiling is 5,000,000,000 bytes with 1,000,000,000 bytes reserved. Ninety equal-size files must fit within 4,000,000,000 bytes; growth and extra manual snapshots also consume space. Use measured encrypted bytes, not database allocation, to report storage.
