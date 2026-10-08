# Reusable Codex skills — updated 9 October 2026

Skills are instruction cards and optional tools, not new models or extra usage allowance. These third-party repositories were downloaded at pinned commits; relevant instructions and helper entry points were inspected. Installation is not a comprehensive security audit or proof of business results.

## Availability

Installed 22 skill folders in `C:/Users/1ann0/.agents/skills`, the official user-wide location. They can be used in local Codex chats for this Windows user across projects. On 5 October the UI, marketing and writing skills appeared in the next turn's skill catalogue; the 15 Superpowers folders remain explicit-only. Restart Codex if a skill is absent. They do not automatically transfer to ChatGPT web/mobile, another computer or a cloud executor. See [OpenAI skill discovery](https://learn.chatgpt.com/docs/build-skills).

Type `$` and select a skill, or name it explicitly in the prompt. Installation does not share one project's facts with another: keep each project's instructions and context in that project.

## What to use and how

| Skill | Simple explanation | Example request |
|---|---|---|
| Superpowers: `$systematic-debugging` | A detective finds why something broke before trying fixes. | Use $systematic-debugging to investigate this receipt error. Inspect the current code and report the cause before proposing a fix. |
| Superpowers: `$writing-plans` | Draw the building instructions before building something complicated. | Use $writing-plans for a bounded owner refund improvement, with exact files, risks and acceptance checks. Do not change code yet. |
| Superpowers: `$verification-before-completion` | Check that the toy actually works before saying it is finished. | Use $verification-before-completion to review the relevant evidence for this change. Separate local checks, student acceptance and deployment. |
| `$ui-ux-pro-max` | Put labels, buttons and messages where people can find them. | Use $ui-ux-pro-max to review this form's error feedback. Keep Qinetra's colours, FastAPI boundary and existing libraries. Suggest three improvements; no code changes yet. |
| `$product-marketing` | Decide who the product helps and which problem it solves. | Use $product-marketing to draft QLMS positioning for small laundry owners. Use only measured proof; mark unanswered questions. |
| `$seo-audit` | Help people find a public website in search. | Use $seo-audit on this public business website. Give the three most useful fixes and evidence. |
| `$social` | Turn a useful idea into posts people understand. | Use $social with Qinetra's content-studio guidance to draft three Instagram captions from these confirmed services. Draft only. |
| `$launch` | Plan how to introduce something when it is ready. | Use $launch to plan a small QLMS pilot announcement after its readiness gates pass. Zero spending and no publishing. |
| `$copywriting` | Explain the benefit and the next action clearly. | Use $copywriting for a future QLMS landing page using these verified facts. Do not invent time savings, testimonials or revenue claims. |
| `$no-ai-slop` | Remove fluffy words while keeping what you mean. | Use $no-ai-slop on this cover letter. Preserve all qualifications and facts; make minimal edits. |

Qinetra marketing and QLMS software marketing have different customers. Create separate project-specific `.agents/product-marketing.md` files when that work is requested. Do not treat the staff-only application as a public SEO target. The existing Qinetra content-studio instructions still govern brand and promotional terms.

## Superpowers scope and cost

All 15 Superpowers skills were installed: brainstorming, diagnosing-superpowers, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, receiving-code-review, requesting-code-review, subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans and writing-skills.

Each has `agents/openai.yaml` with `allow_implicit_invocation: false`. This prevents automatic selection from an ordinary prompt; explicitly requested skills can still recommend other skills. No full plugin bootstrap, session hooks, model configuration or automatic agent workflow was installed. Avoid `$using-superpowers` as the default for a small edit: it introduces the wider protocol. Prefer one named skill for one problem.

Use brainstorming/planning for uncertain features, debugging for unexplained failures, and verification for consequential completion claims. Full executing-plans/subagent-driven workflows require their own scope decision and can consume substantially more shared usage. Several helpers use Bash; their Windows execution, visual companion and multi-agent workflows were not exercised. The optional visual companion loads an external brand image unless telemetry is disabled. It was not started. Review and disable that tracking before any future use; its instructions are not permission to publish or expose data.

## UI tool check and limits

The UI skill includes its CSV data, references and Python search scripts. Its Claude-specific script prefix was adapted to its actual installed Codex path. Two read-only searches ran successfully: UX error-summary guidance and Next.js form guidance. No design-system files, packages or application code were generated.

Example using this checkout's working Python:

```powershell
& C:/Users/1ann0/qlms/tmp/test-venv/Scripts/python.exe C:/Users/1ann0/.agents/skills/ui-ux-pro-max/scripts/search.py 'error summary validation' --domain ux -n 1
```

In another project use its verified Python interpreter. Search results are suggestions, not architectural authority: one result recommended Next.js Server Actions, while QLMS already uses a FastAPI API. Existing architecture, accessibility, reduced motion and business rules take priority. Use a focused search for a small fix; a full design-system run is for a genuinely new design direction.

## Efficient workflow

