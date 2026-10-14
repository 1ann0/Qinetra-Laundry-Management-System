"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import SessionReauthenticationDialog from "@/components/auth/session-reauth-dialog";
import PageTour from "@/components/layout/page-tour";
import { useAuth } from "@/context/auth-context";

const PAGE_TITLES = {
  "/finance": "Finance",
  "/workspace": "Home",
  "/customers": "Add customer",
  "/customers/search": "Find customer",
  "/customers/contact": "Customer contact details",
  "/orders": "New order",
  "/orders/status": "Track orders",
  "/orders/receipt": "Order receipt",
  "/dashboard": "Dashboard",
  "/reports": "Reports",
  "/staff": "Staff",
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
    tracking: (
      <>
        <circle cx="5" cy="5" r="2" />
        <circle cx="5" cy="12" r="2" />
        <circle cx="5" cy="19" r="2" />
        <path d="M5 7v3m0 4v3M11 5h10M11 12h10M11 19h10" />
      </>
    ),
    dashboard: (
      <>
        <path d="M3 3v18h18" />
        <path d="m7 15 4-4 3 3 5-6" />
      </>
    ),
    staff: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M17 11.5 19 13l3-3.5M19.5 6.5l2.5 1v2.4c0 2.1-1 3.9-2.5 4.6-1.5-.7-2.5-2.5-2.5-4.6V7.5z" />
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
  const { role, idleExpiresAt, reauthenticationRequired, hasOpenedSession, logout } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);
  const [isMobileNavigation, setIsMobileNavigation] = useState(false);
  const [warningIdleExpiry, setWarningIdleExpiry] = useState(null);
  const menuRef = useRef(null);
  const menuButtonRef = useRef(null);

  // Creating an order and following saved orders are separate daily tasks.
  const isWorkspacePage = pathname === "/workspace";
  const isCustomersPage = pathname.startsWith("/customers");
  const isNewOrderPage = pathname === "/orders";
  const isTrackingPage = pathname.startsWith("/orders/");
  const isDashboardPage = pathname === "/dashboard";
  const isFinancePage = pathname.startsWith("/finance");
  const isStaffPage = pathname.startsWith("/staff");
  const isSettingsPage = pathname.startsWith("/settings");
  const homeHref = role === "owner" ? "/dashboard" : "/workspace";
  const pageTitle = PAGE_TITLES[pathname] || (
    isTrackingPage ? "Order details" : isSettingsPage ? "Shop setup" : "QLMS"
  );
  const sidebarHidden = reauthenticationRequired || (
    isMobileNavigation && !mobileNavigationOpen
  );
  const sessionEndingSoon = Boolean(
    idleExpiresAt && warningIdleExpiry === idleExpiresAt,
  );
  const navigationItems = [
    ...(role === "owner"
      ? [{ href: "/dashboard", label: "Dashboard", icon: "dashboard", active: isDashboardPage },
         { href: "/finance", label: "Finance", icon: "finance", active: isFinancePage }]
      : []),
    { href: "/workspace", label: "Home", icon: "workspace", active: isWorkspacePage },
    { href: "/orders", label: "New order", icon: "orders", active: isNewOrderPage },
    { href: "/orders/status", label: "Track orders", icon: "tracking", active: isTrackingPage },
    { href: "/customers/search", label: "Customers", icon: "customers", active: isCustomersPage },
    ...(role === "owner"
      ? [
          { href: "/reports", label: "Reports", icon: "orders", active: pathname === "/reports" },
          { href: "/staff", label: "Staff", icon: "staff", active: isStaffPage },
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

  useEffect(() => {
    if (!idleExpiresAt) {
      return undefined;
    }

    const warningDelay = idleExpiresAt - Date.now() - 2 * 60 * 1000;
    const warningTimer = window.setTimeout(
      () => setWarningIdleExpiry(idleExpiresAt),
      Math.max(warningDelay, 0),
    );
    return () => window.clearTimeout(warningTimer);
  }, [idleExpiresAt]);

  useEffect(() => {
    if (!isMobileNavigation || !mobileNavigationOpen || reauthenticationRequired) return undefined;
    const menu = menuRef.current;
    const menuButton = menuButtonRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    menu?.querySelector("button, a[href]")?.focus();
    function handleMenuKey(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobileNavigationOpen(false);
      } else if (event.key === "Tab") {
        const controls = menu?.querySelectorAll("button, a[href]");
        if (!controls?.length) return;
        const first = controls[0], last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    }
    document.addEventListener("keydown", handleMenuKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleMenuKey);
      menuButton?.focus({ preventScroll: true });
    };
  }, [isMobileNavigation, mobileNavigationOpen, reauthenticationRequired]);

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
      <a className="skip-link" href="#main-content">Skip to page content</a>
      <aside
        ref={menuRef}
        role={isMobileNavigation && mobileNavigationOpen ? "dialog" : undefined}
        aria-modal={isMobileNavigation && mobileNavigationOpen ? true : undefined}
        aria-label={isMobileNavigation && mobileNavigationOpen ? "Main menu" : undefined}
        className={`app-sidebar ${mobileNavigationOpen ? "sidebar-open" : ""}`}
        inert={sidebarHidden ? true : undefined}
        aria-hidden={sidebarHidden || undefined}
      >
        {isMobileNavigation && mobileNavigationOpen ? <button className="secondary-button mb-4 min-h-11" type="button" onClick={() => setMobileNavigationOpen(false)}>Close menu</button> : null}
        <Link className="sidebar-brand" href={homeHref} aria-label="QLMS home">
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

      <div
        className="app-content"
        inert={reauthenticationRequired || (isMobileNavigation && mobileNavigationOpen) ? true : undefined}
        aria-hidden={reauthenticationRequired || (isMobileNavigation && mobileNavigationOpen) || undefined}
      >
        <header className="app-header">
          <div className="topbar-heading">
            <button
              ref={menuButtonRef}
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
            <Link className="secondary-button inline-flex min-h-11 items-center no-underline" href="/workspace#quick-find">Find</Link>
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

        {sessionEndingSoon ? (
          <p
            className="m-0 border-b border-amber-300 bg-amber-50 px-4 py-2 text-center text-sm font-semibold text-amber-900"
            role="status"
          >
            No activity has been detected recently. QLMS will pause in less
            than 2 minutes unless you continue working.
          </p>
        ) : null}

        <main id="main-content" tabIndex="-1" className={`app-main ${isWorkspacePage ? "workspace-main" : ""}`}>
          {hasOpenedSession ? children : <p role="status">Enter your password to open this page.</p>}
        </main>
      </div>
      {reauthenticationRequired ? <SessionReauthenticationDialog /> : null}
    </div>
  );
}
