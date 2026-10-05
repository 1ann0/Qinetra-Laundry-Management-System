# Pilot database and recovery operations

These are private operations tools, not browser/database access or a public bootstrap API. Install `../requirements-ops.txt` into a verified private Python environment. Use the current check record in `../../docs/pilot-essentials-check.md` for actual evidence and unresolved setup gates.

- `base-schema.sql` supplies the original tables; `schema_setup.py` applies every numbered migration twice and checks current model columns.
- `rehearse_schema.py` produces `../schema/pilot.sql` and its migration/hash manifest only after a disposable local restore succeeds. The snapshot excludes prices, users and customers. Regenerate it; do not hand-edit it or apply it over an existing schema.
- `runtime_access_sql`/`backup_access_sql` configure separate restricted roles. Runtime deletion is limited to old login buckets and replaceable current clothing rows; clothing snapshots remain in immutable history. Provisioning must test those rights before opening access. Browser roles remain denied.
- `init_backup_key.py --key-file PRIVATE_PATH` creates a 32-byte owner-readable key without printing or overwriting it. Put a recoverable owner-controlled copy somewhere separate from backups. Losing the key loses access to the encrypted backups.
- `backup_job.py --config PRIVATE_ENV_FILE` takes an encrypted archive and a second verified copy. Copy `backup.env.example` to a protected private `.env`; do not commit it. A local cloud-sync copy does not prove remote upload.
- `register-backup-task.ps1 -PythonExecutable VERIFIED_PYTHON -ConfigFile PRIVATE_ENV_FILE -DailyTime HH:mm` registers a limited daily Windows task after its configuration/closing time are confirmed. The PC must be awake, connected and signed in; a missed-run/failure alert and remote upload need independent qualification. No task was registered merely by adding this file.
- `backup.py restore --key-file PRIVATE_PATH --encrypted-file ARCHIVE` reads `QLMS_BACKUP_DATABASE_URL` and `QLMS_RESTORE_DATABASE_URL`. It refuses the source database/project and any target already containing the application schema. Local targets must be named `qlms_restore_*`; remote targets need a distinct explicitly approved Supabase project via `--approved-project`. It never uses `--clean` or replaces live data.

PostgreSQL client tools must be installed separately for the unattended job. Passwords go through subprocess environment variables, not command arguments or output. The Docker runner provides clients only for its disposable local rehearsal. A restored schema still needs reviewed runtime/backup role setup; do not copy old login passwords into another project.

Keep daily exports and receipts until retention is agreed. No automatic deletion exists. Stop new trial entry on backup failure, mismatched restored records/money or unreliable hosting. The measured local restore time is not the shop's four-working-hour recovery proof.
