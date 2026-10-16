# Actual scheduled backup, duplicate prevention and alerts

Verified 16 October 2026 from public workflow/run/step metadata and the actual GitHub summary. No raw backup logs, private configuration, credentials or record contents were read.

| Actual run | Nairobi time on 16 October | Verified result |
| --- | --- | --- |
| [38813186276](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38813186276) | Created 00:53:01; backup finished 00:54:07 | Actual `schedule`, main cd5d865. Public summary identifies `0 19 * * *` UTC and `New backup required: true`. Retention admission, encrypted export/authenticated Drive read-back and completion signal all succeeded. Scheduled start ping was correctly skipped. |
| [38816067605](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38816067605) | Created 01:17:20; admission finished 01:17:31 | Actual `schedule`. Summary identifies `17 19 * * *` UTC and `New backup required: false`. Admission succeeded; backup was skipped after existing scheduled proof. |
| [38821319500](https://github.com/1ann0/Qinetra-Laundry-Management-System/actions/runs/38821319500) | Created 02:04:32; admission finished 02:04:46 | Actual `schedule`. Admission succeeded; backup was skipped. This confirms a later event did not create another archive. |

The Owner explicitly confirms **both the company-inbox DOWN and UP emails arrived** for this late slot. This is actual missed-run/recovery delivery evidence, in addition to the earlier deliberate alert rehearsal. Email contents and links remain private.

The primary target was **22:00 Nairobi on 15 October**. Its backup finished **2h 54m 07s late**, beyond the configured two-hour monitor grace. Do not describe this as punctual scheduling or widen grace to make the result look healthy. The deployed catch-ups did not remove this provider delay. Their date-scoped duplicate prevention and the independent monitor did work.

**What is now proved:** unattended daily execution on a GitHub-hosted runner, actual archive authentication/read-back, retention admission, live duplicate prevention across later scheduled events, and actual missed-run plus recovery emails. The laptop was not observed powered off; the Owner-approved hosted-runner alternative remains the independence proof.

**What remains:** a backup within the agreed operating window. Evaluate one independent free Cloudflare Cron trigger for the existing GitHub workflow, keeping the same encrypted backup/retention pipeline. That requires a separate bounded design and narrowly restricted dispatch credential entered privately by the human; no new credential, Worker or trigger was created during this observation. Do not extract the CLI/connector token or repeat Drive/key/account setup.

Public evidence: [filtered run/step metadata](diagrams/evidence/qlms-scheduled-backup-catchups-20261016.json), screenshot **77** actual primary run, screenshot **78** actual catch-up summary. Screenshots visibly distinguish scheduled execution and skipped duplicate export; no social post was published.

Skills: Superpowers debugging/verification separates real scheduled proof from manual qualification and keeps the failed timing target visible. Ponytail reused the existing public metadata and safe summaries. UI/UX does not change staff screens here. The existing operations pin is 25a135a; current workflow-only main is cd5d865. Rollback/configuration remain in [the catch-up release note](pilot-backup-catchup-check.md). Learning/evidence notes record the new result; feature work must not silently claim all release hygiene complete.
