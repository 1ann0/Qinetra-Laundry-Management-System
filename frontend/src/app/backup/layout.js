import Image from "next/image";
import Link from "next/link";

export default function BackupInformationLayout({ children }) {
  return (
    <div className="public-info-page">
      <a className="skip-link" href="#backup-content">Skip to content</a>
      <header className="public-info-header">
        <Link href="/backup" aria-label="QLMS backup information">
          <Image src="/qinetra-logo.jpg" alt="Qinetra Laundry" width={160} height={94} />
        </Link>
        <nav className="public-info-links" aria-label="Backup information">
          <Link href="/backup">About backups</Link>
          <Link href="/backup/privacy">Privacy</Link>
          <Link href="/backup/terms">Terms</Link>
          <Link href="/login">Staff sign in</Link>
        </nav>
      </header>
      <main id="backup-content" tabIndex={-1} className="public-info-content">
        {children}
      </main>
      <footer className="public-info-footer">
        <p>Backup support: <a href="mailto:qinetraian@gmail.com">qinetraian@gmail.com</a></p>
        <p>Keep passwords, recovery keys and customer records out of support messages.</p>
      </footer>
    </div>
  );
}
