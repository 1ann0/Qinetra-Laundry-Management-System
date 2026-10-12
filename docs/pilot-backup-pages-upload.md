# Public backup pages — verified frontend release

Prepared 12 October 2026 after the user approved the public content and three pages. This candidate also includes the finished search/help increment from the preceding frontend candidate. It targets the existing **qlms** Worker and paired HTTPS API; no account reconnection, database migration or backup activation is included.

## Candidate and checks

- Routes: `/backup`, `/backup/privacy`, `/backup/terms`; sign-in links to the public information/privacy pages. The operational root redirect is preserved.
- Exact image: `sha256:65d380728a9d9d81130d730b99e73eae890928fa95244ebd651decc7c6d1900e`, tagged `qlms-backup-info:20261012` in the agent's Docker context.
- Image build: 90 frontend tests, lint and 19-page static export passed. All 60 public source files match the image. No new dependency, API contract, secret or schema change.
- Anonymous browser checks: three pages at 320/375/768/1280 px; content available in initial HTML; no horizontal overflow; 44 px header navigation; skip-to-content keyboard focus; privacy/terms/login links; private/security headers; no API request or page error. These are local simulated phone widths, not actual Android evidence.
- Exact offline `versions upload --strict --dry-run` passed with no credential and network disabled. Worker upload is 2.15 KiB, gzip 1.03 KiB, with only ASSETS and the expected public API origin.
- [Public asset manifest](diagrams/evidence/qlms-backup-info-assets-20261012.json): 124 assets, 28 JavaScript files; SHA256 `8330c2425aa6aa74ca0b8227ffb61aa74d0e5900d10aa49cf002a7f1ad8b4d7a`. Static routes, compiled HTTPS policy and stale fixture-address exclusion checked.
- Previous verified version `c622e581-6d12-45a9-b0d6-c07d8bf4bd36` remains available for rollback. The release below supersedes it.

## Connected-plugin release — completed 12 October

The user authorized handling the temporary Cloudflare upload grant after the human upload failed, then requested another Chrome attempt. Chrome control still failed with `Unable to load browser request-header policy`; account-token administration through the plugin returned authorization denial. No account API token was created, existing private token file read or permission broadened.

Instead, the connected plugin registered the verified public manifest and provided a short-lived asset upload session. Its grant was encrypted for transfer to local memory; 104 unique assets covering 123 public paths uploaded successfully (HTTP 202/202/201). `_headers` was preserved as a Worker text module, rather than uploaded as a public asset. The 147 entries reported by Wrangler comprise 124 files and 23 directories.

Automatic approval review rejected printing the completion grant, including during a proposed tool transfer. That action was not performed. The safe replacement registered the same already-uploaded manifest inside the connected plugin: no buckets remained, so the plugin used the completion grant internally and created the version without exposing it. Active local credential variables were cleared afterward; no credential file was written. Short-lived provider grants expire normally.

- Source: `bb71009`; immutable image and manifest above.
- Version: `cf2c15f9-90c0-4a53-a6dc-3cc7eefbaadd`, number 7, Worker startup 2 ms.
- Deployment: `5732c263-0031-41aa-bdbd-470a5a52cc81`, 100%, **12 October 2026, 15:00:27 Nairobi**.
- Before activation: byte-for-byte readback matched the exported `worker.js` and `_headers`; bindings, compatibility date/flags, asset routing and previous live version matched. Observability/logpush remain disabled.
- After activation: independent hosted HTTP checks returned 200 and initial content for About/Privacy/Terms/login; private/CSP/frame headers passed. All **123 public asset SHA256 hashes** match the qualified export. Missing route returns 404; numeric order/customer links return the expected 302 with private headers; sign-in includes both public links. Connected-plugin readback confirms the new version at 100%.
- [Public hosted evidence](diagrams/evidence/qlms-backup-info-hosted-20261012.json) records this release. The earlier phone screenshots remain local simulated-width evidence; Chrome control, actual Android rendering, authenticated sessions and Google domain acceptance were not verified during this release.

