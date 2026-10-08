# Cloudflare frontend qualification — 9 October 2026

Continue the approved zero-spend frontend experiment. Preserve Next.js, the HTTP-only FastAPI boundary, Supabase and all earlier fixtures. This is developer qualification, not a production release or final staff acceptance.

## Account and limits

The user supplied the open, signed-in Cloudflare account. Its Workers plans page showed Free as the current $0 plan, 100,000 requests/day and 10 ms CPU/request. No account setup, upgrade, new access grant, billing action or external project was performed. Browser control later detached; re-enabling it and a fresh tool session still failed. Actual hosted CPU/startup and interactive acceptance remain blocked at that transport, not at account connection.

Current [Workers limits](https://developers.cloudflare.com/workers/platform/limits/) specify 64 MiB uncompressed bundle size, 128 MB isolate memory and one-second script startup. Local wall time is not cloud CPU time. The [self-serve agreement](https://www.cloudflare.com/terms/) has free-service conditions; the reviewed text does not contain Vercel's explicit non-commercial-personal-use restriction. Do not infer availability guarantees from Free or a successful build.

## Exact source and isolated wrapper

- App source: published full SHA `1bfdf4a3b607a3349769fe3c4b46c64e0fb1790b`. Git archive supplied only `frontend`; no working-tree draft, private file or demonstration database entered the build.
- Reused existing local image `qlms-cloudflare-qualification:20261005`, digest `8c4a506ff331feea26455bae487200116bd4f61712abbbd8032a89d4670c3378`. Installed tooling was read back: Node 22.23.3, OpenNext 1.20.7, Wrangler 4.125.0 and Next.js 16.3.6. This is a local build environment, not the Node 24 GitHub runner or the hosted V8 runtime.
- Derived image `qlms-workers-candidate:1bfdf4a`, manifest `baeec29ffb31afa7375b0b9ce1165e5b105f7be2604ff0bd325aaaa04f203587`. All **57 source/public files matched SHA-256** against the archived candidate.
- Temporary deployment wrapper uses the original static logo without image optimization, existing headers, compatibility date `2026-08-27`, only ASSETS, disabled observability and a 10 ms CPU configuration. No R2/KV/database/image service or product dependency was added. API origin is fictional loopback `http://127.0.0.1:8012`; a real HTTPS origin requires a new build and paired configuration checks.

The old Docker image was retained even though no prototype files/volumes were found in the earlier bounded search. Reusing its tooling does not reuse its old app source or acceptance results.

## Fresh verification

| Check | Result |
| --- | --- |
| Frontend tests in the isolated Linux copy | 77 passed, zero failed/skipped. |
| Lint | Zero errors; one anonymous-default-export warning in the temporary wrapper. |
| Next.js/OpenNext build | Passed through OpenNext's own standalone build path. |
| Wrangler upload dry-run | Passed; 42 static files, 5,472.90 KiB uncompressed / 1,123.38 KiB gzip, only ASSETS binding. No upload. |
| Local HTML routes | `/login` twice, `/workspace`, `/orders/1`, `/customers/1`: HTTP 200, correct HTML/title, private/no-store, CSP, nosniff, frame denial and no-referrer headers. |
| Static delivery | Original 142,697-byte logo and two JavaScript chunks returned HTTP 200/nonempty content. |
| Local wall time | First login 2,859 ms; repeated login 297 ms; other HTML routes 110–235 ms. The older 85-second result was not reproduced. This does not prove cloud CPU/startup limits. |
| Source/public readback | All 57 files matched; no mismatch. |
| Browser/hosted checks | Not completed: Chrome attachment and in-app-browser setup failed even after fresh sessions. No UI action or cloud Worker creation is claimed. |

Two qualification-harness errors were corrected after identifying their causes: the Docker copy initially omitted the existing ESLint configuration; a separate normal Next build followed by OpenNext `--skipNextBuild` omitted standalone output. Installed adapter source confirmed its `NEXT_PRIVATE_STANDALONE` setup. Letting OpenNext run the build resolved that bundle failure. No application feature defect or production fix is claimed.

## Evidence and continuation

Ignored evidence: `tmp/qlms-workers-build-1bfdf4a.log`, `tmp/workers-runtime-check.json`, archived candidate/source wrapper under `tmp/qlms-workers-source-1bfdf4a`, and read-only runtime helper `tmp/check-workers-runtime.py`. The new fictional API used a separate `tmp/workers-qualification-1bfdf4a.sqlite`, fixed dummy credentials and disabled dotenv loading. No original fixture, pilot record or live credential was used. The disposable Worker and API helper were stopped; image, scripts and SQLite evidence remain available.

Next restore working browser/tool transport, verify a scoped deployment route without exposing credentials, then use a clearly marked fictional Worker to measure actual cloud CPU/startup/errors. Complete login, role restrictions, direct receipt/refresh, logout/account switching, lost-reply recovery and CSV browser checks. Rebuild with the final HTTPS API origin and qualify CORS/private headers before opening the pilot. Keep the real-data cutover closed until the existing private setup/recovery/alerts/staff gates pass.

For the browser connection failure, [official OpenAI troubleshooting](https://learn.chatgpt.com/docs/chrome-extension#troubleshooting) recommends restarting the browser, confirming its extension/profile and Computer Use connection, and restarting the desktop app if needed. The next bounded attempt is restart Chrome, reopen Cloudflare in the same signed-in profile, restart Codex and return to this chat. This is an unverified troubleshooting step; the user has already granted browser control and no account reconnection or password disclosure is required.

Cloudflare D1 was discussed only. It uses SQLite semantics and Workers/HTTP access, whereas the current production backend requires PostgreSQL, locks and restricted roles. Keep Supabase for this pilot; D1 would require a separately planned conversion and backup/permission/money tests. [D1 overview](https://developers.cloudflare.com/d1/), [D1 limits](https://developers.cloudflare.com/d1/platform/limits/), [Supabase PostgreSQL](https://supabase.com/docs/guides/database/overview).

Useful later additions are Worker metrics, DNS/Universal SSL for an owned domain, and Turnstile if login abuse warrants it. No feature activation follows from that recommendation. [Metrics](https://developers.cloudflare.com/workers/observability/metrics-and-analytics/), [Universal SSL](https://developers.cloudflare.com/ssl/edge-certificates/universal-ssl/), [Turnstile](https://developers.cloudflare.com/turnstile/plans/).
