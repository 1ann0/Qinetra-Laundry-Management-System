# Frontend dependency patch verification

Updated 28 September 2026. Local evidence only; no production deployment.

## Change and boundary

- `frontend/package.json` and its lockfile move Next.js and eslint-config-next from 16.2.10 to 16.3.6. React and React DOM remain 19.2.4.
- Compatible lockfile fixes were applied without `npm audit fix --force`. No authentication, pricing or database behavior was changed by this patch.
- The older customer-contact backend draft and migration 020 are separate unfinished work and must not enter the dependency commit.
- [Next.js release](https://github.com/vercel/next.js/releases/tag/v16.3.6), [Windows vulnerability advisory](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36), [image optimization advisory](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4).

## Automated evidence

Recorded during the approved patch on 26 September, using Node 24.11.0 and npm 11.18.0:

| Check | Result |
| --- | --- |
| npm audit before patch | 8 affected packages: 1 critical, 6 high, 1 moderate; includes development dependencies |
| npm audit after compatible fixes | 0 reported vulnerabilities across 351 packages |
| npm test | 50 passed; no failures or skips |
| npm run lint | Passed |
| npm run build | Passed with Next.js 16.3.6 |
| git diff --check | Passed; existing line-ending notices only |

These are dated results, not a guarantee against future advisories. A dependency audit does not certify the application's security. The package-manager warning about the unapproved unrs-resolver postinstall was not bypassed; lint/build completed without blanket script approval.

## Browser evidence, 27–28 September

Used the local production build at `http://127.0.0.1:3100` and the disposable in-memory API at port 8000, never the shop database. Fixture account names are nav_owner and nav_employee; credentials remain in the ignored fixture script.

- Owner fresh login displayed Finance: one fictional order, KES 750 booked, KES 0 received, KES 750 outstanding.
- Direct receipt QL-NAV-TEST-001 loaded and survived refresh. It retained the three previous quantity corrections and exactly one `lost reply test` event. This is a read check, not a rerun of the September 25 lost-reply acceptance.
- Logout cleared the session; employee login showed only operational navigation. A direct `/finance` visit redirected to `/workspace`.
- Employee phone search for 0700000000 returned exactly Navigation test customer.
- Employee inactivity reauthentication preserved the search and its result on 28 September.
- Receipt loading also intermittently displayed QLMS-CONNECTION, including after reauthentication. Fresh owner login and a later refresh succeeded. Individual authenticated fixture endpoints returned HTTP 200 and the expected CORS origin. The fixture's earlier log contains a SQLite shared-connection InterfaceError; that historical entry does not prove the cause of every new failure. Employee receipt/reauthentication acceptance is not a clean pass yet.

### Fresh fixture follow-up, 28 September

Preserved the old fictional receipt as `tmp/fictional-receipt-before-patch-fixture.json`, then replaced only the verified disposable API process. `tmp/security-patch-fixture.py` uses a temporary SQLite file and separate pooled connections instead of sharing one StaticPool connection across concurrent requests. Neither helper nor fixture data belongs in the release.

- Fresh employee login and first direct receipt load passed. All three receipt/lookup requests returned 200; no server exception appeared in the fresh fixture log.
- Employee receipt showed the new fixture's 2 kg / KES 300 order and no owner correction controls.
- Recorded one fictional KES 100 cash payment through the browser. Refresh preserved exactly one payment, KES 100 paid and KES 200 balance. No pending-save notice remained.
- The old fixture's in-memory data is no longer live; earlier three-correction acceptance evidence remains historical. New manual checks must use the current fixture values, not expect the old KES 750 receipt.

The ordinary patch smoke now passes on the fresh fixture. This narrows the earlier problem to investigate, but does not prove every interrupted-login/old-tab path safe. Keep those scenarios in S1c/C3 and verify against PostgreSQL before release. No new screenshot was added for an invisible dependency change; existing screenshots remain historical evidence.

## Repeatable manual check

1. Verify the fresh `tmp/security-patch-fixture.py` API is on 8000 and the built frontend uses that address. Do not substitute a production DATABASE_URL. This fixture does not simulate lost replies; use the dedicated earlier fixture for that scenario.
2. Sign in as the fixture owner; compare Finance against the current fictional receipt. Open `/orders/1`, refresh and compare ticket, amounts and correction count.
3. Log out; sign in as nav_employee. Visit `/finance` directly: expect Home and no owner Finance content.
4. Search the fictional phone and open its order history/receipt. Expect the right customer and no owner correction form. The currently running fresh fixture has KES 300 total, KES 100 paid, KES 200 balance and one payment. Do not record another KES 100 merely to reproduce the existing evidence.
5. After an inactivity lock, reauthenticate and retry the original read without losing the search/draft. Record any first-load failure separately from a successful refresh.

Student explain-back: why does a passing dependency audit not prove that refunds, permissions or recovery are correct?

## Release boundary

The dependency change is ready to isolate locally. A production release still requires the [pilot gates](../IMPLEMENTATION_ROADMAP.md), session-recovery review, a known backend/frontend pair and the approved cutover. No hosting purchase, database migration, push or deployment belongs to this patch.
