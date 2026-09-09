# Daily navigation: review checklist

Implemented locally on 9 September 2026. Not deployed. The navigation phase passed lint and the production build. Image 34 was supplied by the user and inspected: it shows Home shortcuts with the menu closed. Browser interaction and an unfamiliar-user session remain pending.

Start with [the development journal](../DEVELOPMENT_JOURNAL.md) for the change history and LinkedIn ideas. The feedback follow-up adds clearer stage buttons and plain error messages. Its sixteen request/message tests passed; final checks are recorded below.

HTTP checks confirmed the local frontend and fixture API respond, both test accounts can sign in and read the fixture order, and employees receive 403 from account management, dashboard summary, finance summary and report export endpoints. These checks do not replace the browser checks below.

## Open the isolated review site

Use [local QLMS](http://127.0.0.1:3100) on this computer. The review API uses temporary in-memory SQLite records, separate from Qinetra's Supabase database.

| Role | Username | Password |
| --- | --- | --- |
| Employee | `nav_employee` | `NavTest123!` |
| Owner | `nav_owner` | `NavTest123!` |

These are disposable local test accounts only. The saved test order is `QL-NAV-TEST-001`. Restarting the fixture API resets its records.

If the site is unavailable, open the QLMS folder in Antigravity and start the following commands in two integrated PowerShell terminals from the project root. Keep both terminals open. The current frontend production build was compiled for the fixture API at port 8100.

Terminal 1:

```powershell
.\backend\venv\Scripts\python.exe .\tmp\usability-nav-server.py
```

Terminal 2:

```powershell
Set-Location frontend
node .\node_modules\next\dist\bin\next start --hostname 127.0.0.1 --port 3100
```

The fixture script is an ignored local helper, not part of the deployed application. Do not use real customer information for this session.

## Check the employee workflow

Do not use Page tour for these checks. No order needs to be created or advanced to check navigation.

| Action | Expected result |
| --- | --- |
| Sign in as the employee | Home opens. Sidebar shows Home, New order, Track orders and Customers. No Finance, Dashboard, Staff or Shop setup links. |
| Use each of the three Home shortcuts | New order opens `/orders`; Track orders opens `/orders/status`; Find customer opens `/customers/search`. Each has a short explanation on Home. |
| Select Customers in the sidebar | Customer search opens, not registration. From Home, Add customer beside Find customer opens `/customers`. |
| Visit New order, tracking, customer search and registration | Topbar titles are New order, Track orders, Find customer and Add customer respectively. Only one sidebar destination is highlighted. Both customer screens highlight Customers. |
| Open the test order from tracking; also open `/orders/1` directly | Topbar says Order details; Track orders alone remains highlighted. |
| Refresh each destination and use browser Back | URL, page title and highlighted destination continue to agree. |
| Collapse the desktop sidebar | Icons retain understandable names on hover. All four destinations still work. Expand the sidebar again. |
| Press Tab and Shift+Tab; activate links with Enter | Every navigation item and Home action is reachable, with a visible focus outline. |
| Narrow the browser window below 900 px, or use browser device emulation | Open navigation, then choose Track orders. The menu closes and tracking opens. Open navigation adds one step; no extra submenu is required. Closed menu links are skipped when tabbing. Descriptions remain visible on Home. |
| Enter `/finance`, `/dashboard`, `/staff`, `/settings/catalog` directly while signed in as employee | Each redirects to Home without displaying owner records or account controls. |

Then log out and sign in as the owner. Finance should open first. Confirm the same four daily-work links exist alongside Finance, Dashboard, Staff and Shop setup. Open Home and confirm owner shortcuts remain available.

## Test with someone unfamiliar with QLMS

Start them on employee Home. Do not coach them or open Page tour. Ask them to find where they would (1) enter a new laundry order, (2) check an existing order's progress, and (3) find a returning customer. Ask them to stop once they reach the right screen.

| Task | Time taken | First selection | Hesitation or wrong selections | Completed unaided? |
| --- | --- | --- | --- | --- |
| Enter a new order | Pending | Pending | Pending | Pending |
| Track an existing order | Pending | Pending | Pending | Pending |
| Find a returning customer | Pending | Pending | Pending | Pending |

Record their words and actions before describing the navigation as intuitive. Note the browser/device and date. If they struggle, record the problem rather than explaining the intended path during the task.

## Capture genuine evidence

After the checks pass, save screenshots under `docs/diagrams/evidence/`:

This is the existing screenshot folder inspected for this phase; there is no folder literally named `screenshot` in this checkout. Existing captures run through number 29, with later numbers already reserved in the tracker. Keep earlier evidence intact and continue the numbered naming convention.

- `34-employee-home-navigation.png`: already captured and inspected. It shows Home shortcuts and Add customer. Keep it; do not retake it just to add an open sidebar.
- `35-employee-track-orders-navigation.png`: pending. Select Received so the stage says Showing these orders. Include its matching test order and the other View orders buttons. This proves a distinct interaction, not another general page view.

Label these as local production-build evidence using isolated test data. They do not prove deployment or real customer activity. Update `docs/evidence-tracker.md` only after the files exist and match the checked behaviour.

Use Windows Snipping Tool (`Win+Shift+S`) to capture the browser view. Include the complete page title, sidebar and relevant actions at a readable size, then save the PNG with the name above. Avoid capturing passwords or unrelated windows. Capture a changed behaviour worth explaining, not every intermediate screen.

Learning correction: `/orders` opens order entry. `/orders/1` opens the saved order with database ID 1. The ID does not reset daily and does not mean the first order of the day.

## Feedback follow-up: stages and messages

1. Open Track orders as `nav_employee`.
2. Without Page tour, select View orders under Received.
3. Confirm that the selected button says Showing these orders. Check that only received orders appear below.
4. Select a stage with no orders. Confirm that No orders found appears only after a successful load.
5. Select View all orders. Confirm that all matching orders return.
6. Use Tab and Enter to select stages. Check the visible focus outline and selected label.
7. Narrow the browser window. Check that each stage still has a readable action and order count.
8. Log out. Enter an incorrect password for the local employee account. Expect a username/password instruction and QLMS-SIGNIN.
9. Open browser developer tools with F12. In Network, select Offline after the login page has loaded.
10. Attempt to sign in. Expect connection advice and QLMS-CONNECTION. The button must stop showing a waiting state.
11. Restore No throttling in Network. Sign in with the correct local password.
12. With Track orders open, select Offline again and submit a search. Expect a load-failure message and Try loading orders again.
13. Restore No throttling. Select Try loading orders again. Confirm that the fixture orders return.

Keep these outage tests on the local review site. They do not require changing Render, Supabase or the production site's availability.
Do not test duplicate payments by submitting repeatedly. Automated tests check that failures never trigger an automatic second save.

An optional `36-connection-support-message.png` can show the single local simulated connection failure. Label it as a simulation.
Skip it if the written example already tells the story. Do not capture the same message on multiple pages.

Ask an unfamiliar user to show only orders that are ready for collection. Record their first selection and any hesitation.
Do not explain that the stage cards are buttons until the attempt is over.

### Verification record

- Request/message tests: 16 passed using Node's test runner; no new test library.
- Source commit: `01a2fa3`, local only. The review server at port 3100 was rebuilt and restarted with these changes.
- Read-only fixture checks: both role logins, order/customer reads, owner CSV/finance, employee 403 restrictions and wrong-password 401 advice passed.
- Automated coverage: transport errors, deadlines, uncertain saves, JSON replies, sign-in status, role errors, validation and CSV exports.
- Lint/build for the feedback follow-up: both passed, including the final payment-warning correction.
- Hands-on stage filtering, keyboard, mobile and outage recovery: pending student checks above.
- New screenshots: none generated by the assistant; image 34 supplied by the user is preserved.
