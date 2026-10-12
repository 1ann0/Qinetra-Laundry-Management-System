export const metadata = { title: "Backup privacy | QLMS" };

export default function BackupPrivacyPage() {
  return (
    <>
      <p className="eyebrow">QLMS backup automation</p>
      <h1>Backup privacy</h1>
      <p>Last updated: 12 October 2026.</p>
      <p>This notice covers Qinetra&apos;s backup automation, rather than customer-facing sign-in or a
        public laundry service.</p>
      <h2>Google information used</h2>
      <p>The tool requests only <code>https://www.googleapis.com/auth/drive.file</code>. It uses the
        authorized account&apos;s email address to confirm the expected business account; Drive storage
        quota to check capacity; and selected folder/archive metadata to check ownership, privacy,
        size and destination.</p>
      <p>It creates encrypted QLMS archives and downloads its archives to verify or restore them.
        This permission can cover files selected for or created by the app; the runner additionally
        checks its privately configured destination.</p>
      <p>It does not request Gmail, contacts, calendar or profile permissions, or browse unrelated
        Drive files. Backup content includes QLMS business records, which may contain customer
        contact information, orders, payments and staff records. This data is encrypted before
        upload to Drive. An encrypted copy still requires careful handling.</p>
      <h2>Storage and access</h2>
      <p>Google stores the encrypted archives in the owner&apos;s selected private Drive folder.
        Authorized recovery work can temporarily create decrypted database files on the recovery
        machine. The owner and human maintainer keep separate private recovery-key copies outside
        the backup folder.</p>
      <p>Authorization credentials are kept in protected local configuration and, when hosted
        scheduling is activated, private runner configuration. They must not appear in chat,
        public source, screenshots or logs. The scheduled runner will use GitHub Actions; backup
        files must not be published as workflow artifacts or caches. Only the owner and authorized
        maintainer should operate these credentials and recovery procedures.</p>
      <p>Google-derived information is used for backup authorization, destination/capacity checks
        and recovery. It is not sold, used for advertising or used to train AI models. Credentials
        and customer backup content must not be sent to ChatGPT. Google and the configured hosting
        providers process the information needed to provide storage and execution.</p>
      <h2>Retention and control</h2>
      <p>The agreed target is 90 days of daily backups. <strong>Automatic cleanup and scheduling are
        not active yet.</strong> This notice does not claim older copies are currently removed
        automatically. Qualification must establish the cleanup procedure and measured storage
        allowance before scheduled use.</p>
      <p>The owner can revoke the app&apos;s permission through their Google Account&apos;s third-party
        connections. Revoking permission stops future authorized access; it does not delete
        existing Drive archives. The owner can manage those files in Drive. Backup snapshots may
        retain older records until their retention period ends.</p>
      <p>For access, deletion or recovery requests, contact <a href="mailto:qinetraian@gmail.com">
        qinetraian@gmail.com</a>. Do not include passwords, keys or customer records in the initial
        message.</p>
      <h2>Changes to this notice</h2>
      <p>Updates to the automation&apos;s data handling require an updated notice before activation of
        the changed behavior.</p>
    </>
  );
}
