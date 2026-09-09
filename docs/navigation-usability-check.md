# Daily navigation: review checklist

Implemented locally on 9 September 2026. Not deployed. Frontend lint and the production build passed; browser interaction, screenshots and an unfamiliar-user session are still pending. The browser tool timed out, so there is no claimed visual verification.

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

- `34-employee-home-navigation.png`: employee Home, all three primary shortcuts, Add customer and the four sidebar entries.
- `35-employee-track-orders-navigation.png`: Track orders selected, the Track orders title and the temporary test order visible.

Label these as local production-build evidence using isolated test data. They do not prove deployment or real customer activity. Update `docs/evidence-tracker.md` only after the files exist and match the checked behaviour.

Use Windows Snipping Tool (`Win+Shift+S`) to capture the browser view. Include the complete page title, sidebar and relevant actions at a readable size, then save the PNG with the name above. Avoid capturing passwords or unrelated windows. Capture a changed behaviour worth explaining, not every intermediate screen.

Learning check: in your own words, explain why `/orders` highlights New order while `/orders/1` highlights Track orders even after a refresh.
