# PC-off backup runner — 8 October 2026

User requirements: daily backup at 22:00 Nairobi while the shop PC may be off, 90-day retention, and separate recovery-key copies for the Qinetra owner and user as technical maintainer. Spend nothing; preserve the existing Drive connections, private destination and all practice records.

## Implementation

- `backend/ops/drive_storage.py` uses the standard Python library and existing encryption functions. It refreshes a separately authorized unattended token, checks account/folder ownership and privacy, uploads encrypted bytes, checks the uploaded file's parent/access/size, downloads the file and authenticates the matching ciphertext/plaintext. It checks the folder again before returning success. No sharing, deletion, public backup endpoint or automatic write retry exists.
- `backup_job.py` retains local-copy mode and adds Drive mode plus protected environment configuration. Cloud mode requires the selected project, TLS, `qlms_backup`, `qlms`, a 32-byte key, explicit private account/folder, offline OAuth settings and pinned client. A remote failure or absent verified reference cannot replace the earlier success marker. Markers record archive size and agreed retention; they contain no credentials and are private operational state.
- `backup.py` can use a pinned PostgreSQL 17 client container for export, without passing passwords in command arguments. Cloud client mode cannot restore. Existing separate-target restore protections remain in place.
- `.github/workflows/pilot-backup.yml` proposes GitHub-hosted Ubuntu execution at 19:00 UTC, with pinned official actions/client, read-only repository permission, serialized jobs and secrets available only to the backup step. It has no caches or artifact uploads. The job requires `QLMS_HOSTED_BACKUP_ENABLED=true` and `main`; absent configuration leaves it disabled. Publishing `main` is still a coordinated release action because Render auto-deploys it.
- No new product dependency or frontend/API/schema change. `hosted-backup.env.example` names private settings without actual values. The existing interactive Drive connection is unchanged; its OAuth token is not extracted or reused as an external runner secret.

## Verification

Changed-file inventory:

| File(s) | Purpose |
| --- | --- |
| `.github/workflows/pilot-backup.yml` | Disabled hosted schedule and private runner environment. |
| `backend/ops/drive_storage.py` | OAuth refresh, account/privacy checks, encrypted upload and authenticated readback. |
| `backend/ops/backup.py` | Pinned PostgreSQL client for cloud export. |
| `backend/ops/backup_job.py` | Environment/cloud mode and honest success/size marker. |
| `backend/ops/hosted-backup.env.example` | Private configuration names with placeholders. |
| `backend/ops/rehearse_recovery.py` | Pinned-client restore rehearsal and archive-size measurement. |
| `backend/tests/run-postgres-tests.ps1` | Optional cloud-client qualification in the disposable runner. |
| `backend/tests/test_drive_storage.py`, `backend/tests/test_hosted_backup_job.py` | Wrong-identity/privacy/corruption/credential/error and marker-ordering checks. |
| `backend/ops/README.md` | Private command/configuration instructions. |
| `docs/hosted-backup-check.md`, `docs/drive-storage-check.md` | Current developer evidence, storage budget and limits. |
| `docs/pilot-handoff.md`, `docs/pilot-essentials-check.md`, `docs/pilot-release-runbook.md` | Fresh continuation and unresolved activation/release gates. |
| `docs/creator-operations-guide.md`, `IMPLEMENTATION_ROADMAP.md` | Resolved owner choices and creator authorization boundary. |
| Ignored `LEARNING_NOTES.md`, `PRESENTATION_NOTES.md` | Data flow, learning backlog and demo explanation. |
| Ignored private `.env.pilot-setup` and `tmp/qualify-drive-storage.py` | Selected destination/choices/status and disposable storage probe. No filled values or probe key enter Git. |

Focused checks cover correct encrypted readback, wrong account, private/unwritable/incomplete folder, unexpected parent/owner/size, modified/truncated/oversized bytes, wrong key, non-database archive, untrusted upload URL, lost upload reply, sanitized OAuth errors and success-marker ordering. Tests use fictional accounts/tokens and HTTP fixtures, not a live automation grant.

Final full backend run: **221 tests passed with PostgreSQL/no skips** (66.610s), including a new guard against false success when no verified remote reference is returned. Full migration application/reapplication and empty schema restore passed. The pinned client then exported the restricted fictional schema, and separate-database restoration verified contact/clothing/settings history, KES 1,000 payment/KES 200 refund, retained charge/cash KES 800, zero debt and login hash (6.8s). The full encrypted fixture measured 103,574 bytes again. This is local developer evidence, not a hosted OAuth run or measured shop recovery.

