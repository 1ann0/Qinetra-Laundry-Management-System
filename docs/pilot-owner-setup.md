# Private first Qinetra Owner account

The frontend is now at **https://qlms.qinetra.workers.dev/login**, paired with the pilot API. The first Owner has already been created privately; do not run bootstrap again. Real customer entry remains closed until backup/recovery and staff/device qualification pass. The bootstrap instructions below are retained for recovery/reference.

## Run in your own PowerShell outside Codex

Database password setup is already complete. Do not reset it, reconnect accounts or paste credentials into chat. The existing private runtime file remains the input; the agent must not read or run it.

```powershell
Set-Location 'C:\Users\1ann0\qlms\backend'
& '..\tmp\test-venv\Scripts\python.exe' -m ops.pilot_owner_setup
```

The wrapper reads only the existing `ops/private/.env.pilot-runtime`, disables implicit `.env` loading, and checks the exact pilot project, TLS URL, restricted role, schema, limited role authority and catalogue-only counts before invoking `create_owner.py`. It does not use administrator credentials or modify the practice project. It refuses noninteractive execution and an already-populated pilot.

Enter your chosen Owner username, password and confirmation privately. Password input does not echo. Use fresh credentials and keep them privately for the Qinetra owner. If password confirmation/validation fails, no account is saved. A connection failure can leave an uncertain outcome: check privately whether an Owner already exists before repeating; do not assume a failed reply means no save.

Success ends with:

`PASS: first pilot Owner created in the verified restricted pilot.`

Report only that PASS, or the safe FAIL line. Do not send the username/password, raw diagnostics, connection URL or private file contents.

## Sign in and verify privately

Open <https://qlms.qinetra.workers.dev/login> yourself. Enter the new credentials without browser automation observing the form. Do not enter real customer details yet.

1. Sign in as Owner. Dashboard, Finance, Staff and Shop setup should be accessible.
2. In Shop setup, confirm the copied 22 services and 30 garment types and their actual prices/options. Operational customer/order/payment lists should still be empty.
3. In Staff, privately create a named Employee account for each actual staff member. On the work Android phone, sign in as Employee and confirm Finance/Staff/Shop setup management is denied.
4. Keep Owner use on the Owner's device and Employee use on the work phone. Both use the same pilot API/dataset; this is online operation.

Report only whether Owner sign-in/catalogue and Employee role checks passed. Recovery, fictional-data staff rehearsal on a separate environment and go-live approval remain open.

## Developer evidence

Seven new isolated tests plus ten existing private-setup tests passed on 11 October. They cover wrong destination/privilege, weak signing secret, TLS/query tampering, unexpected operational records, noninteractive input, disabled implicit dotenv loading and sanitized failure output. All credentials in tests are fictional. The agent has not executed this command against the actual private file or created a real staff account.

The user subsequently reported creation; a metadata-only check confirmed one active Owner, zero Employees and zero customers/orders/payments, with 22 services and 30 garment types. No usernames, password hashes or private credentials were retrieved.
