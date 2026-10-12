export const metadata = { title: "Backup terms | QLMS" };

export default function BackupTermsPage() {
  return (
    <>
      <p className="eyebrow">QLMS backup automation</p>
      <h1>Backup terms</h1>
      <h2>Authorized use</h2>
      <p>This recovery tool is for Qinetra&apos;s authorized owner and human maintainer. Authorize only
        an account and destination that you are permitted to manage. Keep credentials and recovery
        keys private, and do not share the owner&apos;s Google sign-in with employees.</p>
      <h2>Recovery checks</h2>
      <p>Backup success requires verified upload and readback; usable recovery also requires a
        tested restore and a recoverable key. A setup confirmation alone does not prove either.
        <strong> Automatic backups remain inactive while these checks are incomplete.</strong></p>
      <h2>Availability and responsibilities</h2>
      <p>Free hosting and Google authorization can be interrupted or revoked. The owner must receive
        and act on operational failure/missed-run alerts once scheduling is activated. Losing all
        recovery-key copies makes encrypted archives unusable.</p>
      <p>Contact <a href="mailto:qinetraian@gmail.com">qinetraian@gmail.com</a> for backup support.</p>
    </>
  );
}
