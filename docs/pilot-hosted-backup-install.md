# One-time private cloud backup installation

Use your own PowerShell outside Codex. The existing Google client, approved folder, recovery key and private settings are reused. No account setup, extra key or new Google consent is required. The human has confirmed backup/readback, separate-key restore, both delivered alert types and isolated retention PASS. The remaining proof is cloud execution with the shop laptop off.

## 1. Give your private command access to GitHub

The official portable GitHub CLI 2.102.0 is installed at `C:\Users\1ann0\qlms\tmp\github-cli\gh.exe`. Its release archive matches the official SHA256 `ae64e556ecc240b200f7eba60d550e4bb60d78e860e69dd88c449405b86067f4`. The connected GitHub plugin cannot install environment secrets. Complete this CLI authorization yourself; do not send the code, token, login link or screenshot to ChatGPT.

```powershell
& 'C:\Users\1ann0\qlms\tmp\github-cli\gh.exe' auth login --hostname github.com --git-protocol https --web
```

Use the existing `1ann0` GitHub account. This is a one-time authorization for the private local command, not a new GitHub account. Do not run `gh auth token` or enable debug output. Never share raw logs.

## 2. Transfer the existing settings privately

Wait until the reviewed workflow is installed on main. Run these as two separate lines:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.install_hosted_backup
```

Type `INSTALL BACKUP` when asked. The helper reads the existing `.env.pilot-hosted-backup` and existing key only inside your private process. GitHub receives eight encrypted environment secrets, including the runner's key copy; preserve the two separate recovery copies you already stored. Secret values never enter ChatGPT, command arguments or a generated plaintext file. The fixed environment allows only `main`, and the helper refuses unexpected existing branch/tag permissions. It verifies the repository, pilot destination and workflow checksum before installation. It does not export data, send monitor pings, dispatch a job, change the local cleanup flag or enable daily scheduling.

Send only the final `PASS:` or `FAIL:` line. If it fails, do not enable the daily switch or send raw logs. Partial installation stays inactive and may be privately resumed after identifying the failed stage.

13 October installer follow-up: a human attempt stopped at local configuration validation before GitHub mutation. A fictional reproduction identified an overly strict optional budget check: the already-qualified backup job accepts the agreed 5 GB default when the field is absent. The installer now reuses that default, still rejects another budget/project/account/retention/key choice, and prints only allowlisted fixed failure reasons. Twenty-one focused installer/budget/hosted-job checks pass; the real attempt's specific cause is not independently read. The corrected private attempt remains pending.

## 3. Prove cloud operation

After installer PASS, turn the shop laptop off. On the work phone, open [Qinetra encrypted backup](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/workflows/pilot-backup.yml). Select **Run workflow**, branch **main**, mode **qualification**, then **Run workflow**. No secrets should be entered on this page.

Keep the laptop off until the run finishes. Report only the public run link and that the laptop stayed off. The agent checks job/step metadata, while you confirm the safe archive size/readback lines privately if necessary. Success requires export, encrypted Drive upload and authenticated download plus retention and monitor acknowledgment; a green skipped job is not a pass.

Daily execution remains OFF throughout qualification. After successful cloud proof, enable the separate repository variable `QLMS_HOSTED_BACKUP_ENABLED=true`. The workflow aims for 22:00 Nairobi; GitHub may delay scheduled runs. The independent monitor stays at 22:00 Nairobi with two-hour grace. Record the first real scheduled run and investigate late/missing emails. Never treat setup alone as cloud-run proof.

## Stop or recover

Set the repository variable `QLMS_HOSTED_BACKUP_ENABLED=false` to stop daily jobs. Disable qualification as well if investigating credentials or destination errors. Preserve existing verified archives and key copies; do not regenerate keys or blindly retry an uncertain upload/delete. The established private restore command and paper receipts remain the recovery path.