5 October application: systematic debugging reproduced expired-session receipt failure and restricted-role clothing correction failure before fixes; verification-before-completion required fresh test/restore evidence. UI/UX guidance kept password recovery on the current page with the payment draft, and made login-limit instructions name the actual five-minute wait. No design-system replacement or extra UI library was needed. The user's later batching instruction replaces per-feature quiz pauses: complete essentials, then one final acceptance session before release.

The project's `AGENTS.md` owns the QLMS workflow. The approved 5 October plan uses brainstorming for uncertain improvements, systematic debugging for reproduced failures, verification before completion/release, UI/UX guidance for staff interactions, and provider skills for database/hosting changes. It retains one active agent and real-data-pilot-first release gates. These triggers do not make every skill mandatory for every task.

1. Give one goal, actual files or draft, constraints, desired output and passing criteria. State whether you want analysis or implementation.
2. Use one relevant skill, adding another only when it serves a distinct need. Don't load every reference or start parallel agents by default.
3. For marketing, establish accurate product context once, then reuse it. Review copy against real prices, capacity and measured results. Generic conversion examples are not Qinetra evidence.
4. For code, inspect current source, make the approved bounded change and run checks appropriate to its risk. A skill cannot replace acceptance evidence.
5. Keep drafts private until explicitly authorized to publish. Optional integrations, purchases, dependency changes and customer-data access are separate decisions.
6. After an increment, update the handoff. Start a fresh chat for a separate task using that handoff and exact files rather than pasting the whole history.

Medium reasoning suits routine UI integration; Low suits simple labels/docs; High suits payments, permissions and concurrency. Skills do not change the selected reasoning setting automatically or guarantee equal quality at a lower setting.

## Ponytail automatic plugin — 9 October 2026

Ponytail is a reminder to reuse the building blocks already here and finish the smallest complete solution. It does not replace Superpowers debugging/verification, UI/UX checks or QLMS release gates. Full is the default; Ultra requires an explicit request. One active agent remains the default, including when the SubagentStart hook is installed.

The official plugin is installed and enabled globally on this Windows user account: `C:/Users/1ann0/.codex/plugins/cache/ponytail/ponytail/5.1.0`. Its Git HEAD is `9cc65d03aa2da1db7121b912d03596409ee340b8` (5.1.0). The local marketplace at `C:/Users/1ann0/.codex/marketplaces/ponytail-reviewed/.agents/plugins/marketplace.json` pins the **plugin source** to that SHA; upstream's entry uses `main`. No shop dependency, model setting or paid benchmark was added. Existing plugins remain installed.

The only tracked-source adaptation sets `process.env.PONYTAIL_MAP='0'` inside the SessionStart command in `hooks/claude-codex-hooks.json`. This disables the optional repository map; its filesystem fallback does not honour Git ignores. Core hook scripts and skills are unchanged. `installation-provenance.json` alongside the installed plugin records source, adaptation and manifest hash. Reinstallation can replace this cache modification: reapply it, verify its hash and review changed hook definitions before use. No automatic update was configured.

The app's existing Codex CLI 0.160.1 reviewed and individually trusted only this plugin's SessionStart, UserPromptSubmit and SubagentStart hooks through `/hooks`; all three showed active with no review pending. No trust bypass was used. Another older `codex` on the escalated shell PATH is 0.144.1; use the verified app binary when checking this installation.

| Skill | When and why | Codex invocation |
| --- | --- | --- |
| Ponytail | Choose the smallest complete change; reuse existing helpers and retain security/accessibility. | `$ponytail:ponytail` |
| Review | Read a consequential diff and its callers before completion; report only demonstrated problems. | `$ponytail:ponytail-review` |
| Audit | A bounded, read-only assessment of pilot auth, money/retries, backup and release paths. | `$ponytail:ponytail-audit` |
| Debt | List documented shortcuts when they affect the next task; keep the master roadmap authoritative. | `$ponytail:ponytail-debt` |
| Gain | Explain the author's benchmark, with its limits; this does not measure our usage or business value. | `$ponytail:ponytail-gain` |
| Help | Show the command card. | `$ponytail:ponytail-help` |

Mode prompts: `/ponytail full`, `/ponytail lite`, `/ponytail off`, or the standalone phrase `normal mode`. An off prompt applies to the current session; new sessions default to Full. Review/audit are one-shot reports and must not edit code or change the active mode. Hook mode state can be shared between sessions in the same project; do not assume chat-level isolation. Restart the desktop app if the installed plugin is absent from a new local chat. Installation is not verified for another computer, mobile/web or cloud executors.

Fresh desktop checks confirmed automatically injected **Full** mode and no repository map in QLMS (`01a11dab-422f-78f3-be8d-e233d67eace8`) and the separate local System analysis and design notes project (`01a11daf-fd1d-7323-bafc-2802c73a1084`). All six skills appeared in both projects. Inspection of their recorded developer messages independently confirmed the mode line. An initial second-project chat (`01a11dac-0b94-7fe0-b4fd-1c1f043a36c1`) saw the skills but received no activation context; the fresh recheck passed without configuration changes. Its cause is unconfirmed. Do not promise every startup succeeds: if context is missing, explicitly select `$ponytail:ponytail`, inspect `/hooks` and retry a fresh chat. The verification chats were sequential, read no project files and made no changes.

