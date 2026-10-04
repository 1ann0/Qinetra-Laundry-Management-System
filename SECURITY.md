# QLMS security boundaries and release checks

Reviewed 28 September 2026. This is a control inventory and implementation contract, not a security certification. Findings and tests belong in [the premortem](docs/pilot-premortem.md) and the relevant check record.

## Trust boundaries

The browser is untrusted input, even for a signed-in owner. FastAPI must validate current identity, permission, record state, fields and amounts. The database is reachable only through server credentials; Supabase's public/authenticated roles are not the application's custom JWT authority.

Protect customer contacts/history, money records, credentials, exports and backups. Shared shop devices need individual sign-in, inactivity lock, logout and safe user switching. Debugging must not print tokens, password hashes, connection strings or customer payloads into public logs.

## Current and required controls

| Area | Current evidence | Required before the affected release |
| --- | --- | --- |
| Authentication | bcrypt; expiring signed JWT; database active-role/version checks | Safe login password bounds, generic errors, throttling, invalid/disabled/revoked-session tests |
| Sessions | sessionStorage token, inactivity lock and refresh | Review script-readable-token risk; resolve first-load/reauthentication findings; prove logout, old-tab and user-switch behavior |
| Authorization | Backend owner/staff dependencies; whole-order employee discount ceiling locally verified 4 October | Keep direct-route/field-tampering checks for other actions; trim excess responses; complete student/release acceptance |
| Queries/input | SQLAlchemy/bound queries and Pydantic | Finite/range/size limits and stale/terminal-state tests; no client-controlled role, actor or saved rate |
| Money/saves | Transactions, correction history, pending-save references | Truthful refunds and PostgreSQL concurrency/replay acceptance; never auto-repeat an uncertain payment |
| Browser output/export | React text rendering and CSV writer | Spreadsheet formula neutralization for untrusted text, numeric money preserved; receipt/internal-note separation |
| Transport/cache | Configurable API origin and CORS | Verify production TLS/HTTPS, explicit origins, suitable CSP/headers and no public caching of authenticated responses |
| Database | Dated browser-role denial observations in the handover | Separate real-data project, restricted runtime role, migration separation and verified restore |
| Dependencies/secrets | Local frontend patch evidence | Current/history redacted secret scan, Python audit, credential-rotation evidence and repeatable maintenance checks |

The [dependency patch record](docs/security-patch-check.md) records the exact versions and limits of its audit/browser evidence. Zero dependency findings do not prove all rows above pass.

The [discount check record](docs/discount-policy-check.md) verifies authenticated reads, owner-only changes/history, disabled/revoked accounts, rejected extra policy fields, whole-order decimal limits and PostgreSQL update/order serialization. Migration 022 enables RLS and revokes public/browser-role table and history-sequence access; restricted runtime access still needs D1 qualification. Policy reads request no-store in the frontend; this does not complete the API-wide private-response/header work in S1b. Neither passing these checks nor founder access permits exporting another client's personal data to an AI provider without the separately reviewed purpose/access/privacy safeguards.

## Credentials and incidents

Keep secrets in backend/provider configuration, never NEXT_PUBLIC variables or source. A public API URL and a later Google client ID are not database credentials. Do not add a browser database key merely to satisfy a generic checklist.

For a suspected exposed credential, contain and rotate/revoke it, assess affected access, then verify service recovery. History removal needs coordinated review because rewriting shared history is disruptive and does not invalidate a stolen key. Record redacted identifiers/evidence only.

For data or money discrepancies, stop affected writes, preserve audit records and reconcile actual events. Restore only through the reviewed data procedure. The owner/support contact and alert route must be confirmed before the trial.

## Deliberately later controls

- Secure HttpOnly/Secure cookie sessions require an agreed same-origin/CSRF design; implement them before Google sign-in. Do not silently bolt cookies onto the existing cross-origin API.
- Google sign-in verifies identity and links only approved accounts; existing FastAPI roles/revocation still govern access. Keep a safe owner recovery path.
- Bot challenges follow demonstrated abuse and throttling, with server verification; do not challenge ordinary saves.
- Uploads are not an approved feature. Before adding them, define authenticated access, size/type/content checks, generated storage names and safe delivery.
- Field encryption needs a specific data threat and recoverable key design. Avoid making ordinary customer search unusable through unplanned encryption.
- WAF rules cannot replace authorization, backups or money correctness. Qualify Cloudflare with no customer-response caching and preserve uncertain-save handling through proxy failures.

Before multi-business operation, test hostile cross-business IDs, linked records, exports, background jobs and callbacks. Platform support access must be time-limited, approved and audited; it is not default access to all customer records.
