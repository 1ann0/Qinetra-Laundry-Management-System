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

1. **Completed and verified 12 October:** existing project **QLMS backup automation**, ID `qlms-backup-automation`, is ACTIVE under the explicitly selected business account. Do not create another project or reconnect accounts.
2. **Completed and verified 12 October through the local MCP:** Google Drive API and Google Picker API are ENABLED. The enable operation and two separate readbacks passed. No billing activation or paid service was created; do not repeat this step or add billing to clear Cloud Hub's unrelated panel.
3. **Completed by human report, 12 October:** the user confirms **Branding created** in the selected backup project. Do not repeat branding creation. Credential pages remain outside Codex browser control; this is human confirmation, not an MCP readback.
4. **Human report, 13 October:** after the guided selection, the user confirms **drive.file is listed** in Data Access. Do not repeat selection. The intended only scope is `https://www.googleapis.com/auth/drive.file`; full-Drive, email, Gmail and profile scopes are not part of this backup client. This is not an independent scope-list readback.
5. **Completed by human report, 13 October:** the user saved the deployed Branding URLs, published the existing app and confirms Audience shows **In production**. Do not repeat those steps. This is human attestation, not an MCP configuration readback or independent ownership verification. Production removes the seven-day Testing expiry for this scope; consent can still be revoked or expire for other reasons. The helper asks for this setting again only as its private execution guard.
6. In **Clients → Create client**, choose **Desktop app**, named **QLMS private backup runner**. Download its JSON directly to `C:\Users\1ann0\qlms\backend\ops\private\google-desktop-client.json`. If Chrome saves it in Downloads, use File Explorer to move that downloaded file to the existing private directory and rename it `google-desktop-client.json`; enable **View → Show → File name extensions** to avoid `.json.json`. Keep the file closed. On 13 October, an exact Git-ignore rule was added and checked before this handoff; Git exclusion does not replace the existing private folder permissions. Do not paste its contents anywhere.

Google's [desktop Picker guide](https://developers.google.com/workspace/drive/picker/guides/desktop-mobile-picker) supports a folder picker within the OAuth flow. It needs no additional JavaScript page or API key. The helper uses a loopback callback, state and PKCE, asks for offline access and excludes previously granted broader scopes. Google documents the [Testing refresh-token limit and other expiry/revocation conditions](https://developers.google.com/identity/protocols/oauth2#expiration); production consent can still be revoked or expire and must be monitored.

## 3. Authorize only the recorded backup folder

**Human report, 13 October:** the Desktop client file is saved at the requested private location. Its contents have not been read by the agent; actual validation happens only in the human-run helper. Do not recreate/download it again.

In your own PowerShell outside Codex, run these two blocks separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.drive_authorize
```

After checking Audience yourself, type `IN PRODUCTION` in that private terminal. The helper opens Google's consent/picker in your browser. Use the existing business account and select only the existing privately recorded backup folder. Do not select a new folder or grant full-Drive access.

The callback listens only on `127.0.0.1` for up to five minutes. It does not log or echo codes. The helper rejects mismatched state, duplicate callback fields, multiple/wrong files, broader scope and explicitly time-limited refresh grants. Before saving anything it checks the Drive identity and private, owned, writable folder. It updates only the three grant fields in the existing private file, retaining its file permissions.

Report only:

`PASS: selected private Drive folder and account verified; runner consent saved privately. Schedule remains off.`

If it fails, report only the safe FAIL line. Close the consent tab and inspect the setup privately before retrying. Do not copy a raw Google error, callback URL, JSON or traceback.

13 October diagnostic update: after the missing file was corrected, the human run stopped with `ValueError` before the production prompt/browser. The helper now displays only an exact allowlist of fixed setup reasons, while all other exception details remain hidden. Share the entire new safe FAIL line, not private configuration values. Three known-reason regressions failed before the change; all 22 consent/storage checks now pass using fictional settings. Real cause/consent remain pending; no validation was relaxed.

Later 13 October format correction: the specific safe failure pointed to the Desktop client check. Google [documents installed-client files](https://github.com/googleapis/google-api-python-client/blob/main/docs/client-secrets.md) with older Google endpoint names that the helper incorrectly rejected. The local fix accepts only known official HTTPS metadata variants while keeping requests pinned to the existing modern Google URLs. Three fixture variants were red before the fix; 24 fictional checks now pass, including Web-client/host-spoofing/HTTP/query/fragment denial and fixed request destinations. Keep the original downloaded Desktop JSON and rerun privately; do not edit its contents or create another client solely for this error. Actual file contents and consent remain unverified.

## Still required before real entry

**13 October consent result:** the user reports PASS after the client-format fix. The helper's success checks the client, account and selected private folder before saving the grant. This is human-reported execution, not an agent credential read. Do not repeat client creation, consent or completed Google setup. Actual unattended refresh/export/upload/readback and recovery remain the next checks.

This setup does **not** prove an independent backup, restore, key recovery, 90-day expiry cleanup, email delivery or laptop-off schedule. Those require a real encrypted export, Drive readback, separate timed restore, actual archive/quota measurements, retention rehearsal, delivered failure/missed-run alerts and a verified hosted run. The schedule stays disabled until those results pass.

Agreed storage budget: 5 GB total, 1 GB reserve, 4 GB usable for 90 archives. An equal-size daily archive must stay at or below 44,444,444 bytes (about 44.4 MB). Actual archive size and Drive usage still need measurement; this is a limit, not a prediction of the shop's future data growth.
