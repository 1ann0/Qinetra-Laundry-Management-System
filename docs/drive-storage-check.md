# Drive storage qualification — 8 October 2026

The approved business connection and privately recorded replacement folder now work. This closes account routing and small-file storage access; it does not qualify daily database backup or production recovery.

## Fresh evidence

| Check | Result |
| --- | --- |
| Account identity | Two live profile reads matched the user-approved business account. No connection was added, removed or reauthorized. |
| Pending folder | Metadata read and empty-folder listing succeeded. Folder MIME type matched; `shared=false`, with exactly one user/owner permission for the approved account. |
| Encrypted upload | Uploaded one clearly named disposable `.qlmsprobe`, using the existing `ops.backup.encrypt_export` envelope. It contains no database records; its random key stayed local, outside the upload directory. |
| File access | Remote metadata confirmed the expected parent, 199-byte size, binary MIME type and the same sole-owner/private permission boundary. |
| Download/readback | Retrieved complete remote bytes through the connector's streamed file reference. SHA-256 matched the original; `decrypt_export` authenticated the envelope and recovered the exact probe payload/metadata. Local tampering was rejected. |
| Privacy after upload | A final folder read still returned `shared=false` and the single approved owner. No sharing change occurred. |
| Private setup | Promoted the verified pending reference into the selected destination, cleared pending, and recorded verification time/probe evidence. Readback passed; Windows access remains limited to the current account and Git excludes the file. Alerts remain disabled. |

Probe ciphertext SHA-256: `077c04bea5e18a6a2965443bd40387e915eb5843698704d6152a4f26a43ff2db`. Verification completed at 12:12 Nairobi on 8 October. Actual account identity, folder/file references and setup values remain in private operations configuration, absent from this document and application code.

The first local download transport failed with `EACCES`. A narrow read of the connector-returned file reference through the approved network path succeeded; checksum and decryption were checked against those downloaded bytes. No second upload or inline base64 fallback was needed. The temporary download access reference was removed.

## Reproduce with disposable data

The ignored helper `tmp/qualify-drive-storage.py` creates a fresh local probe with a separate key and expected payload. It imports the actual backup encryption/decryption functions; it never connects to a database. Its `create` command prints only local paths, ciphertext hash/size and authentication checks.

```powershell
./tmp/test-venv/Scripts/python.exe tmp/qualify-drive-storage.py create
# After uploading and independently downloading only that encrypted probe:
./tmp/test-venv/Scripts/python.exe tmp/qualify-drive-storage.py verify --manifest <local-manifest> --downloaded <downloaded-probe>
```

Use the privately recorded folder reference with the existing business connection. Before upload, check the profile, owner-only folder access and MIME type. After upload, check parent, size and private permissions before fetching complete binary bytes. Keep the probe key local; never upload it alongside the file. Do not mark a database backup successful from this probe result.

Optional final-session browser check: open the already-connected approved business Drive, follow the private folder link and find `qlms-storage-probe-20261008.qlmsprobe`. Manage access must show Restricted and only its owner. This is an operations check, with no new staff interface or application screenshot. The old wrong-account folder remains untouched.

## Next gates

- User selected 90-day retention and separate recovery-key custody for the owner and the user as technical maintainer. These choices are recorded privately; the actual offline key copies and recovery exercise are still pending. Do not enable automatic deletion before recovery is qualified.
- Confirm whether the shop computer may be off at 22:00 Nairobi, then qualify the appropriate zero-spend schedule. This is an operating choice, not repeated account setup.
- Privately configure and verify the restricted backup connection and actual export. The setup-choice file contains no backup runtime connection; `backup_job.py` still requires its separate database/key/local/independent configuration.
- The interactive Drive connector is not an unattended backup runner. Qualify a zero-spend execution path, authenticated upload/download, missed-run/failure delivery and restart behavior. A synced local copy alone is insufficient.
- Restore a real pre-entry export into a separate approved target, verify complete record/role/money behavior and demonstrate recovery-key access. Do not overwrite the pilot or import practice records.
- Keep actual backups, scheduler and alerts inactive until their gates pass. Final staff acceptance, hosting, exact remote CI/release pair and coordinated cutover remain open.
