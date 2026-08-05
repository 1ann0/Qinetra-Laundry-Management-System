"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

// Display the protected pages with navigation shared by every signed-in user.
export default function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { role, logout } = useAuth();

  // Keep the main module highlighted while the user is on one of its related pages.
  const isWorkspacePage = pathname === "/workspace";
  const isCustomersPage = pathname.startsWith("/customers");
  const isOrdersPage = pathname.startsWith("/orders");
  const isDashboardPage = pathname === "/dashboard";
  const isFinancePage = pathname.startsWith("/finance");
  const isSettingsPage = pathname.startsWith("/settings");
  const homeHref = role === "owner" ? "/finance" : "/workspace";

  // Clear the saved session before returning the user to the login page.
  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link href={homeHref} aria-label="QLMS home">
          <Image
            className="header-logo"
            src="/qinetra-logo.jpg"
            alt="Qinetra Laundry"
            width={1600}
            height={942}
            priority
          />
        </Link>

        <nav className="app-nav flex-wrap" aria-label="Main navigation">
          {role === "owner" ? (
            <Link
              href="/finance"
              aria-current={isFinancePage ? "page" : undefined}
            >
              Finance
            </Link>
          ) : null}
          <Link
            href="/workspace"
            aria-current={isWorkspacePage ? "page" : undefined}
          >
            Workspace
          </Link>
          <Link
            href="/customers"
            aria-current={isCustomersPage ? "page" : undefined}
          >
            Customers
          </Link>
          <Link
            href="/orders"
            aria-current={isOrdersPage ? "page" : undefined}
          >
            Orders
          </Link>
          {role === "owner" ? (
            <>
              <Link
                href="/dashboard"
                aria-current={isDashboardPage ? "page" : undefined}
              >
                Dashboard
              </Link>
              <Link
                href="/settings/catalog"
                aria-current={isSettingsPage ? "page" : undefined}
              >
                Shop setup
              </Link>
            </>
          ) : null}
        </nav>

        <div className="session-controls">
          <span className="role-badge">{role}</span>
          <button className="secondary-button" type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      <main className={`app-main ${isWorkspacePage ? "workspace-main" : ""}`}>
        {children}
      </main>
    </div>
  );
}
