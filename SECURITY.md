# QLMS security boundaries and release checks

Updated 5 October 2026. This is a control inventory and implementation contract, not a security certification. [Current essentials evidence](docs/pilot-essentials-check.md) records the shared login throttle, safe password/body bounds, generic failures, formula-safe CSV, private API/browser headers, sanitized errors, explicit production schema/role/TLS checks and session recovery. The inventory below retains launch requirements; local implementation does not prove deployed configuration. Findings belong in [the premortem](docs/pilot-premortem.md) and relevant check records.

## Trust boundaries

The browser is untrusted input, even for a signed-in owner. FastAPI must validate current identity, permission, record state, fields and amounts. The database is reachable only through server credentials; Supabase's public/authenticated roles are not the application's custom JWT authority.

Protect customer contacts/history, money records, credentials, exports and backups. Shared shop devices need individual sign-in, inactivity lock, logout and safe user switching. Debugging must not print tokens, password hashes, connection strings or customer payloads into public logs.

## Current and required controls

| Area | Current evidence | Required before the affected release |
| --- | --- | --- |
| Authentication | bcrypt/72-byte boundary; expiring JWT; active-role/version checks; generic failures, bounded body and shared PostgreSQL throttling tested locally | Verify deployed trusted peer IP behavior and actual credentials; retain disabled/revoked-session coverage |
| Sessions | sessionStorage token, inactivity lock/refresh; expired-receipt and pending-payment recovery, same-account logout and different-owner isolation passed locally | Script-readable tokens remain; global token logout and secure cookies are later work; complete final staff acceptance |
| Authorization | Backend owner/staff dependencies; whole-order employee discount ceiling locally verified 4 October | Keep direct-route/field-tampering checks for other actions; trim excess responses; complete student/release acceptance |
| Queries/input | SQLAlchemy/bound queries and Pydantic | Finite/range/size limits and stale/terminal-state tests; no client-controlled role, actor or saved rate |
| Money/saves | Transactions, correction history, pending-save references | Truthful refunds and PostgreSQL concurrency/replay acceptance; never auto-repeat an uncertain payment |
| Browser output/export | React text rendering; formula-neutralized text CSV and unchanged numeric money tested locally | Retain receipt/internal-note separation and final staff CSV reconciliation |
| Transport/cache | Configurable API/CORS; API/browser private cache and security headers locally verified | Verify deployed TLS/HTTPS, explicit origins, proxy handling and no public caching; disable query-string access logs |
| Database | Separate empty project, 20 RLS tables, denied browser schema usage; restricted runtime/backup NOLOGIN roles; local restore/rights verified | Resolve limited clothing grant approval, actual credentials/connections and operational backup/restore |
| Dependencies/secrets | Current redacted history/staged scans and Python/production npm audits; unpatched development braces advisory recorded | Confirm old credential rotation, use new pilot credentials and maintain repeatable checks; no whole-system clearance |

The [dependency patch record](docs/security-patch-check.md) records historical patch evidence. Current production npm and pinned Python/operations audits report zero findings; full npm has an unpatched development-only braces advisory. A redacted history scan found reviewed test-variable references, without proving prior credential rotation. Never reuse old credentials for the new pilot. Zero findings do not prove every control passes.

The [discount check record](docs/discount-policy-check.md) verifies authenticated reads, owner-only changes/history, disabled/revoked accounts, rejected extra policy fields, whole-order decimal limits and PostgreSQL update/order serialization. The new pilot has RLS on all 20 tables and browser schema denial. Restricted-role correction/payment/refund/restore checks passed locally; the remote clothing replacement permission needs explicit approval, and actual connections remain unconfigured. API-wide no-store/header controls now pass locally. Neither passing checks nor founder access permits another client's personal-data transfer to AI without reviewed purpose/access/privacy safeguards.

Same-account logout propagates within supporting browsers without transmitting tokens. It does not revoke server tokens globally; separate devices and browsers without BroadcastChannel need explicit logout. Protected-page initialization and receipt reauthentication preserve drafts; late responses from another identity cannot populate the page. Script-readable session tokens and inline hydration CSP remain residual risks until the separate cookie/nonce increment. Before release, verify trusted proxy IP/HTTPS handling and disable Uvicorn access logs containing query strings (`--no-access-log`).

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

The creator requested system administration, not a second shop-owner identity. Current QLMS roles remain Owner/Employee; technical operations use the creator's private provider/repository accounts. A later maintenance interface needs separate server-side authorization, safe operational status, bounded actions and an audit trail. Keep secrets and arbitrary SQL/code execution out of that browser interface. Access to business records requires its own approved scope.
