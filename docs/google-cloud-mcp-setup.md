# Local Google Cloud MCP for QLMS

The user requested this local integration on 12 October 2026 to reduce manual Cloud Console work. It is independent of the QLMS app and does not replace the separate Drive consent needed by an unattended backup runner.

## Installation and boundaries

- Google-published `@google-cloud/gcloud-mcp` is pinned to **0.5.3**, installed under `C:\Users\1ann0\AppData\Local\QLMS-tools\gcloud-mcp`. QLMS application dependencies are unchanged.
- Google Cloud CLI **588.0.0**, including its Python runtime, is extracted under the same tools directory. Its official Windows archive SHA256 is `9e00e3c9b042f732e29eb7ca6095fdb44bda03938013274a148b5c5f95a6ec92`.
- `gcloud-mcp-allowlist.json` permits only `version`, `projects describe`, `services list` and `services enable`. This command policy does not itself restrict project arguments or the Google account's IAM authority. Every actual project/API command must explicitly name `qlms-backup-automation`; enable only `drive.googleapis.com` and `picker.googleapis.com` for this task.
- Do not use HTTP debug logging, token-file flags, impersonation, credentials, auth/token commands, billing, resource creation/deletion or another project. Credentials are kept in a separate user/System-only `gcloud-private` directory. Never read it, copy its files or expose its contents to chat.
- This is a local stdio MCP. Do not enable the billing-dependent Cloud CLI Execution API for Google's remote CLI MCP.

Official references: [Google's MCP repository](https://github.com/googleapis/gcloud-mcp), [versioned CLI archives](https://docs.cloud.google.com/sdk/docs/downloads-versioned-archives), [Codex MCP commands](https://learn.chatgpt.com/docs/developer-commands#codex-mcp).

## Private human installation and sign-in

The human reports that the tools directory is absent in their PowerShell even though it exists in the agent execution environment. Do not call installation on the human's computer verified. Run the reviewed [setup script](scripts/install-google-cloud-mcp.ps1) in your own PowerShell **outside Codex**. It resolves that terminal's local paths, installs the checksum-verified CLI and pinned MCP, registers only `gcloud-qlms`, and opens Google's private sign-in. Its version check uses a separate empty configuration; it does not inspect existing credentials.

The execution policy below applies only to this PowerShell process; it does not change the machine's saved policy. Select the existing Qinetra account in Google's browser page, keep the page and terminal output private, and stop if payment or billing activation is requested. Do not send passwords, authorization codes, URLs, tokens or raw logs.

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File 'C:\Users\1ann0\qlms\docs\scripts\install-google-cloud-mcp.ps1'
```

The first run can take several minutes to extract the CLI. Report only the final PASS/FAIL line. After the private sign-in PASS, restart Codex and continue the same chat. The first authenticated checks are the expected project identity and enabled API names. Actual backup authorization, export, restore, retention, alerts and scheduled execution still require their own proof.

## Verification record

Verified **in the agent execution environment** on 12 October 2026: official archive checksum, CLI `588.0.0` version, pinned MCP `0.5.3` version, Codex registration/enabled readback, stdio handshake, tool discovery, a real MCP CLI-version call and denial of `auth print-access-token` all passed. This is not proof of installation visibility in the human's terminal. The MCP check used an empty test configuration and no Google login. Native Windows extraction skipped six auxiliary gsutil documentation/test entries; these were completed from the same verified archive using .NET ZIP extraction before the version/handshake checks.

After the human's final setup **PASS** and restart on 12 October, `mcp__gcloud_qlms` is exposed in this chat. Authenticated MCP readback, explicitly selecting `qinetraian@gmail.com` and `qlms-backup-automation`, confirms the project name **QLMS backup automation** and lifecycle **ACTIVE**. Separate enabled-service queries initially returned neither required API. The authorized enable operation completed successfully; independent follow-up queries now report both `drive.googleapis.com` and `picker.googleapis.com` as **ENABLED**. No billing activation, paid resource, app deployment or backup schedule activation was performed.

Installation/sign-in/project/API verification is complete. Do not repeat it. The Google Auth platform branding, production consent setting, Desktop client and private backup-runner grant remain separate human steps. No Google credentials were read or requested in chat.

For MCP 0.5.3, query one API per `--filter=config.name:API_NAME` argument. Its command linter split the attempted multi-value filter containing a space; that failed read performed no mutation. Keep explicit account/project arguments and the existing narrow command policy.

Earlier sign-in attempts returned CommandNotFound. The human's `Test-Path` returned False, and they reported the tools directory absent while the agent environment reported it present on `DESKTOP-HEFFC86`. The precise environment/machine mismatch remains unconfirmed; the human-run setup's final PASS supersedes that pending installation step. Its parser/prerequisite checks passed, and its redirected-terminal guard refused execution before installation/sign-in. Preserve that history without treating a guessed typo as the cause.
