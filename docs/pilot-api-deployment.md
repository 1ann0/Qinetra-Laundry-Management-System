# Private pilot API deployment — 11 October 2026

The owner confirmed the setup command's final PASS, including both restricted TLS connections and private URL writes. Independent Supabase metadata confirms `qlms_runtime` and `qlms_backup` can log in, neither has administrator/create-role/create-database/bypass-RLS/replication authority, all 22 tables have RLS, backup has no write/destructive table rights, browser roles lack schema access, and counts remain 22 services/30 clothing types and zero staff/customers/orders/payments. No secret file was read by the agent.

**Completed 11 October:** the owner privately installed the two runtime variables and saved `/health/ready`. Render reports deployment `dep-db5d3gt9fdbs73celc90` Live at exact candidate `97686708c2f6e4facf574054850847b50bd0dbbd`, finished 00:02:51 UTC / 03:02:51 Nairobi. A fresh service read confirms the health path. Public HTTPS readiness returns 200 with `{"status":"ready"}`; `/docs` is 200; anonymous `/customers` is 401. Private cache, HSTS, nosniff and frame-denial headers passed. Both QLMS frontend preflights are allowed with their exact origin; an unrelated origin is denied. No environment values, credential-bearing logs or staff/customer records were inspected.

## Budget and source checks

The separate **qlms-pilot-api** service has been created in the already-approved **My Workspace**, on Python **Free** in Frankfurt. The original `qlms-backend` and August practice database are preserved. No Render database, disk, background worker, cron or paid add-on was created.

The owner confirmed My Workspace has **no payment method attached**. [Render's Free documentation](https://render.com/docs/free) says Free services share 750 running hours per month, with suspension when exhausted. Without a payment method, build/bandwidth limits stop or suspend the relevant Free operation instead of buying extra usage. Do not add a payment method or upgrade. Set the Build Pipeline supplementary-minute spend limit to zero if available, following [Render's instructions](https://render.com/docs/build-pipeline#setting-a-spend-limit). Do not leave two APIs continuously running for normal shop operation; agree the reversible old-service suspension at coordinated cutover, preserving its database and rollback revision.

The published app candidate is `97686708c2f6e4facf574054850847b50bd0dbbd`, on `codex/transaction-save-safety`, with [passing exact-candidate CI](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38083394911). A fresh 11 October GitHub branch-commit read matched that SHA. The connector rejected the slash-encoded branch-detail path; the supported commits collection with a branch query returned the exact head. Later local owner-run tooling/docs do not change the app API. Check the remote branch SHA immediately before deployment; do not deploy a changed/unverified head or merge main to create this service.

## Created service and public settings

Open [the existing pilot API](https://dashboard.render.com/web/srv-db5cqa0473hc73amomg0), rather than creating another service or reconnecting accounts. Its public URL is `https://qlms-pilot-api.onrender.com`. The connector supports build/start commands but not root-directory or health-path settings, so the commands below use the repository root. The owner has saved **Settings → Health Checks → Edit → `/health/ready` → Save Changes**, following [Render's documented location](https://render.com/docs/health-checks#setup); the field is independently verified. Do not repeat this completed step.

| Setting | Value |
| --- | --- |
| Workspace | My Workspace |
| Repository | `1ann0/Qinetra-Laundry-Management-System` |
| Name | `qlms-pilot-api` |
| Branch | `codex/transaction-save-safety` |
| Region | Frankfurt |
| Language/runtime | Python 3 |
| Root directory | Leave blank (repository root) |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT --no-access-log` |
| Instance type | **Free** |
| Auto-deploy | **Off** |
| Health-check path | `/health/ready`, saved by owner and verified |

These commands use Render's [FastAPI deployment pattern](https://render.com/docs/deploy-fastapi), with request access logs disabled for the pilot's privacy requirement. Pin `PYTHON_VERSION=3.12.14`, matching the tested local interpreter; Render supports a [fully qualified Python version variable](https://render.com/docs/python-version). Trusted-proxy/IP behavior still needs hosted qualification; do not add wildcard trust or claim this gate passed from a successful deployment alone.

## Enter the private runtime configuration yourself

The owner has completed private **Environment** entry of `DATABASE_URL` and `SECRET_KEY` from `C:\Users\1ann0\qlms\backend\ops\private\.env.pilot-runtime`. The five non-secret values below were already installed. Keep the private file and filled form outside ChatGPT/Codex observation. The agent did not read the values. Do not repeat entry, regenerate secrets or use the administrator/backup credential for the web service. The table records the configuration for recovery and later reviewed changes.

| Variable | Entry |
| --- | --- |
| `QLMS_ENV` | `production` |
| `QLMS_DB_SCHEMA` | `qlms` |
| `QLMS_DB_USER` | `qlms_runtime` |
| `PYTHON_VERSION` | `3.12.14` |
| `DATABASE_URL` | The privately saved runtime value; never send it in chat |
| `SECRET_KEY` | The privately saved fresh signing secret; never send it in chat |
| `ALLOWED_ORIGINS` | `https://qlms-pilot-qualification.qinetra.workers.dev,https://qlms.qinetra.workers.dev` |

The two installed origins cover the isolated qualification site and approved final branded site. No old Vercel/demo origin, localhost or wildcard belongs in the pilot CORS list. After qualification, remove the temporary origin at cutover. The local file's origins were deliberately left blank; copy only its two private entries, so that a blank local value does not replace the installed Render origins. Do not copy secret-bearing files to the public repository or share screenshots containing the filled Environment form.

The owner's rebuild/deploy completed successfully as recorded above; auto-deploy remains off. Historical creation deployment `dep-db5cqag473hc73amoo10` ended `update_failed` before private entry. No application logs were inspected and its specific provider failure was not diagnosed. It is superseded by the verified Live deployment, not an outstanding setup failure. For any later deploy report only its non-secret status; do not paste environment values or raw application/SQL logs.

## Verification and remaining work

The public metadata/readiness/docs/anonymous-denial/header/CORS checks above passed without passwords or staff data. The frontend has already been rebuilt locally for this verified HTTPS API and passed its offline checks; the new package still needs upload and hosted pairing. Cloudflare currently serves the earlier fictional-loopback build. Trusted client-IP behavior, privately created owner/staff accounts, independent recovery/alerts and the actual laptop/phone session remain gates before real-customer entry.
