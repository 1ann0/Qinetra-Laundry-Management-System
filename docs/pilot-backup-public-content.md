# Backup app public-page content — approved copy

Prepared 12 October 2026 from the backup runner and Drive transport source; the user approved this content and the public pages. Implemented under `frontend/src/app/backup/`. These pages are not deployed. They contain no credentials, private folder identifiers or customer records.

## About page: QLMS backup automation

QLMS is Qinetra Laundry's staff system for customer records, laundry orders and payments. QLMS backup automation is a separate recovery tool for that system. It lets the Qinetra owner authorize encrypted database copies in a privately selected Google Drive folder and retrieve those copies for recovery checks.

Only the Qinetra owner authorizes the business Google account. This backup permission does not sign anyone in to QLMS or give employees access to the owner's Google account.

Automatic backups are undergoing qualification and are not yet active. The intended schedule is daily at 22:00 Nairobi time, using a hosted runner that does not depend on the shop laptop being on. The agreed retention target is 90 days; scheduled execution, cleanup and recovery must pass qualification before activation.

Links: Backup privacy; Backup terms; Staff sign in. Contact: qinetraian@gmail.com.

## Privacy page: QLMS backup automation privacy

Last updated: 12 October 2026. This notice covers Qinetra's backup automation, rather than customer-facing sign-in or a public laundry service.

### Google information used

The tool requests only `https://www.googleapis.com/auth/drive.file`. It uses the authorized account's email address to confirm the expected business account; Drive storage quota to check capacity; and selected folder/archive metadata to check ownership, privacy, size and destination. It creates encrypted QLMS archives and downloads its archives to verify or restore them. This permission can cover files selected for or created by the app; the runner additionally checks its privately configured destination.

It does not request Gmail, contacts, calendar or profile permissions. It does not browse unrelated Drive files. The backup content includes QLMS business records, which may contain customer contact information, orders, payments and staff records. This data is encrypted before upload to Drive. An encrypted copy still requires careful handling.

### Storage and access

Google stores the encrypted archives in the owner's selected private Drive folder. Authorized recovery work can temporarily create decrypted database files on the recovery machine. The owner and human maintainer keep separate private recovery-key copies outside the backup folder.

Authorization credentials are kept in protected local configuration and, when hosted scheduling is activated, private runner configuration. They must not appear in chat, public source, screenshots or logs. The scheduled runner will use GitHub Actions; backup files must not be published as workflow artifacts or caches. Only the owner and authorized maintainer should operate these credentials and recovery procedures.

Google-derived information is used for backup authorization, destination/capacity checks and recovery. It is not sold, used for advertising or used to train AI models. Credentials and customer backup content must not be sent to ChatGPT. Google and the configured hosting providers process the information needed to provide storage and execution.

### Retention and control

The agreed target is 90 days of daily backups. Automatic cleanup and scheduling are not active yet; this notice does not claim older copies are currently removed automatically. Qualification must establish the cleanup procedure and measured storage allowance before scheduled use.

The owner can revoke the app's permission through their Google Account's third-party connections. Revoking permission stops future authorized access; it does not delete existing Drive archives. The owner can manage those files in Drive. Backup snapshots may retain older records until their retention period ends. For access, deletion or recovery requests, contact qinetraian@gmail.com. Do not include passwords, keys or customer records in the initial message.

Updates to the automation's data handling require an updated notice before activation of the changed behavior.

## Terms page: QLMS backup automation use

This recovery tool is for Qinetra's authorized owner and human maintainer. Authorize only an account and destination that you are permitted to manage. Keep credentials and recovery keys private, and do not share the owner's Google sign-in with employees.

Backup success requires verified upload and readback; usable recovery also requires a tested restore and a recoverable key. A setup confirmation alone does not prove either. Automatic backups remain inactive while these checks are incomplete.

Free hosting and Google authorization can be interrupted or revoked. The owner must receive and act on operational failure/missed-run alerts once scheduling is activated. Losing all recovery-key copies makes encrypted archives unusable.

Contact qinetraian@gmail.com for backup support. Links: About backup automation; Backup privacy; Staff sign in.
