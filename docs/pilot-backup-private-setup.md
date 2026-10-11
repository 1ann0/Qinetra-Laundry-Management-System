# Private backup setup — human steps

The Qinetra Drive plugin and the existing private backup folder are already connected and verified. Do not reconnect them. A GitHub runner needs its own narrowly scoped grant because it cannot use the chat plugin's authentication.

Never put a password, recovery key, downloaded client JSON, authorization URL/code or token in chat, screenshots, public GitHub or command arguments. Agents must not execute these commands against real private files. Run them yourself in PowerShell outside Codex. Share only safe PASS/FAIL lines.

## 1. Create and keep the recovery key

Completed for this pilot: the user reported key creation PASS and later confirmed both separate private recoverable copies. Keep those copies; the commands below are reference instructions, not a request to generate a replacement.

Run these blocks separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
& '..\tmp\test-venv\Scripts\python.exe' -m ops.init_backup_key --key-file 'C:\Users\1ann0\QLMS-Recovery\backup.key'
```

The command secures the empty file before generating 32 random bytes. It refuses an existing file and prints no key. A successful result starts `PASS: recovery key created privately.` If it reports FileExistsError, keep the existing file and stop; do not delete it or make a different key for existing archives.

Keep recoverable copies for the Qinetra owner and you as the human maintainer in separate private vaults or encrypted storage outside the Drive backup destination. At least one must remain accessible if the shop computer is lost. ChatGPT does not hold a copy. Do not email the key or open it in an editor visible to Codex. Confirm the copies privately; later restore qualification must prove one of them works.

In your existing protected `backend\ops\private\.env.pilot-hosted-backup`, privately set `QLMS_BACKUP_KEY_FILE=C:/Users/1ann0/QLMS-Recovery/backup.key`. Keep the base64 key source unset when using a file. Do not change the completed backup database URL, verified account or recorded folder. This does not activate backups.

## 2. Create one automation client, using the existing Google account

Open [Google Cloud Console](https://console.cloud.google.com/) in your own browser. Keep credential pages outside Codex browser control. Use the existing business account; this is authorization for the runner, not a new Drive account.

1. Select or create a dedicated project named **QLMS backup automation**. No billing account or paid trial is needed for this design; stop if a screen requests payment or an unrelated upgrade.
2. In **APIs & Services → Library**, enable **Google Drive API** and **Google Picker API** for that project.
3. In **Google Auth platform → Branding**, use **QLMS backup automation** and a support/developer email you control.
4. In **Audience**, choose the appropriate external audience for the existing Gmail account. In **Data Access**, request only `https://www.googleapis.com/auth/drive.file`. Do not add full-Drive, email, Gmail or profile scopes.
5. Set the publishing status to **In production**. A Testing consent refresh token expires after seven days for this scope. The helper asks you to check this setting; that confirmation is a human attestation, not an API verification of Google's project configuration.
6. In **Clients → Create client**, choose **Desktop app**, named **QLMS private backup runner**. Download its JSON directly to `C:\Users\1ann0\qlms\backend\ops\private\google-desktop-client.json`. Keep the file protected and ignored. Do not paste its contents anywhere.

Google's [desktop Picker guide](https://developers.google.com/workspace/drive/picker/guides/desktop-mobile-picker) supports a folder picker within the OAuth flow. It needs no additional JavaScript page or API key. The helper uses a loopback callback, state and PKCE, asks for offline access and excludes previously granted broader scopes. Google documents the [Testing refresh-token limit and other expiry/revocation conditions](https://developers.google.com/identity/protocols/oauth2#expiration); production consent can still be revoked or expire and must be monitored.

## 3. Authorize only the recorded backup folder

With the downloaded client saved privately, run this in the same private PowerShell:

```powershell
& '..\tmp\test-venv\Scripts\python.exe' -m ops.drive_authorize
```

After checking Audience yourself, type `IN PRODUCTION` in that private terminal. The helper opens Google's consent/picker in your browser. Use the existing business account and select only the existing privately recorded backup folder. Do not select a new folder or grant full-Drive access.

The callback listens only on `127.0.0.1` for up to five minutes. It does not log or echo codes. The helper rejects mismatched state, duplicate callback fields, multiple/wrong files, broader scope and explicitly time-limited refresh grants. Before saving anything it checks the Drive identity and private, owned, writable folder. It updates only the three grant fields in the existing private file, retaining its file permissions.

Report only:

`PASS: selected private Drive folder and account verified; runner consent saved privately. Schedule remains off.`

If it fails, report only the safe FAIL line. Close the consent tab and inspect the setup privately before retrying. Do not copy a raw Google error, callback URL, JSON or traceback.

## Still required before real entry

This setup does **not** prove an independent backup, restore, key recovery, 90-day expiry cleanup, email delivery or laptop-off schedule. Those require a real encrypted export, Drive readback, separate timed restore, actual archive/quota measurements, retention rehearsal, delivered failure/missed-run alerts and a verified hosted run. The schedule stays disabled until those results pass.

Agreed storage budget: 5 GB total, 1 GB reserve, 4 GB usable for 90 archives. An equal-size daily archive must stay at or below 44,444,444 bytes (about 44.4 MB). Actual archive size and Drive usage still need measurement; this is a limit, not a prediction of the shop's future data growth.
