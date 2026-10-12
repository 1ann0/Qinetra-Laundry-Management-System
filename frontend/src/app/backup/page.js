import Link from "next/link";

export const metadata = { title: "QLMS backup automation | Qinetra Laundry" };

export default function BackupInformationPage() {
  return (
    <>
      <p className="eyebrow">Qinetra Laundry</p>
      <h1>QLMS backup automation</h1>
      <p>QLMS is Qinetra Laundry&apos;s staff system for customer records, laundry orders and payments.
        Backup automation is a separate recovery tool for that system.</p>
      <h2>What the backup tool does</h2>
      <p>The Qinetra owner authorizes encrypted database copies in a privately selected Google Drive
        folder. The tool can retrieve those copies for recovery checks.</p>
      <p>Only the owner authorizes the business Google account. This backup permission does not sign
        anyone in to QLMS or give employees access to the owner&apos;s Google account.</p>
      <h2>Current status</h2>
      <p><strong>Automatic backups are not yet active.</strong> The automation is undergoing qualification.</p>
      <p>The intended schedule is daily at 22:00 Nairobi time, using a hosted runner that does not
        depend on the shop laptop being on. The agreed retention target is 90 days. Scheduled
        execution, cleanup and recovery must pass qualification before activation.</p>
      <nav className="public-info-links" aria-label="Backup policies">
        <Link href="/backup/privacy">Read the backup privacy policy</Link>
        <Link href="/backup/terms">Read the backup terms</Link>
      </nav>
    </>
  );
}
