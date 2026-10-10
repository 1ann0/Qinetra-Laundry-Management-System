# Pilot database and recovery operations

These are private operations tools, not browser/database access or a public bootstrap API. Install `../requirements-ops.txt` into a verified private Python environment. Use the current check record in `../../docs/pilot-essentials-check.md` for actual evidence and unresolved setup gates.

## Owner-run private database setup

The user requires all real credential handling outside ChatGPT. Agents must not read private configuration/key files, execute commands which load real secrets, capture filled password forms or inspect credential-bearing logs. Guide private entry/execution and check only sanitized status and database metadata. Existing connector authentication stays connected; do not repeat account setup.

`pilot_private_setup.py` is a bounded setup command for the existing fresh `QLMS-Qinetra-Pilot` only. It uses the four prepared owner-only `.env.pilot-*` files in `private/`. The administrator password must already match the reset completed privately in Supabase. If you prefer your own role passwords/signing secret, replace their values privately first: use separate strong values, with at least 32 bytes for the signing secret. Never paste these values into chat, command arguments, screenshots or the Codex terminal.

Open your own Windows PowerShell window outside Codex and run:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
& '..\tmp\test-venv\Scripts\python.exe' -m ops.pilot_private_setup
```

The command reads secrets locally and authenticates only to the verified pilot Supabase session pooler. Before changing access it requires the expected catalogue-only counts, 22 RLS tables, restricted grants, immutable-history protection and denied browser access. It assigns passwords/login only to the existing `qlms_runtime` and `qlms_backup` roles, using SCRAM verifiers in SQL, without changing their grants. It verifies each actual encrypted role/schema connection and saves only `DATABASE_URL` and `QLMS_BACKUP_DATABASE_URL` in the existing private files, preserving their Windows file permissions and other settings. It does not connect to the old practice project or create staff/data, deploy, upload archives, or activate a schedule. Supabase and your local process necessarily use the credentials; they are never printed to ChatGPT.

Success ends with `PASS: private pilot database setup; runtime and backup TLS connections verified; private settings saved.` Report only the PASS or FAIL/STEP lines. A STEP line means role credentials were committed, even if a later connection/file check fails; stop and share only those safe lines before continuing. Do not copy a traceback, connection URL or file contents. The administrator credential remains a private setup credential and must never be installed on Render or the frontend.

The SQL password handling follows [PostgreSQL's client-side password preparation guidance](https://www.postgresql.org/docs/current/libpq-misc.html#LIBPQ-PQENCRYPTPASSWORDCONN) through the installed [Psycopg password function](https://www.psycopg.org/docs/extensions.html#psycopg2.extensions.encrypt_password). Actual hosted connection verification remains the owner's pending action.

## Existing operations tools

- `base-schema.sql` supplies the original tables; `schema_setup.py` applies every numbered migration twice and checks current model columns.
- `rehearse_schema.py` produces `../schema/pilot.sql` and its migration/hash manifest only after a disposable local restore succeeds. The snapshot excludes prices, users and customers. Regenerate it; do not hand-edit it or apply it over an existing schema.
- `runtime_access_sql`/`backup_access_sql` configure separate restricted roles. Runtime deletion is limited to old login buckets and replaceable current clothing rows; clothing snapshots remain in immutable history. Provisioning must test those rights before opening access. Browser roles remain denied.
- `init_backup_key.py --key-file PRIVATE_PATH` creates a 32-byte owner-readable key without printing or overwriting it. Put a recoverable owner-controlled copy somewhere separate from backups. Losing the key loses access to the encrypted backups.
- `backup_job.py --config PRIVATE_ENV_FILE` takes an encrypted archive and a second verified copy. Copy `backup.env.example` to a protected private `.env`; do not commit it. A local cloud-sync copy does not prove remote upload.
- `register-backup-task.ps1 -PythonExecutable VERIFIED_PYTHON -ConfigFile PRIVATE_ENV_FILE -DailyTime HH:mm` registers a limited daily Windows task after its configuration/closing time are confirmed. The PC must be awake, connected and signed in; a missed-run/failure alert and remote upload need independent qualification. No task was registered merely by adding this file.
- `backup.py restore --key-file PRIVATE_PATH --encrypted-file ARCHIVE` reads `QLMS_BACKUP_DATABASE_URL` and `QLMS_RESTORE_DATABASE_URL`. It refuses the source database/project and any target already containing the application schema. Local targets must be named `qlms_restore_*`; remote targets need a distinct explicitly approved Supabase project via `--approved-project`. It never uses `--clean` or replaces live data.

PostgreSQL client tools must be installed separately for the unattended job. Passwords go through subprocess environment variables, not command arguments or output. The Docker runner provides clients only for its disposable local rehearsal. A restored schema still needs reviewed runtime/backup role setup; do not copy old login passwords into another project.

Keep daily exports and receipts until retention is agreed. No automatic deletion exists. Stop new trial entry on backup failure, mismatched restored records/money or unreliable hosting. The measured local restore time is not the shop's four-working-hour recovery proof.

## Hosted Drive candidate

The user requires execution with the shop PC off. The local candidate in `.github/workflows/pilot-backup.yml` stays disabled until hosted authorization/recovery/alerts qualify. See [hosted-backup-check.md](../../docs/hosted-backup-check.md) for evidence and activation boundaries.

Drive mode uses `hosted-backup.env.example` with `python -m ops.backup_job --config PRIVATE_FILE`, or protected runner secrets with `--environment`. Supply exactly one 32-byte key source: a separate private file or its base64 value in a protected secret. No key is uploaded to Drive. The job checks account/folder privacy before export, then verifies the remote encrypted file and decryption before writing success. Failures preserve the local encrypted archive and older success marker; inspect an unknown upload outcome privately before retrying.

The agreed retention is now 90 days. This is recorded as policy, without automatic deletion; cleanup needs recovery qualification. The selected owner/technical-maintainer offline copies, runtime database/Drive credentials, account quota and real alerts are not created by saving the policy. Interactive plugin access is already verified and must not be reconnected as a workaround for absent unattended credentials.
