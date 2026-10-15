# Backup trigger resilience

**Goal:** Retain nominal 22:00 Nairobi and recover from a delayed/dropped trigger without another account, secrets transfer, service or paid tier. One active agent, exact-source checks, then a workflow-only main change; no app/API/schema release.

**Design:** Keep `0 19 * * *` UTC; add catch-up opportunities at 19:17 and 20:17 UTC (22:17 and 23:17 Nairobi). Before using the protected backup environment, an admission job reads only public GitHub run/job metadata. It skips another export only if a scheduled main run in the current 19:00 UTC-to-next-19:00 window completed the existing archive/read-back, scheduled retention admission and monitor-completion steps successfully. A manual run, overall success with skipped steps, old run, current run or missing proof never suppresses a backup. The workflow concurrency group remains serial and cancellation remains disabled.

This is bounded improvement within GitHub, not an independent scheduler or an exact-time promise. All three triggers can still be delayed/dropped together; retain the separately qualified company-email missed-run monitor. If actual timing remains unacceptable, qualify an independent free trigger separately; its restricted dispatch credential would require private human installation, not extracting the existing connector/CLI credential.

**Existing code reused:** standard-library public HTTP client from `ops.release_smoke` (no auth/environment secrets), existing backup job, encrypted Drive read-back, complete-folder safe retention and 20% storage headroom. No new Drive listing/marker format, database permissions or recovery keys.

**File map and checks:**

- `backend/ops/backup_schedule.py`, `backend/tests/test_backup_schedule.py`: public proof admission, bounded metadata work, UTC/Nairobi midnight/late-trigger boundaries, invalid/unavailable provider metadata chooses a fresh backup. Maximum ten candidate jobs; no token or private configuration loaded.
- `backend/ops/backup_budget.py`, `backup_job.py` and existing tests: budget a worst case of three scheduled copies/day if duplicate suppression cannot establish prior success. Local private configs retain default one-copy projections. Ninety-day retention and 5 GB/20% headroom stay unchanged. Manual extra runs and data growth remain outside this equal-size projection; actual Drive capacity is still checked before each upload.
- `.github/workflows/pilot-backup.yml`: admission before protected credentials, three cron opportunities, exact tested operations pin and maximum-three-copy setting. Send start only for manual qualifications so a scheduled catch-up start cannot extend the nominal monitor grace. Actual successful exports still send completion; failures still send failure. Duplicate-skipped runs send no success ping.
- Record run/step proof, source pins, remaining actual-schedule observation and rollback in handoff/operation notes.

**Sequence:**

1. [x] Write and observe failing admission/budget/job-integration tests first; implement the minimal helpers and budget extension.
2. [x] Initial source `8d806b7`: 56 focused operations checks, redacted scan and exact-source CI `38744010222` passed. Subsequent local repository-proof hardening still needs its own scan/commit/fresh CI; see the [deployment handover](../../pilot-backup-catchup-check.md).
3. [x] Hardened pin `25a135a` passed CI `38788784374`; whole candidate `4f94ca6` passed CI `38789214685`; workflow-only main `5fcb488` was scope/hash verified. Application history and divergent local main were preserved. Post-change hosted smoke `38790277891` passed all jobs.
4. [ ] Run the existing manual cloud qualification after deployment; inspect safe run/step metadata only. Exercise admission using public historical proof and fictional boundary cases. Observe a real scheduled invocation when due; no forced past timestamp or manual dispatch counts as that proof.

**Current state:** the temporary automatic-review failure recovered through the same reviewer; no bypass. Catch-ups are active, and actual cloud qualification `38789560522` passed. Step 4's natural scheduled-event/timing observation remains open; the manual qualification is not a substitute for it. See the current release check rather than older prepared-state paragraphs.

**Acceptance and limits:** Automated proof must reject a successful-looking workflow without actual completed archive/retention/monitor steps. When metadata is rate-limited or malformed, request a fresh archive rather than silently skipping. With a 113,262-byte fictional archive, three possible copies/day × 90 days is 30,580,740 bytes; this is a fixture projection, not measured live storage or a growth forecast. A successful previous read-back is historical proof; admission does not re-download the earlier archive or guarantee it was not subsequently removed outside QLMS. Every actual new export still performs authenticated Drive read-back.

**Rollback:** Restore the previous default-branch workflow (one nominal cron, no admission, old `c06dc6290394d607dccc927c2046a2a2bb77d104` operations pin), leaving all archives and private settings intact. New budget arguments default to prior behavior; no database migration. `[skip render]` on a workflow-only commit must be qualified against Render's documented skip behavior before pushing main; inspect service metadata afterwards. The original practice service and pilot app must not be redeployed by this operational change.

**Skills:** Superpowers bounded brainstorming/planning/TDD/debugging/verification; Ponytail reuses the existing public HTTP and backup/retention paths instead of adding a second Drive protocol; UI/UX review confirms no staff screens change. No agent delegation. Private credentials stay out of tool input/output.
