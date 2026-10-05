# QLMS data and recovery contract

Updated 5 October 2026. The separate empty pilot project/schema is provisioned; restricted roles remain NOLOGIN. Local encrypted restore is verified, but actual credentials, daily backup/cloud upload, alerts and operational recovery are not completed. See [current evidence](docs/pilot-essentials-check.md), [operations](backend/ops/README.md) and [the roadmap](IMPLEMENTATION_ROADMAP.md) for D1/R1 gates.

## Data meanings

| Record | Meaning and protection |
| --- | --- |
| Staff user | Individual identity, active flag, role and session version; password hash never appears in API responses |
| Customer | Name and normalized/display phone; shared numbers need explicit selection and are not automatic identity merges |
| Catalogue | Owner-managed current prices/options; changing it does not reprice saved work |
| Discount policy/change | One shop-wide employee ceiling, initially 0%; attributed before/after percentages and revision. Accepted order prices and save references remain valid after a policy change |
| Order/service line | Ticket, customer link, saved price/quantity/discount and promised work; preserve attributed corrections |
| Physical item/handling | Counts, references, condition, holds and outsourced handover/return; not interchangeable with billable kg/units |
| Payment | Staff-confirmed money received, method and receipt date; preserve original entries |
| Correction/refund | Attributed event, reason and original record; distinguish wrong entry, actual money returned and service-charge reduction |
| Save reference | Binds an accepted request to its result; retained while an outcome is unknown |

Use decimal money and explicit Nairobi business dates. Booked value and receipts can fall on different dates. Income/cash movement is not a profit calculation. The local refund increment derives debt = max(net charge - net payments, 0), refund due = max(net payments - net charge, 0). Service refunds reduce the charge; excess-payment returns do not. Old refunds keep an unknown purpose, with no guessed charge reduction. See [refund meanings and checks](docs/refund-check.md).

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

## Retained report and AI requirements

The [roadmap's reporting/AI section](IMPLEMENTATION_ROADMAP.md#retained-pilot-priorities-and-approved-reportingai-additions) owns the approved later work. Excel/CSV downloads are dated review snapshots, not editable database replicas or backups. Booking dates, payment dates, return dates and current debt/queue state have different meanings; preserve them explicitly. A separate reviewed analysis pack excludes contacts, identifiers and free text and must address sparse-group identification before external AI use. No external AI transfer or additional customer-data collection is implemented by the discount increment.
