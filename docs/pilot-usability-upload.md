# QLMS search and help — private frontend upload

Prepared 12 October 2026. The current public app remains **https://qlms.qinetra.workers.dev/login**. This guide targets the finished interface increment; it does not repeat the earlier completed sign-in-button upload.

**Superseded before upload:** the approved public backup-information/privacy/terms pages are now included alongside this increment in [the newer upload candidate](pilot-backup-pages-upload.md). Use that candidate once its checks are complete; do not upload both images. The image below remains the historical usability-only qualification record.

## Reviewed candidate

- Frontend source: `e6c7ec9`, shared Find, searchable catalogue/Staff lists, direct history links, optional page help and accessible mobile navigation/buttons.
- Exact public image: `sha256:76f34de9421592cef64aeafdf66cf214c023978c0c0376f56ac82caad1566f31`.
- Completed checks: 90 frontend tests, lint, 16-page static export, strict offline upload dry-run, public source match and final fictional phone-width login/reentry/search/help checks. Screenshots 60/61 retain meaningful fictional evidence.
- On 12 October, this exact image was present in the agent's Docker context. Its 108 public static assets were exported and hashed in [the manifest](diagrams/evidence/qlms-usability-assets-20261012.json), SHA256 `c2eaf909d8a23c891fdea8a709b9aed7da8ba1480a163b9c254bf57ed3fe4841`. The stopped export container was removed. No credential or private environment file was used.
- Paired API remains `https://qlms-pilot-api.onrender.com`, source `9768670`; this interface increment needs no database migration. Actual upload and activation are still pending.

## Human-operated upload

Keep the existing Cloudflare account/plugin connection and private token file. If the token has expired, renew only the same single-Worker Editor grant for **qlms**, expiring within one day, using the instructions in [the earlier upload guide](pilot-frontend-deployment.md#keep-the-upload-token-private). Do not broaden access. The agent must not read or load the file.

Run these two blocks separately in your own PowerShell **outside Codex**:

```powershell
Set-Location 'C:\Users\1ann0\qlms'
```

```powershell
docker --context default run --rm --pull=never --env-file 'C:\Users\1ann0\qlms\.env.cloudflare-qualification' -e WRANGLER_SEND_METRICS=false --entrypoint ./node_modules/.bin/wrangler sha256:76f34de9421592cef64aeafdf66cf214c023978c0c0376f56ac82caad1566f31 versions upload --config hosting/wrangler.generated.json --name qlms --strict --message 'QLMS shared search and contextual page help'
```

`--pull=never` refuses a missing local image; it does not substitute a download or rebuild. If your Docker context cannot see this image, report only that safe error and stop so the public package can be transferred/verified. Never send the token or raw Wrangler logs.

The [official version-upload command](https://developers.cloudflare.com/workers/wrangler/commands/workers/#versions-upload) uploads a candidate without switching live traffic. Strict mode refuses conflicting remote settings. Keep the built public API origin; do not add `--keep-vars` or upload database/signing secrets.

Report only the **Uploaded Version ID**, or a short nonsecret missing-image/expiry/permission error. The agent then reads nonsecret version metadata, activates the reviewed candidate through the Cloudflare plugin, verifies the expected deployment/binding, compares hosted public assets with this manifest and checks private headers/routes. Rollback retains the previous live version `c622e581-6d12-45a9-b0d6-c07d8bf4bd36`.

## Release boundary

These instructions do not activate backup jobs or open real-data use. Independent backup/restore/key recovery, measured retention/storage, delivered alerts and laptop-off scheduling remain separate pilot gates. The existing workflow trials reported by the user remain accepted; this UI package is not evidence of an actual Android walkthrough.
