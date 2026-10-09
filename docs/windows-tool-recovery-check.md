# Windows terminal/browser recovery — 9 October 2026

Current state: after the user reopened Codex, ordinary terminal startup passed with `SANDBOX_OK`, exit 0 and the expected workspace. Subsequent normal source reads and fictional API/database checks also passed. Browser interaction works for local QLMS qualification; some Chrome commands and the download observer still time out. The approved temporary `unelevated` setting remains in effect. QLMS release work remains open.

## Verified diagnosis and attempted repair

- Ordinary exec and browser startup originally shared `helper_unknown_error: setup refresh had errors`.
- The dated sandbox log identifies runtime read/execute validation on `node_repl.exe` failing with Windows sharing violation `os error 32`. A user-profile permission warning is nonfatal; runtime validation is the recorded fatal step.
- Windows reports Windows 11 Pro, version 10.0.22621. The desktop binary reports Codex CLI 0.162.0-alpha.2.
- The user ran the supported elevated setup with Codex closed. The setup marker was updated at 15:48 Nairobi. After reopening, fresh runtime processes were present and the same validation failure recurred. The marker update alone is not proof that every runtime check passed.
- Resetting this chat's CUA/Node tools did not fix ordinary exec. No unrelated processes were killed.

## Approved fallback and fresh checks

OpenAI documents `unelevated` as a legacy fallback with ACL filesystem restrictions, weaker network isolation and no denied-read-path support. The user explicitly approved that temporary tradeoff. In `C:/Users/1ann0/.codex/config.toml`, only `[windows] sandbox` changed from `elevated` to `unelevated`; other configuration was preserved and exact readback checked. This did not select a different thread permission profile.

| Check | Result |
| --- | --- |
| Official one-command MXC compatibility probe, managed workspace profile | Failed: native MXC is unavailable on this executor. No saved setting changed. |
| Explicit unelevated read-only startup probe | Passed, exit 0: `RESTRICTED_SANDBOX_OK`. |
| Fresh CLI using the saved configuration, managed workspace profile, no mode override | Passed, exit 0: `CONFIGURED_SANDBOX_OK`. |
| Fresh CUA kernel and browser inventory | Passed after reset. |
| Existing Cloudflare tab/accessibility read and navigation | Passed: Workers plans to Workers & Pages; loaded inventory showed no projects and zero requests. No project or grant created. |
| Playwright DOM read after navigation | One timeout; accessibility reading succeeded afterwards. No broad browser clearance claimed. |
| Existing normal `exec_command` after app reopen | Passed, exit 0: `SANDBOX_OK`, correct workspace, then repeated normal repository/API/SQLite checks. The setup-refresh startup failure is resolved in the approved fallback. |
| Local browser interactions after app reopen | Owner/employee login, role routing, order entry, lost-reply refresh/retry, receipt, customer history, owner Finance and export feedback passed. Browser download-file observation timed out; this is a separate remaining tool limitation. |

## Read-only change review

What this change does: Selects the documented temporary Windows fallback for fresh executors. It preserves the rest of Codex configuration and QLMS code/data.

Expected use is one active local QLMS chat. Review covered the selected config field, actual installed CLI/help, official configuration semantics, fresh CLI callers, CUA startup/navigation and the failing existing terminal caller.

The terminal startup blocker is cleared by fresh evidence after app reopen. Browser commands can still fail intermittently; inspect current state after a timeout before assuming the action did not happen. A timed-out password-resume click did complete, and the next snapshot confirmed the same owner dashboard.

Verdict: the approved fallback restores ordinary execution and usable browser interaction. It does not establish that every browser capability is reliable.

Not checked: sandbox implementation source, denied-read protection (unsupported in the approved fallback), full browser workflow coverage, hosted CPU or real-data cutover. The weaker isolation remains an approved temporary operational risk.

## Next continuation

Continue QLMS qualification with ordinary terminal and documented browser APIs. Do not repeat account setup or elevated provisioning. The download observer reset the browser kernel; numeric browser IDs changed afterwards. Match the existing Chrome profile/extension identity from fresh inventory rather than trusting the old number. An unintended new signed-out Brave review tab carried no credentials and received no login; it is disposable.

Return to `elevated` only after a suitable repair/build is qualified: restore `[windows] sandbox = "elevated"` and verify both tool paths. Do not silently reduce additional permissions or use a full-access preset as a repair.

Preserve the unpublished Cloudflare note, unfinished save-rejection draft, practice data and private setup file. No app code, credential, external deployment, remote database or account connection changed.

[Official Windows sandbox guidance](https://learn.chatgpt.com/docs/windows/windows-sandbox#troubleshooting-and-faq). Keep raw sandbox logs and `.sandbox-secrets` private.
