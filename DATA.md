# QLMS data and recovery contract

Approved requirements, 28 September 2026. Production provisioning, backup automation and restoration are not yet completed. See [the roadmap](IMPLEMENTATION_ROADMAP.md) for D1/R1 gates.

## Data meanings

| Record | Meaning and protection |
| --- | --- |
| Staff user | Individual identity, active flag, role and session version; password hash never appears in API responses |
| Customer | Name and normalized/display phone; shared numbers need explicit selection and are not automatic identity merges |
| Catalogue | Owner-managed current prices/options; changing it does not reprice saved work |
| Order/service line | Ticket, customer link, saved price/quantity/discount and promised work; preserve attributed corrections |
| Physical item/handling | Counts, references, condition, holds and outsourced handover/return; not interchangeable with billable kg/units |
| Payment | Staff-confirmed money received, method and receipt date; preserve original entries |
| Correction/refund | Attributed event, reason and original record; distinguish wrong entry, actual money returned and service-charge reduction |
| Save reference | Binds an accepted request to its result; retained while an outcome is unknown |

Use decimal money and explicit Nairobi business dates. Booked value and receipts can fall on different dates. Income/cash movement is not a profit calculation. After truthful refunds are implemented: debt = max(net charge - net payments, 0), refund due = max(net payments - net charge, 0). Do not infer the purpose of old refund records.

## Environments and access

- Create a separate Supabase project for genuine Qinetra data only if a free slot is available. A named schema in the old project is not the approved substitute. Preserve old public/qinetra_live records until the owner classifies them.
- Keep local fixtures, tests, preview URLs, credentials and databases separate. Never point a test runner at a shop connection string. Label trial/demo environments clearly.
- Browser roles receive no application-table access. FastAPI uses a restricted runtime login; migration/admin credentials stay separate. Verify schema, revision and permissions before startup/cutover.
- Employees retrieve the operational customer/order records needed for work. Finance, exports, account administration and corrections remain owner-controlled according to the actual API. Later delegated permissions require explicit design.
- Owner signs off prices, real accounts and opening clothes/payments/debt. Historical opening receipts must not become today's income or a second collection request.

## Recovery requirements

The agreed targets are daily encrypted database exports, an independent copy, no more than one day reconstructed using retained receipts, and restoration within four working hours. They remain unproved until a timed exercise passes.

Before real-data entry, record the responsible person, independent destination, backup retention, encryption/key recovery and alert contact. Keep keys apart from backup files; verify the owner can recover without the developer's current laptop/session. No paid storage or new sharing is implied by this document.

Run a restore into a separate database. Check migrations, record counts, relationships, recent tickets, corrections, balances, Finance and login. Record backup age, start/end time, failures and reconciliation of writes after the backup. A CSV or same-provider snapshot alone is not the independent database backup.

Stop new trial entry if backups fail or restored money/records disagree. Do not overwrite the live database or replay uncertain payments as a recovery shortcut.

## Trial, retention and exit

Keep receipts alongside QLMS for the first ten trading days. At close, compare tickets, actual payments/refunds, balances and collections; resolve unknown save outcomes before transcription. Use temporary paper references during an outage and reconcile once.

Agree customer-record retention and access/export/deletion handling before operational dependence; do not implement automatic deletion using an invented retention period. Restrict logs, exports and backups as customer data. Use fictional or anonymized examples for demonstrations and public proof. Future client software expiry must not accidentally block legitimate record export/recovery.
