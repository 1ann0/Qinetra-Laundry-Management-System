# Creator operations — QLMS

5 October 2026. The creator requested control of the software itself. Caroline's Owner account manages the laundry; it is not the technical-maintenance account. Current QLMS supports Owner/Employee only (`backend/schemas.py`, `backend/auth.py`). No platform-admin console has been built.

## Use the existing control panels now

| Private account/control panel | Purpose |
|---|---|
| [GitHub repository](https://github.com/1ann0/Qinetra-Laundry-Management-System) | Review source changes and the exact version being released. |
| [Render dashboard](https://dashboard.render.com/) | Backend releases, process health, logs and private server configuration. |
| [Supabase pilot project](https://supabase.com/dashboard/project/istweeaqtykwfuhntgik) | Pilot database configuration and restricted runtime/backup roles. |
| [Vercel dashboard](https://vercel.com/dashboard) | Current frontend deployment/configuration; verify actual plan eligibility before the business pilot. Cloudflare remains a separately qualified alternative. |
| Private backup storage and operations tools | Independent encrypted copies, recoverable key and restore evidence. They are not yet configured for daily operation. |

Use your own provider identities. Don't share Caroline's password to manage releases. Do not move provider secrets into frontend variables or a shop settings form. Keep role grants, actual backup storage and release changes within their reviewed scope.

## Operating checks

- Before opening for work: verify the confirmed frontend/backend release pair, usable database, latest verified independent backup and alerts. The current readiness route is implemented locally; it has not been released to the old public backend.
- Investigate errors through sanitized logs. A page loading or process running does not prove that orders can be retrieved/saved.
- Record corrections through supported application workflows, preserving history. Technical access must not become routine deletion or direct rewriting of money records.
- Develop changes against fictional records. Release tested compatible changes; restore into a separate target before reconciling or switching. Do not roll back to August code after newer refund/correction data exists.

## Later private maintenance view

Keep this bounded: deployed versions, service/database readiness, sanitized recent failures, last remotely verified backup/restore, alert status and approved configuration. Start with status; add actions only when repeated manual operations justify them. Every consequential action needs server-side creator authorization and attribution. Avoid a general SQL/code/secret editor.

Before another business shares the deployment, add separate platform identity/permissions and tested business isolation. Platform maintenance does not automatically grant access to named customers, private notes or money records. Client support access needs a defined purpose, owner approval, expiry and audit. Existing Qinetra ownership is not authorization from future clients.

The master [roadmap](../IMPLEMENTATION_ROADMAP.md) owns priorities. This maintenance view does not delay the essential pilot. Current catalogue copy and remaining backup/credentials/hosting gates are in [the check record](pilot-essentials-check.md).