The API/schema pair is unchanged. This publishes the public pages and finished shared search/help increment, not automatic backups or permission to enter real customer data. No repeat upload or token renewal is required for this candidate.

## Historical human upload — fallback instructions only

Use your own PowerShell outside Codex. Keep the existing private token file and same single-Worker Editor restriction. Do not display or send its contents. This candidate supersedes the earlier usability-only upload image; do not upload both.

Run these blocks separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms'
```

```powershell
docker --context default run --rm --pull=never --env-file 'C:\Users\1ann0\qlms\.env.cloudflare-qualification' -e WRANGLER_SEND_METRICS=false --entrypoint ./node_modules/.bin/wrangler sha256:65d380728a9d9d81130d730b99e73eae890928fa95244ebd651decc7c6d1900e versions upload --config hosting/wrangler.generated.json --name qlms --strict --message 'QLMS public backup information and privacy; shared search and help'
```

Report only the **Uploaded Version ID**. For an error, report only a safe missing-image/expired-token/permission description; never raw logs. `--pull=never` refuses a missing human-side local image. Agent-side visibility does not establish that your Docker context can see it. If missing, stop for transfer of the public package. Renew an expired token only with the existing single-Worker Editor restriction; do not broaden it.

12 October human upload attempt: the screenshot confirms Wrangler **4.125.0** ran, so the candidate image is available in the human's Docker context. It reports service-request authentication error **10000** and invalid access token **9109**. No successful version ID is shown; no activation was performed by the agent. Token expiry/revocation/malformed saved value cannot be distinguished from the screenshot. Do not read the private file or debug log. Privately replace the rejected token via account **Manage account → Account API tokens**, keeping **Individual Workers → qlms → Editor** and an expiry within one day, as detailed in [the renewal instructions](pilot-frontend-deployment.md#keep-the-upload-token-private). Save only the new value after `CLOUDFLARE_API_TOKEN=`, preserve the account-ID entry, close the editor, and rerun this exact command. No rebuild, account reconnection or permission broadening is needed.

Upload creates a candidate without switching live traffic. Through the connected Cloudflare plugin, inspect the uploaded version and expected assets/public API binding, refresh the active version, activate, then verify hosted public pages/links/security headers and asset hashes. Preserve the prior version for rollback. If unexpected live state or checks fail, stop activation or restore the verified prior version.

## Google Branding — hosted URLs now verified

Use the existing backup project in your own browser. Confirm app name **QLMS backup automation** and support email **qinetraian@gmail.com**. Set these verified public URLs:

- Homepage: `https://qlms.qinetra.workers.dev/backup`
- Privacy: `https://qlms.qinetra.workers.dev/backup/privacy`
- Terms: `https://qlms.qinetra.workers.dev/backup/terms`

Do not use the sign-in page as the homepage. These pages are deployed; Google's acceptance is the next separate check.

Google's domain acceptance/ownership verification for this free address is still unqualified. `workers.dev` is a public suffix; `qinetra.workers.dev` is the candidate authorized domain, but that fact alone does not prove Google accepts or verifies it. If Google refuses it, report only the nonsecret validation message and stop. Do not buy a domain, add billing, use another organization's URLs or claim verification succeeded. A Search Console verification challenge, if required, needs a separate bounded public-file/tag step; credentials stay private.

After required Branding fields and domain checks pass, return to Audience and confirm **In production** before issuing the offline Drive grant. Creating Branding, uploading frontend files or passing local tests does not itself set that status. Actual Drive consent, measured backup/storage, timed restore, retention, alerts and laptop-off scheduling remain incomplete.

References: [Google Branding requirements](https://support.google.com/cloud/answer/15549049), [Testing expiry](https://support.google.com/cloud/answer/15549945), [Workers version upload](https://developers.cloudflare.com/workers/wrangler/commands/workers/#versions-upload).