The local pinned client reports PostgreSQL 17.11. actionlint accepts both workflows. Real interactive folder/probe evidence is in [drive-storage-check.md](drive-storage-check.md); those checks do not qualify this new unattended OAuth client or a real database export.

## Storage budget

The initial real PostgreSQL fixture archive measured **103,574 bytes** (0.104 MB). Ninety equal-size copies use **9,321,660 bytes**, about **9.3 MB / 0.0093 GB**. The fixture contains the full schema and a small fictional contact/order/payment/refund/settings history; it is not a real trading-volume forecast. A read-only pilot metadata query returned 22 tables, 24,576 table bytes and 688,128 table/index bytes; database allocation and compressed archive size are different measurements.

For planning, add the sizes of the retained daily archives. `90 × latest archive size` is a useful rolling-window approximation when sizes are similar; extra manual/pre-release copies and growth need additional space. Examples using decimal MB/GB:

| Daily encrypted file | 90 equal-size copies |
| --- | --- |
| 1 MB | 90 MB / 0.09 GB |
| 10 MB | 900 MB / 0.9 GB |
| 50 MB | 4,500 MB / 4.5 GB |

User reports a **5 GB allowance, all free**; this is recorded privately as user-reported, not an independent quota read. The 9.3 MB fixture projection uses about **0.19%** of that space. At 10 MB per archive, 90 copies use 0.9 GB. Five decimal GB holds 90 equal-size archives of about 55.6 MB each before headroom, or about 44.4 MB each when reserving 20% for growth/other use. These are capacity calculations, not predictions of actual order volume.

Google storage is shared with Gmail, Photos and other covered backups, so future other use reduces the space available. [Google storage explanation](https://support.google.com/accounts/answer/14733746?hl=en). Actual export sizes and account quota must be checked before activating the job. The 90-day policy is recorded; expiry cleanup remains to qualify after recovery, and this runner currently preserves every archive.

## Activation gates

1. User confirmed only the connected Drive plugin exists; no unattended OAuth client/grant is configured. Keep both connections/folder privacy. A dedicated folder-limited authorization for the same business account is required for the cloud runner; obtain the user's Google consent without extracting plugin credentials or requesting secrets in chat. Prefer `drive.file` with explicit folder selection; do not silently broaden to full Drive access or a shared service-account folder. This is runtime authorization for a different program, not reconnecting either existing plugin account. Check revocation and expiry; Google's external Testing grants normally expire after seven days for Drive scopes. [Google OAuth guidance](https://developers.google.com/identity/protocols/oauth2), [Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth).
2. Configure fresh restricted backup credentials, approved project/schema and actual TLS connection. Privately generate the real key, keep separate owner/maintainer recovery copies, then demonstrate access without this machine. Nothing in the private choice record presently supplies these runtime secrets.
3. Rehearse actual export, direct API upload/readback and restoration in a separate target. Verify the full application/money history and measure real archive size. Check account free space against growth and retained-copy policy. Do not import fixture records or overwrite the pilot.
4. Qualify delivered failure and missed-run alerts before enabling the workflow. GitHub can delay/drop schedule events and disable public-repository schedules after 60 inactive days. The schedule runs only on the default branch; do not promise exact-minute execution or bypass release gates to test it. [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
5. Review the exact candidate and secret/branch/environment boundary before any remote publication. Confirm the standard public-repository runner allowance remains free. Enable only after authenticated hosted execution, key/restore, alerts and retention handling pass. No workflow, secrets, credentials, alert provider or deployment has been activated remotely by this increment.

## Reproduce developer checks

```powershell
./backend/tests/run-postgres-tests.ps1 -PythonExecutable C:/Users/1ann0/qlms/tmp/test-venv/Scripts/python.exe -CloudClientImage postgres:17@sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675
./tmp/actionlint-tool/actionlint.exe .github/workflows/verify.yml .github/workflows/pilot-backup.yml
```

The runner creates only a disposable local database, checks restricted access, exports through the pinned client and restores into another disposable database. No browser product flow changed; final staff acceptance remains the single planned session.
