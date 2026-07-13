"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function AppShell({ children }) {
  const router = useRouter();
  const { role, logout } = useAuth();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link href="/workspace" aria-label="QLMS workspace">
          <Image
            className="header-logo"
            src="/qinetra-logo.jpg"
            alt="Qinetra Laundry"
            width={1600}
            height={942}
            priority
          />
        </Link>

        <nav className="app-nav" aria-label="Main navigation">
          <Link href="/workspace">Workspace</Link>
          <Link href="/customers">Customers</Link>
          {role === "owner" ? <Link href="/dashboard">Dashboard</Link> : null}
        </nav>

        <div className="session-controls">
          <span className="role-badge">{role}</span>
          <button className="secondary-button" type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      <main className="app-main">{children}</main>
    </div>
  );
}
