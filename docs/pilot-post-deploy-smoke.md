# Public post-deployment smoke check

This is a required read-only release check. It uses the approved public asset manifest to catch incomplete frontend uploads, missing clean page routes (including Expenses), stale assets, a wrong compiled API origin, unsafe response headers, unavailable/wrong-schema readiness, missing API routes and endpoints that fail to deny anonymous access. It does not log in, read protected response bodies, save shop records, load private configuration or enable a recurring keep-alive.

## After each application deployment

1. Record the exact frontend source/image/asset manifest and actual Cloudflare version/deployment, actual Render API commit/deployment and schema revision in the release check. Provider metadata, not this public tool, proves the API commit and traffic allocation.
2. Run the existing **Verify QLMS** workflow from the reviewed source branch using **Run workflow**. Enable **post_deploy_smoke** and provide the approved full frontend source SHA and repository path to that release's public asset manifest. The current defaults describe the expense release, not every future release. Ordinary pushes/PRs never run these live requests.
3. Require the **Public pilot post-deploy smoke** job and both normal verification jobs to pass. The smoke result is public JSON in its job summary; it contains counts/origins/source/time only, no records, credentials or server bodies.
4. Complete the affected authenticated Owner/Employee workflow with fictional local evidence and appropriate private human acceptance. A public smoke pass cannot prove account permissions, successful financial saves, actual Android behavior or restore readiness.
5. If the tool fails, stop promotion, investigate the named public check and use the release's recorded compatible rollback if needed. Do not reset the database, replay payments or run setup commands to fix a hosting mismatch.

The workflow is on `codex/transaction-save-safety`, like the pilot release source; do not merge unrelated application history into main merely to expose a button. Main's backup workflow and original practice service remain separate. A workflow run can explicitly select the reviewed feature branch.

## Equivalent local command

Run these as two separate PowerShell commands from the repository. No private terminal or secret file is needed:

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
```

```powershell
..\tmp\test-venv\Scripts\python.exe -m ops.release_smoke --manifest ..\docs\diagrams\evidence\qlms-owner-expenses-assets-20261015.json --frontend https://qlms.qinetra.workers.dev --api https://qlms-pilot-api.onrender.com --source e6d9d2bb68ae8224e311c15e3a4232057bc7d6bb
```

An optional `--output` takes a **new** public JSON filename. Existing files are never overwritten. The manifest must contain the entire approved static export; `_headers` is hosting configuration and is checked through actual page headers instead of fetched as a public file. Generated Next.js route payloads are included. Every generated HTML page's clean URL must return its expected content, not a successful generic fallback.

## Design, checks and rollback

- Standard-library-only `backend/ops/release_smoke.py`, invoked by the existing verification workflow. No application dependency, schema, UI, hosting permission or secret changes.
- Network is bounded, HTTPS-only and does not follow redirects to another origin. Anonymous denial probes deliberately never read a body even if a broken endpoint unexpectedly returns 200. Errors do not print exception details or server content. Readiness gets a longer cold-start deadline; a timeout fails honestly rather than hiding it with unbounded retries.
- Test-first checks use fictional replies: missing route and wrong fallback HTML, stale hashes, wrong API/CSP, missing private headers, unavailable readiness, missing API contracts, exposed anonymous endpoints, unsafe manifests, generated route payload filenames, same-origin/cross-origin redirects, sanitized errors, new page discovery and refusal to overwrite files.
- Skills: Superpowers brainstorming bounded the read-only design to existing release facts; TDD established failing cases before implementation; debugging corrected the actual generated Next.js filename case; verification and Ponytail review cover network/privacy/callers; UI/UX review confirms this increment changes no staff screens or navigation.
- Rollback: revert this workflow job and helper/tests/docs, or leave the optional input off. No deployment/database rollback is needed for an operations-only change. Existing staff behavior and the current live application remain unchanged.
- Local test-first result: **11 focused tests passed**. The initial missing helper, generated Next.js `!` payload-name validation and incorrect GET assumption on the POST-only `/expenses` collection were reproduced before their fixes. The final denial probe uses existing GET `/expenses/1` and never reads its body.
- Actual live run passed **135 public asset hashes, 19 clean page routes, API readiness/contract and three anonymous denials**. [Public evidence](diagrams/evidence/qlms-release-smoke-20261015.json) records time/counts/source, explicitly excluding authenticated behavior and API commit proof.
- Published operations source **`1451ccc7dbbd8be1b4d13338c23036b3e374713a`** passed [GitHub run 38741029506](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38741029506): public live smoke, Backend and recovery, and Frontend tests/lint/build all completed successfully. Public smoke ran on GitHub from 13:15:23–13:15:40 UTC on 15 October. This completes the operations increment; the hosted app/API/schema remain the expense release. No application redeploy was needed.
- Chrome evidence capture timed out twice; no new screenshot or actual phone acceptance is claimed. The live tool result and actual hosted job/steps are the evidence, not a manufactured test screenshot.
