# Reusable Codex skills — installed 5 October 2026

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

The project's `AGENTS.md` owns the QLMS workflow. The approved 5 October plan uses brainstorming for uncertain improvements, systematic debugging for reproduced failures, verification before completion/release, UI/UX guidance for staff interactions, and provider skills for database/hosting changes. It retains one active agent and real-data-pilot-first release gates. These triggers do not make every skill mandatory for every task.

1. Give one goal, actual files or draft, constraints, desired output and passing criteria. State whether you want analysis or implementation.
2. Use one relevant skill, adding another only when it serves a distinct need. Don't load every reference or start parallel agents by default.
3. For marketing, establish accurate product context once, then reuse it. Review copy against real prices, capacity and measured results. Generic conversion examples are not Qinetra evidence.
4. For code, inspect current source, make the approved bounded change and run checks appropriate to its risk. A skill cannot replace acceptance evidence.
5. Keep drafts private until explicitly authorized to publish. Optional integrations, purchases, dependency changes and customer-data access are separate decisions.
6. After an increment, update the handoff. Start a fresh chat for a separate task using that handoff and exact files rather than pasting the whole history.

Medium reasoning suits routine UI integration; Low suits simple labels/docs; High suits payments, permissions and concurrency. Skills do not change the selected reasoning setting automatically or guarantee equal quality at a lower setting.

## Installation provenance

| Repository | Pinned commit | Installed subset |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | All 15 `skills/*` folders |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `477bcb28c9812b385cb51a4605ddf30d7b2266e2` | `.claude/skills/ui-ux-pro-max` only |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | `dda3841f0b294e01e93b1541486beefbfab0915e` | product-marketing, seo-audit, social, launch, copywriting |
| [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) | `000650b156983f5159695b441477f4e63b25dc85` | `skills/no-ai-slop` |

Every installed folder has `installation-provenance.json` identifying its source and local adaptations, plus the upstream root licence where available. Review snapshots and installer helpers are ignored under `tmp/skill-review-20261005`; they are not application dependencies. No updates run automatically. Re-review upstream changes before replacing these pinned versions.
