# Private recovery proof — human-only run

Prepared 13 October 2026. The first actual backup passed: 103,411 encrypted bytes, 9,306,990 bytes for 90 equal-size copies. No OAuth/account setup or new backup is needed. The independent restore remains unverified until the human supplies the result below.

## What this checks

`ops.verify_pilot_restore` uses the existing private backup settings and success marker. It downloads the verified archive afresh from the expected private Drive destination, authenticates it using a separately stored recovery-key copy and restores into a newly created local PostgreSQL container. It compares every table's rows, including duplicate rows, and sequence values with the authenticated archive. It does not connect to the pilot database, upload/delete Drive files or activate scheduling.

The pinned PostgreSQL image must already exist. Only local loopback receives the temporary database connection; its database files are in a bounded memory filesystem with no host volume. Plaintext rows are compared in memory and never printed or saved as host SQL files. The encrypted temporary download and generated container are removed before PASS. Cleanup failure is a FAIL. Recovery time starts before downloading and includes database start, restoration, comparison and cleanup; it excludes obtaining a replacement computer, installing tools and finding the private key copy. This is a controlled local recovery test, not proof of a hosted replacement API.

## Run privately

1. Keep Docker Desktop running.
2. Privately make one of the separately stored recovery-key copies available as a file on your computer or attached private drive. Use that existing copy, not the original `C:\Users\1ann0\QLMS-Recovery\backup.key`. Do not generate a replacement key, put it in the backup folder, send it to chat or upload it to Drive. If your vault holds a file attachment, download it privately outside the backup folder. You may delete that temporary key copy yourself after the test while preserving the two recoverable stored copies.
3. In File Explorer, select the copy and choose **Copy as path**. This copies the filename/path, not the key contents. Keep it private.
4. In your own PowerShell outside Codex, run these two blocks separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.verify_pilot_restore
```

5. At `Private recovery-key COPY path (keep it out of chat):`, paste that file path and press Enter. Quoted Windows paths are accepted. Wait for the PowerShell prompt to return.
6. Send only the entire final `PASS:` or `FAIL:` line. Do not send the entered path, file, configuration, keys, remote IDs, screenshots or raw logs. A FAIL leaves the schedule off; inspect before repeating.

Expected safe success: `PASS: fresh Drive download authenticated with recovery-key copy; ... tables and sequence values match; separate local restore and cleanup completed in ... seconds. Schedule remains off.`

## Developer evidence and next gates

All 35 focused fictional transport/encryption/manifest/target/cleanup/key-custody checks pass (0.839 s). The real Docker/PostgreSQL rehearsal passed with 22 fictional tables, payment/refund/customer/correction histories and sequences (8.9 s for the full rehearsal). Money mismatch and cleanup failure both refuse success; the original key, a hard-link alias and a key inside the archive folder are refused. A stored copy works even when the original is unavailable. That rehearsal is separate from actual recovery evidence. Read-only review assumes one human operator; there is no concurrent reset, external restore target or real-record output.

Even after actual PASS: qualify 90-day retention cleanup, deliver failure and missed-run alerts to the company email, and verify hosted execution with the shop computer off. Scheduling and real-data use remain gated.
