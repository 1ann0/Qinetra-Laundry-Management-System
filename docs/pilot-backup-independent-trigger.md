# Independent daily backup trigger — 16 October 2026

Operations source **dc47db29c02401a88b82fbb9375cd57a237573ea** passed exact CI **38944859612**. Source pin commit **0485450** passed the nine affected trigger/wiring checks. Workflow-only main **44fff87f0faac3b76dffadea47eba7da857ced07** is published with Render/CI skip markers; no application files were merged. Actual protected qualification **38950225528** passed admission, encrypted archive/authenticated Drive read-back and monitor completion. The practice Render deployment stayed unchanged.

**Activated at 22:13:37 Nairobi on 16 October:** the Owner privately installed `GITHUB_BACKUP_DISPATCH`; only secret name/type metadata was checked. GitHub `QLMS_INDEPENDENT_BACKUP_ENABLED=true` and the separate Worker's `0 19 * * *` Cron are active. Public and preview URLs remain disabled. The first nominal event is 22:00 Nairobi on 17 October; today's 22:00 slot had passed before activation. **Actual next-night timing and token acceptance by a real Cloudflare invocation remain unproved.** Keep the existing missed-run email monitor.

Cloudflare's separate Cron trigger calls only the existing GitHub backup workflow on main at 19:00 UTC (22:00 Nairobi). It holds no database password, Drive grant, archive key, monitor URL or shop records. The fixed dispatch body selects `daily-trigger` and names the actual UTC slot. The GitHub daily-enable switch, additional independent-trigger switch, current-slot validation, protected environment and serial concurrency all apply. A dispatch acceptance is not backup completion.

The existing scheduled retention check, encrypted archive/read-back and monitor completion must all succeed before either provider can suppress a second export. Manual qualifications still cannot supply this proof. No daily start ping extends the monitor grace. Missing/malformed public proof requests a fresh backup.

When independent triggering is enabled, the native 22:17 admission is disabled; native 22:00 and 23:17 remain. This keeps three ordinary opportunities/day and the existing 270-copy, 90-day/5 GB projection with 20% headroom. Before activation, all three native opportunities remain. Manual extra runs and growing archives remain outside the equal-size projection.

## Activation gates

1. Verify the exact operations source and workflow wiring in CI; pin that source in all three workflow checkouts. Publish only the workflow to main, preserving the separate application branches and avoiding Render auto-deploy.
2. Deploy the separate `qlms-backup-trigger` Worker with no HTTP handler and public/preview URLs disabled. It was initially deployed without Cron; the repository now records the activated daily Cron after private setup.
3. The human privately creates a GitHub fine-grained token for **1ann0/Qinetra-Laundry-Management-System only**, **Actions: read and write**, with a chosen expiry. No Contents, Administration, account-wide token or existing CLI-token extraction. GitHub cannot narrow this permission to one workflow; compromise could operate other Actions in this one repository. The Worker hardcodes the one workflow/main destination. Revocation disables this trigger; native triggers and independent missed-run emails remain.
4. The human enters that token directly into this Worker's encrypted secret named `GITHUB_BACKUP_DISPATCH`, outside Codex browser control. Never send it in chat or save it in tracked files. Install no backup credentials here.
5. Confirm only secret-name metadata, enable the independent repository switch, then set this Worker's Cron to `0 19 * * *`. Verify actual provider schedules. Allow propagation before judging the next nominal slot.
6. Observe a real Cloudflare scheduled event and actual GitHub archive/read-back/monitor steps for its named slot, then the later native duplicate skip. Record elapsed time against 22:00. Do not call it fixed from a manual invocation or HTTP 200/204 alone. Confirm failure/missed-run notices still reach the company inbox.

## Checks and rollback

Focused tests cover exact destination/body, no public handler, deadline/no redirects, safe provider failures, accepted responses, slot rejection, native/independent deduplication and manual qualification exclusion. Existing backup/budget tests remain required; no migration or shop workflow changes.

Rollback: disable the independent repository switch and remove the Worker's Cron. The native 22:17 admission automatically returns, retaining the original three native opportunities. Revoke its separate GitHub token privately. Leave the backup secrets, archives, monitor grace, daily-enable switch, app and database unchanged.

Limits: independent scheduling reduces correlated trigger delays; neither free provider guarantees an exact start time. GitHub runner queues can still delay a dispatched job. Keep the existing two-hour missed-run alert rather than masking a late run. Dispatch-token expiry is a maintenance task; never replace evidence of a real scheduled run with a qualification run.

Skills: Superpowers debugging/TDD/verification; Cloudflare and Workers best practices; Ponytail reused the existing protected backup pipeline. UI/UX: no staff screen changes. One active agent. The latest Owner priority is backup timing, then customer-return insights, then pickup/delivery and secure-cookie sessions.

Sources: [GitHub dispatch permissions](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event), [GitHub schedule limitations](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [Cloudflare Cron configuration](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
