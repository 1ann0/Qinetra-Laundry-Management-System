# Public backup pages — private frontend upload

Prepared 12 October 2026 after the user approved the public content and three pages. This candidate also includes the finished search/help increment from the preceding frontend candidate. It targets the existing **qlms** Worker and paired HTTPS API; no account reconnection, database migration or backup activation is included.

## Candidate and checks

- Routes: `/backup`, `/backup/privacy`, `/backup/terms`; sign-in links to the public information/privacy pages. The operational root redirect is preserved.
- Exact image: `sha256:65d380728a9d9d81130d730b99e73eae890928fa95244ebd651decc7c6d1900e`, tagged `qlms-backup-info:20261012` in the agent's Docker context.
- Image build: 90 frontend tests, lint and 19-page static export passed. All 60 public source files match the image. No new dependency, API contract, secret or schema change.
- Anonymous browser checks: three pages at 320/375/768/1280 px; content available in initial HTML; no horizontal overflow; 44 px header navigation; skip-to-content keyboard focus; privacy/terms/login links; private/security headers; no API request or page error. These are local simulated phone widths, not actual Android evidence.
- Exact offline `versions upload --strict --dry-run` passed with no credential and network disabled. Worker upload is 2.15 KiB, gzip 1.03 KiB, with only ASSETS and the expected public API origin.
- [Public asset manifest](diagrams/evidence/qlms-backup-info-assets-20261012.json): 124 assets, 28 JavaScript files; SHA256 `8330c2425aa6aa74ca0b8227ffb61aa74d0e5900d10aa49cf002a7f1ad8b4d7a`. Static routes, compiled HTTPS policy and stale fixture-address exclusion checked.
- Fresh connected-plugin readback after one transient HTTP 504: version `c622e581-6d12-45a9-b0d6-c07d8bf4bd36`, deployment `5ca27a41-144c-494d-90ea-f4823ea535b8`, 100%. Refresh again before activation. No upload or activation has occurred.

## Human upload — keep credentials outside Codex

Use your own PowerShell outside Codex. Keep the existing private token file and same single-Worker Editor restriction. Do not display or send its contents. This candidate supersedes the earlier usability-only upload image; do not upload both.

Run these blocks separately:

```powershell
Set-Location 'C:\Users\1ann0\qlms'
```

```powershell
docker --context default run --rm --pull=never --env-file 'C:\Users\1ann0\qlms\.env.cloudflare-qualification' -e WRANGLER_SEND_METRICS=false --entrypoint ./node_modules/.bin/wrangler sha256:65d380728a9d9d81130d730b99e73eae890928fa95244ebd651decc7c6d1900e versions upload --config hosting/wrangler.generated.json --name qlms --strict --message 'QLMS public backup information and privacy; shared search and help'
```

Report only the **Uploaded Version ID**. For an error, report only a safe missing-image/expired-token/permission description; never raw logs. `--pull=never` refuses a missing human-side local image. Agent-side visibility does not establish that your Docker context can see it. If missing, stop for transfer of the public package. Renew an expired token only with the existing single-Worker Editor restriction; do not broaden it.

Upload creates a candidate without switching live traffic. Through the connected Cloudflare plugin, inspect the uploaded version and expected assets/public API binding, refresh the active version, activate, then verify hosted public pages/links/security headers and asset hashes. Preserve the prior version for rollback. If unexpected live state or checks fail, stop activation or restore the verified prior version.

## Google Branding — only after hosted verification

Use the existing backup project in your own browser. Confirm app name **QLMS backup automation** and support email **qinetraian@gmail.com**. Set the homepage to the verified `/backup` address, privacy URL to `/backup/privacy`, and terms URL to `/backup/terms` on the same hosted origin. Do not use the sign-in page as the homepage.

Google's domain acceptance/ownership verification for this free address is still unqualified. `workers.dev` is a public suffix; `qinetra.workers.dev` is the candidate authorized domain, but that fact alone does not prove Google accepts or verifies it. If Google refuses it, report only the nonsecret validation message and stop. Do not buy a domain, add billing, use another organization's URLs or claim verification succeeded. A Search Console verification challenge, if required, needs a separate bounded public-file/tag step; credentials stay private.

After required Branding fields and domain checks pass, return to Audience and confirm **In production** before issuing the offline Drive grant. Creating Branding, uploading frontend files or passing local tests does not itself set that status. Actual Drive consent, measured backup/storage, timed restore, retention, alerts and laptop-off scheduling remain incomplete.

References: [Google Branding requirements](https://support.google.com/cloud/answer/15549049), [Testing expiry](https://support.google.com/cloud/answer/15549945), [Workers version upload](https://developers.cloudflare.com/workers/wrangler/commands/workers/#versions-upload).
