# Owner-run pilot frontend upload — 11 October 2026

The current address is **https://qlms.qinetra.workers.dev/login**. The reviewed HTTPS frontend is activated and the pilot API is Live at `https://qlms-pilot-api.onrender.com`. A same-version API redeploy recovered a reproduced timeout; final-origin readiness/CORS pass, while idle recovery and actual private device sign-in remain to qualify.

The next upload adds the requested inline sign-in/reentry spinner and bounded login-only two-minute wait. The new pinned local image passed all 84 frontend tests, lint, 16-page static export, compiled HTTPS-origin checks and an offline strict upload dry-run. This button change is prepared, not live until a new version is activated/read back. The existing Worker was renamed to `qlms`, preserving its immutable ID; target that name now.

## Keep the upload token private

The Cloudflare account/plugin connection remains established. The user already replaced the earlier expired temporary Worker token privately. Reuse the existing private file for this upload; the agent must not read or load it. If Cloudflare rejects expiry or scope, renew privately for the same immutable Worker now named `qlms`; do not broaden access or repeat account setup.

Only if renewal is required: the previous review screenshot and [current account-token instructions](https://developers.cloudflare.com/fundamentals/api/get-started/account-owned-tokens/) identify **Manage account → Account API tokens**, after selecting the account containing `qlms`. Use this account page, not the personal profile's token page. Select **Create Token** and name it `QLMS frontend upload`. Set the resource to **Workers → Specified Workers → qlms only** and permission to **Individual Workers → Editor**, starting now and expiring within one day. [Workers authorization guidance](https://developers.cloudflare.com/workers/authorization/workers/) confirms the per-Worker Editor scope. Do not select every Worker/account or broaden the permissions if the upload fails.

For renewal, select **Continue to summary**. Check that the review lists only `qlms`, **Individual Workers Editor** and a future expiry within 24 hours; then select **Create Token** privately. Keep the token outside ChatGPT; save it after `CLOUDFLARE_API_TOKEN=` in the existing owner-only, ignored `C:\Users\1ann0\qlms\.env.cloudflare-qualification`, preserving the existing account-ID entry. Do not put database credentials, staff passwords or the recovery key in that file.

Use your own editor outside Codex and close the file after saving. Do not share its contents or a filled-form screenshot. If the token screen cannot restrict access to that single existing Worker, stop before creating it and report only that limitation.

## Upload the prepared package privately

Open your own PowerShell window outside Codex. Run these two commands (the second is one line):

```powershell
Set-Location 'C:\Users\1ann0\qlms'
docker --context default run --rm --pull=never --env-file 'C:\Users\1ann0\qlms\.env.cloudflare-qualification' -e WRANGLER_SEND_METRICS=false --entrypoint ./node_modules/.bin/wrangler sha256:1e1e9f34960ae70a42ea3e66805f58effbb1675e5b3c7726d005af541f843e56 versions upload --config hosting/wrangler.generated.json --name qlms --strict --message 'QLMS inline sign-in feedback and bounded startup wait'
```

The image digest pins the verified local package rather than downloading or rebuilding different code. Its static browser assets use the actual pilot HTTPS API; it contains no private environment files. Docker imports the token locally when **you** run this command. Only ASSETS and the public API-origin binding belong to the uploaded Worker; runtime database/signing secrets stay on Render.

The exact pinned-image `versions upload` command above was rehearsed with `--dry-run`, empty credential variables and no network: exit 0, Worker 2.15 KiB raw / 1.03 KiB gzip, ASSETS and the correct public HTTPS API origin only. This verifies the package/flags; the real token and remote upload remain owner-operated.

This uses [Cloudflare's upload-without-deployment operation](https://developers.cloudflare.com/workers/versions-and-deployments/deployment-management/#upload-a-version-without-deploying). It uploads a new version to the same renamed Worker without changing live traffic. It avoids the account-subdomain operation that previously failed outside the single-Worker token grant. Strict mode also prevents an unnoticed conflicting remote change. Do not add `--keep-vars`; the built public API origin must match its security policy.

On success, report **only the Uploaded Version ID** (a public UUID). Do not paste raw logs, token values or file contents. If it fails, report only the exit status and a non-secret error code; do not widen access or repeatedly retry an uncertain upload. Wrangler's private diagnostic log remains outside agent access.

## What happens after upload

The agent checks the new version's non-secret metadata and expected public API binding, activates the reviewed version through the already-connected Cloudflare plugin, and independently verifies the deployment and public HTTPS routes/headers at `qlms.qinetra.workers.dev`. No duplicate Worker is needed.

Private Owner/Employee creation, actual signed-in laptop/work-phone checks, independent backups/recovery/alerts and final cutover remain separate gates. Do not enter real customer data yet.
