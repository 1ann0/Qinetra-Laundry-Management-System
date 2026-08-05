"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import PageTour from "@/components/layout/page-tour";
import { useAuth } from "@/context/auth-context";

const PAGE_TITLES = {
  "/finance": "Finance",
  "/workspace": "Workspace",
  "/customers": "Customers",
  "/orders": "Orders",
  "/dashboard": "Dashboard",
  "/settings": "Shop setup",
};

function NavigationIcon({ name }) {
  const paths = {
    finance: <path d="M4 19V9m5 10V5m5 14v-7m5 7V3M2 21h20" />,
    workspace: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    customers: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      </>
    ),
    orders: (
      <>
        <path d="M6 2h9l5 5v15H6z" />
        <path d="M14 2v6h6M9 13h8M9 17h8" />
      </>
    ),
    dashboard: (
      <>
        <path d="M3 3v18h18" />
        <path d="m7 15 4-4 3 3 5-6" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V21h-4v-.08A1.7 1.7 0 0 0 8.97 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15 1.7 1.7 0 0 0 3.08 14H3v-4h.08A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.34-1.88L4.2 7.06l2.83-2.83.06.06A1.7 1.7 0 0 0 8.97 4.6 1.7 1.7 0 0 0 10 3.08V3h4v.08A1.7 1.7 0 0 0 15.03 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9 1.7 1.7 0 0 0 20.92 10H21v4h-.08A1.7 1.7 0 0 0 19.4 15Z" />
      </>
    ),
  };

  return (
    <svg
      aria-hidden="true"
      className="nav-icon"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    >
      {paths[name]}
    </svg>
  );
}

// Display the protected pages with navigation shared by every signed-in user.
export default function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { role, logout } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);
  const [isMobileNavigation, setIsMobileNavigation] = useState(false);

  // Keep the main module highlighted while the user is on one of its related pages.
  const isWorkspacePage = pathname === "/workspace";
  const isCustomersPage = pathname.startsWith("/customers");
  const isOrdersPage = pathname.startsWith("/orders");
  const isDashboardPage = pathname === "/dashboard";
  const isFinancePage = pathname.startsWith("/finance");
  const isSettingsPage = pathname.startsWith("/settings");
  const homeHref = role === "owner" ? "/finance" : "/workspace";
  const pageTitle =
    Object.entries(PAGE_TITLES).find(([path]) => pathname.startsWith(path))?.[1] ||
    "QLMS";
  const navigationItems = [
    ...(role === "owner"
      ? [{ href: "/finance", label: "Finance", icon: "finance", active: isFinancePage }]
      : []),
    { href: "/workspace", label: "Workspace", icon: "workspace", active: isWorkspacePage },
    { href: "/customers", label: "Customers", icon: "customers", active: isCustomersPage },
    { href: "/orders", label: "Orders", icon: "orders", active: isOrdersPage },
    ...(role === "owner"
      ? [
          { href: "/dashboard", label: "Dashboard", icon: "dashboard", active: isDashboardPage },
          { href: "/settings/catalog", label: "Shop setup", icon: "settings", active: isSettingsPage },
        ]
      : []),
  ];

  useEffect(() => {
    const mobileNavigationQuery = window.matchMedia("(max-width: 900px)");
    const savedPreferenceTimer = window.setTimeout(() => {
      setSidebarCollapsed(
        window.localStorage.getItem("qlms-sidebar-collapsed") === "true",
      );
      setIsMobileNavigation(mobileNavigationQuery.matches);
    }, 0);

    function updateNavigationMode(event) {
      setIsMobileNavigation(event.matches);
      setMobileNavigationOpen(false);
    }

    mobileNavigationQuery.addEventListener("change", updateNavigationMode);

    return () => {
      window.clearTimeout(savedPreferenceTimer);
      mobileNavigationQuery.removeEventListener("change", updateNavigationMode);
    };
  }, []);

  function toggleSidebar() {
    if (isMobileNavigation) {
      setMobileNavigationOpen((current) => !current);
      return;
    }

    setSidebarCollapsed((current) => {
      const nextValue = !current;
      window.localStorage.setItem(
        "qlms-sidebar-collapsed",
        String(nextValue),
      );
      return nextValue;
    });
  }

  // Clear the saved session before returning the user to the login page.
  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div
      className={`app-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}
    >
      <aside
        className={`app-sidebar ${mobileNavigationOpen ? "sidebar-open" : ""}`}
      >
        <Link className="sidebar-brand" href={homeHref} aria-label="QLMS home">
          <Image
            className="header-logo"
            src="/qinetra-logo.jpg"
            alt="Qinetra Laundry"
            width={1600}
            height={942}
            priority
          />
          <span className="sidebar-mark" aria-hidden="true">
            Q
          </span>
        </Link>

        <nav className="app-nav" aria-label="Main navigation">
          {navigationItems.map((item) => (
            <Link
              href={item.href}
              aria-current={item.active ? "page" : undefined}
              aria-label={sidebarCollapsed ? item.label : undefined}
              title={sidebarCollapsed ? item.label : undefined}
              key={item.href}
              onClick={() => setMobileNavigationOpen(false)}
            >
              <NavigationIcon name={item.icon} />
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      {mobileNavigationOpen ? (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileNavigationOpen(false)}
        />
      ) : null}

      <div className="app-content">
        <header className="app-header">
          <div className="topbar-heading">
            <button
              className="navigation-toggle"
              type="button"
              aria-label={
                isMobileNavigation
                  ? mobileNavigationOpen
                    ? "Close navigation"
                    : "Open navigation"
                  : sidebarCollapsed
                    ? "Expand navigation"
                    : "Collapse navigation"
              }
              aria-expanded={
                isMobileNavigation ? mobileNavigationOpen : !sidebarCollapsed
              }
              onClick={toggleSidebar}
            >
              <svg
                aria-hidden="true"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <p>Qinetra Laundry</p>
              <strong>{pageTitle}</strong>
            </div>
          </div>

          <div className="session-controls">
            <PageTour key={pathname} pathname={pathname} />
            <span className="role-badge">{role}</span>
            <button
              className="secondary-button logout-button"
              type="button"
              onClick={handleLogout}
            >
              Log out
            </button>
          </div>
        </header>

        <main className={`app-main ${isWorkspacePage ? "workspace-main" : ""}`}>
          {children}
        </main>
      </div>
    </div>
  );
}
