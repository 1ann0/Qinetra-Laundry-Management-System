# Pilot release status — 8 October 2026

The August demonstration is still deployed. The modern pilot candidate is now published and verified on GitHub, but the real-data pilot has not been opened. Continue only the setup and release work below; the creator console, new business features and deep teaching sessions remain after the pilot.

## Verified current state

- Candidate `1bfdf4a3b607a3349769fe3c4b46c64e0fb1790b` is published to `codex/transaction-save-safety` with the user's explicit public-publication approval. Remote branch SHA matches. GitHub `main` remains `5da24e577e6c373ca79b7318ded9c50e1d983a45`.
- [GitHub run 37808811073](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/37808811073) completed successfully for that exact candidate. Both jobs passed: backend/PostgreSQL/schema/recovery; frontend tests/lint/build. This clears remote verification, not production setup or staff acceptance.
- Render was read in the user-confirmed My Workspace. `qlms-backend` still reports a live `5da24e5` deployment, automatic deployment of `main`, root `backend`, request access logs enabled by its start command and health check `/`. It is on the free plan. Candidate-specific log/privacy and readiness configuration must be coordinated with release.
- Fresh pilot reads found zero staff accounts, customers, orders and payments; 22 services and 30 garment types. Both restricted database roles remain NOLOGIN. The practice records were not imported or changed.
- The business Drive identity/private folder and encrypted disposable upload/readback are verified. Both existing plugin connections remain intact. User choices are resolved: 90 days, 22:00 Nairobi with the PC off, separate owner/technical-maintainer key copies, 5 GB reported free space. No unattended grant or running backup/alert schedule exists yet.
- The Vercel dashboard opened at its login page. Automatic approval review initially blocked its GitHub sign-in route; the user then explicitly approved that existing sign-in. The GitHub browser session is signed out, so the tab is retained for the user to finish login privately. Actual Vercel plan remains unknown; no authenticated login or hosting change occurred.

## Remaining work, in order

| Work | Completion evidence |
| --- | --- |
| Private pilot setup | Actual restricted runtime/backup TLS connections to `qlms`, fresh signing secret and privately entered first-owner/staff credentials. Verify schema/permissions/readiness; preserve the demonstration. |
| Real backup and recovery | Dedicated unattended Google consent for the verified business destination; real encrypted export/upload/readback; separate-target restoration; owner/maintainer recovery without this machine; measured archive/quota and qualified 90-day expiry handling. |
| PC-off operation | Authenticated hosted execution targeting 22:00 Nairobi, delivered failure and missed-run alerts, with schedule delays accounted for. The workflow remains disabled until these pass. |
| Hosting and paired release | Verify a suitable commercial frontend plan within zero spend; qualify the exact candidate on HTTPS with private headers, CORS, trusted proxy, readiness and a fresh pilot frontend origin. Rehearse the first-release receipt fallback and record actual deployment IDs. |
| Final acceptance and cutover | One fictional staff session covering time/contact, sessions, clothing/outsourcing/custody, money/CSV and daily close; then concrete cutover approval, coordinated deployment and live owner/employee smoke checks before real entry. |

The copied real catalogue needs no re-entry. Drive plugin account setup and the resolved operating choices need no repetition. Remote CI is complete for `1bfdf4a`; do not rerun the same local suites solely to restate that result.

## Storage

The full small fictional archive measured 103,574 bytes. Ninety equal-size copies use about 9.3 MB, or 0.19% of the user's reported 5 GB. A 10 MB daily archive would use about 0.9 GB for 90 copies; 50 MB would use 4.5 GB. These are capacity calculations, not a forecast of actual trading-data growth. [Hosted backup evidence](hosted-backup-check.md) records the measurements and activation limits.

## Publication and release boundary

The initial branch push was rejected by automatic approval review because the complete 47-commit public export needed explicit authorization. The user then approved that exact candidate and branch; the push and independent remote-SHA check succeeded. No merge into `main`, provider deployment, credential/role change, real-data write, scheduler activation or delivered alert occurred.

The unrelated unfinished `docs/save-rejection-check.md` remains unstaged. Follow [pilot-release-runbook.md](pilot-release-runbook.md) for the coordinated cutover; August code is not a compatible rollback after modern correction/refund records.
