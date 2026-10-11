# Owner-run pilot frontend upload — 11 October 2026

The pilot API is Live at `https://qlms-pilot-api.onrender.com`, with saved `/health/ready` and passing public readiness/security/CORS/anonymous-denial checks. The matching frontend package is already built and checked. The current Cloudflare site still uses the older fictional API; uploading and activating this new package is the next step.

## Keep the upload token private

The Cloudflare account/plugin connection remains established. The prior temporary Worker-only upload token expired **11 October at 01:18 Nairobi**. It must not be read, tested or renewed by an agent. Use your existing signed-in Cloudflare account; this is replacement of an expired deployment credential, not account setup.

The previous review screenshot and [current account-token instructions](https://developers.cloudflare.com/fundamentals/api/get-started/account-owned-tokens/) identify **Manage account → Account API tokens**, after selecting the account containing `qlms-pilot-qualification`. Use this account page, not the personal profile's token page. Select **Create Token** and name it `QLMS frontend upload`. Set the resource to **Workers → Specified Workers → qlms-pilot-qualification only** and permission to **Individual Workers → Editor**, starting now and expiring within one day. [Workers authorization guidance](https://developers.cloudflare.com/workers/authorization/workers/) confirms the per-Worker Editor scope. Do not select every Worker/account or broaden the permissions if the upload fails.

Select **Continue to summary**. Check that the review lists only `qlms-pilot-qualification`, **Individual Workers Editor** and a future expiry within 24 hours; then select **Create Token** privately. Keep the token outside ChatGPT; save it after `CLOUDFLARE_API_TOKEN=` in the existing owner-only, ignored `C:\Users\1ann0\qlms\.env.cloudflare-qualification`, preserving the existing account-ID entry. Do not put database credentials, staff passwords or the recovery key in that file.

Use your own editor outside Codex and close the file after saving. Do not share its contents or a filled-form screenshot. If the token screen cannot restrict access to that single existing Worker, stop before creating it and report only that limitation.

## Upload the prepared package privately

Open your own PowerShell window outside Codex. Run these two commands (the second is one line):

```powershell
Set-Location 'C:\Users\1ann0\qlms'
docker --context default run --rm --pull=never --env-file 'C:\Users\1ann0\qlms\.env.cloudflare-qualification' -e WRANGLER_SEND_METRICS=false --entrypoint ./node_modules/.bin/wrangler sha256:91aeac649e6ced997ead6c49cdc708a6be86464de3e3526117e192843416e899 versions upload --config hosting/wrangler.generated.json --name qlms-pilot-qualification --strict --message 'QLMS 9768670 paired HTTPS API qualification'
```

The image digest pins the verified local package rather than downloading or rebuilding different code. Its static browser assets use the actual pilot HTTPS API; it contains no private environment files. Docker imports the token locally when **you** run this command. Only ASSETS and the public API-origin binding belong to the uploaded Worker; runtime database/signing secrets stay on Render.

The exact pinned-image `versions upload` command above was rehearsed with `--dry-run`, empty credential variables and no network: exit 0, Worker 2.15 KiB raw / 1.03 KiB gzip, ASSETS and the correct public HTTPS API origin only. This verifies the package/flags; the real token and remote upload remain owner-operated.

This uses [Cloudflare's upload-without-deployment operation](https://developers.cloudflare.com/workers/versions-and-deployments/deployment-management/#upload-a-version-without-deploying). It uploads a new version to the existing qualification Worker without changing live traffic. It avoids the account-subdomain operation that previously failed outside the single-Worker token grant. Strict mode also prevents an unnoticed conflicting remote change. Do not add `--keep-vars`: retaining the old fictional API-origin binding would give the new build the wrong security policy.

On success, report **only the Uploaded Version ID** (a public UUID). Do not paste raw logs, token values or file contents. If it fails, report only the exit status and a non-secret error code; do not widen access or repeatedly retry an uncertain upload. Wrangler's private diagnostic log remains outside agent access.

## What happens after upload

The agent checks the new version's non-secret metadata and expected public API binding, activates the reviewed version through the already-connected Cloudflare plugin, and independently verifies the deployment and public HTTPS routes/headers. The approved final `qlms.qinetra.workers.dev` address is applied only with the coordinated final routing/release step; no duplicate Worker is needed merely to upload this package.

Private Owner/Employee creation, actual signed-in laptop/work-phone checks, independent backups/recovery/alerts and final cutover remain separate gates. Do not enter real customer data yet.
