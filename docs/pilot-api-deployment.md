# Private pilot API deployment — 11 October 2026

The database-role change is independently visible: `qlms_runtime` and `qlms_backup` can log in, neither has administrator/create-role/create-database/bypass-RLS/replication authority, all 22 tables have RLS, backup has no write/destructive table rights, browser roles lack schema access, and counts remain 22 services/30 clothing types and zero staff/customers/orders/payments. The owner's final setup PASS line is still needed to attest the actual TLS checks and private URL writes. No secret file was read by the agent.

## Budget and source checks

Use the already-approved **My Workspace**. Preserve the existing `qlms-backend` service and August practice database while the separate pilot is qualified. The proposed service is one Python **Free** web service, with Supabase retained as the database; no Render database, disk, background worker, cron or paid add-on is required.

Before creating it, confirm the workspace payment/usage setting privately. [Render's Free documentation](https://render.com/docs/free) says Free services share 750 running hours per month, with suspension when exhausted. Build/bandwidth overages can be billed if a payment method exists. Without a payment method, those limits stop/suspend the relevant Free operation instead of buying extra usage. Do not add a payment method or upgrade. If one already exists, stop here until a verified zero-charge arrangement is in place; a pipeline limit alone does not document a bandwidth cap. Set the Build Pipeline supplementary-minute spend limit to zero if available, following [Render's instructions](https://render.com/docs/build-pipeline#setting-a-spend-limit). Do not leave two APIs continuously running for normal shop operation; agree the reversible old-service suspension at coordinated cutover, preserving its database and rollback revision.

The published app candidate is `97686708c2f6e4facf574054850847b50bd0dbbd`, on `codex/transaction-save-safety`, with [passing exact-candidate CI](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38083394911). A fresh 11 October GitHub branch-commit read matched that SHA. The connector rejected the slash-encoded branch-detail path; the supported commits collection with a branch query returned the exact head. Later local owner-run tooling/docs do not change the app API. Check the remote branch SHA immediately before deployment; do not deploy a changed/unverified head or merge main to create this service.

## Enter the non-secret settings

Open [Render's New Web Service form](https://dashboard.render.com/web/new) in your existing signed-in account. Select the existing GitHub repository rather than reconnecting accounts. If it shows a new permission or paid requirement, stop before accepting it.

| Setting | Value |
| --- | --- |
| Workspace | My Workspace |
| Repository | `1ann0/Qinetra-Laundry-Management-System` |
| Name | `qlms-pilot-api` (requested name; actual URL must be read back after creation) |
| Branch | `codex/transaction-save-safety` |
| Region | Frankfurt |
| Language/runtime | Python 3 |
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT --no-access-log` |
| Instance type | **Free** |
| Auto-deploy | **Off** |
| Health-check path | `/health/ready` |

These commands use Render's [FastAPI deployment pattern](https://render.com/docs/deploy-fastapi), with request access logs disabled for the pilot's privacy requirement. Pin `PYTHON_VERSION=3.12.14`, matching the tested local interpreter; Render supports a [fully qualified Python version variable](https://render.com/docs/python-version). Trusted-proxy/IP behavior still needs hosted qualification; do not add wildcard trust or claim this gate passed from a successful deployment alone.

## Enter the private runtime configuration yourself

Copy only the runtime fields from `C:\Users\1ann0\qlms\backend\ops\private\.env.pilot-runtime` into this new service's Environment fields, directly in Render. Keep this file and filled form outside ChatGPT/Codex observation. Do not use the administrator or backup credential for the web service.

| Variable | Entry |
| --- | --- |
| `QLMS_ENV` | `production` |
| `QLMS_DB_SCHEMA` | `qlms` |
| `QLMS_DB_USER` | `qlms_runtime` |
| `PYTHON_VERSION` | `3.12.14` |
| `DATABASE_URL` | The privately saved runtime value; never send it in chat |
| `SECRET_KEY` | The privately saved fresh signing secret; never send it in chat |
| `ALLOWED_ORIGINS` | `https://qlms-pilot-qualification.qinetra.workers.dev,https://qlms.qinetra.workers.dev` |

The two origins cover the isolated qualification site and approved final branded site. No old Vercel/demo origin, localhost or wildcard belongs in the pilot CORS list. After qualification, remove the temporary origin at cutover. The local file's origins were deliberately left blank; enter the exact value above in Render yourself. Do not copy secret-bearing files to the public repository or share screenshots containing the filled Environment form.

Create/deploy only after the database setup PASS, exact source SHA and zero-spend checks are confirmed. Report only the **public service URL** or service ID and the deployment status. If the deploy fails, report its status and stop; do not paste environment values or raw application/SQL logs.

## Verification and remaining work

The agent can independently read the new service's non-secret metadata and deployed commit, check public HTTPS `/health/ready` and `/docs`, and test private headers/CORS with fictional inputs. These checks do not require passwords or staff data. The frontend must then be rebuilt for the actual verified HTTPS API and deployed; its current qualification build still uses a fictional loopback API. Final proxy/security checks, privately created owner/staff accounts, independent recovery/alerts and the actual laptop/phone session remain gates before real-customer entry.