Verification used isolated temporary state under ignored `tmp/ponytail-check-20261009`, without customer data. All **9 native Windows regression checks** passed, including the stalled-input exit and hostile-root command checks. The unchanged common suite passed in the existing Linux Docker image with networking off and source mounted read-only. **17 focused Codex checks** passed on Windows: two project scopes, Full startup with no map/status-line setup, mode changes, off/normal-mode, malformed/closed input, SubagentStart output, six skill entries and report-only mode preservation. No model calls were needed for these focused checks.

The combined native suite is **not all green**: `tests/hooks.test.js:319` compares an unescaped Windows path with the JSON-escaped command in Claude's status-line nudge. The installed Codex path skips that Claude-only block. Preserve this failure rather than altering upstream tests to claim a pass; Linux common checks and Windows Codex checks provide separate evidence. Initial shorter test runs timed out; the complete sequential run retained all upstream hang guards. These results qualify the tested hooks, not every third-party workflow.

### First focused pilot audit

Assumed load: one shop, a few concurrent staff, one daily hosted backup. This was source inspection, not a fresh production or database audit. Money/auth helpers and relevant tests were traced; no new application defect or worthwhile speculative refactor was established in the reviewed paths.

| Required before daily reliance | Concrete case and source evidence | Smallest next step |
| --- | --- | --- |
| Unattended backup and recovery | `.github/workflows/pilot-backup.yml:19` deliberately gates execution; a Drive chat connection cannot supply the offline credentials required by `backend/ops/backup_job.py:23`. Connected Drive alone does not produce a nightly backup. | Complete the existing dedicated consent/private credential and separate-target restore checks in `docs/hosted-backup-check.md`; keep the workflow disabled until qualified. |
| Delivered failure/missed-run alerts | `backend/ops/backup_job.py:67` stores success in the local runner folder; the workflow neither persists a remote heartbeat nor delivers an alert. An omitted schedule event leaves no new job to report its own absence. | Qualify a persistent success record and an independent overdue check, plus a delivered failure alert, within the existing zero-spend plan. Owner alert settings alone are not alert delivery. |
| Retention handling | `backend/ops/backup_job.py:72` records 90 days but explicitly reports `automatic_deletion: False`. Day 91 does not expire an archive. | Rehearse conservative expiry handling for verified QLMS archives in the private destination, preserving a recoverable recent copy; then qualify it before activation. |
| Paired hosted release | `docs/cloudflare-qualification-check.md` distinguishes local success from open hosted CPU/browser checks; `docs/pilot-release-status.md` keeps runtime/backup credentials and staff acceptance open. Local builds do not qualify the shop. | Continue hosted frontend/private API configuration, fictional acceptance and coordinated release in the existing order. Cloudflare account setup is already complete. |

Retain DB-backed login throttling and live account/version checks (`backend/login_throttle.py`, `backend/auth.py`); decimal whole-order discount policy (`backend/discount_policy.py`); request fingerprint/advisory-lock/replay checks before new validation (`backend/transaction_safety.py`, `backend/main.py`); and preserved uncertain browser attempts (`frontend/src/lib/pending-save.js`). Relevant existing tests include `backend/tests/test_launch_security.py`, `test_discount_policy.py`, `test_refunds.py` and `frontend/tests/pending-save.test.mjs`. They were inspected, not rerun for this workflow-only change. The protected save-rejection draft remained unchanged.

Not checked: full application regression, every router/screen, live credentials/provider state, actual staff acceptance, cloud alerts/recovery or cutover. Review/audit reports do not authorize those operations. Plugin/doc changes need no shop deployment. The author's [Claude Code benchmark](https://github.com/DietrichGebert/ponytail/blob/9cc65d03aa2da1db7121b912d03596409ee340b8/benchmarks/results/2026-10-07-agentic.md#limitations) does not establish equivalent QLMS or Plus savings.

## Earlier skill installation provenance

| Repository | Pinned commit | Installed subset |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | All 15 `skills/*` folders |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `477bcb28c9812b385cb51a4605ddf30d7b2266e2` | `.claude/skills/ui-ux-pro-max` only |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | `dda3841f0b294e01e93b1541486beefbfab0915e` | product-marketing, seo-audit, social, launch, copywriting |
| [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) | `000650b156983f5159695b441477f4e63b25dc85` | `skills/no-ai-slop` |

Every installed folder has `installation-provenance.json` identifying its source and local adaptations, plus the upstream root licence where available. Review snapshots and installer helpers are ignored under `tmp/skill-review-20261005`; they are not application dependencies. No updates run automatically. Re-review upstream changes before replacing these pinned versions.
