# Customer returns — 16 October 2026

Owner-approved next feature after the backup timing work. Backup activation is parked only at private installation of its narrow dispatch credential; the existing schedule remains active.

Small extension of existing Owner Reports, not a separate CRM. Dashboard → Customer returns; Reports → Customer returns. Search name/phone, choose last-visit group and dates, open a customer's existing history, download the same filtered Excel/CSV snapshot. No schema migration, new dependency, automatic message, discount or marketing attribution.

Visits are distinct non-cancelled booking dates through today in Nairobi; several tickets on one date count as one visit. Payments, collection, registration-only profiles and future bookings do not establish visits. Groups are within 7, 7–29, 30–89, 90+ days and no recorded visit. New means first recorded order, with the pilot's limited history clearly identified. Weekly counts start Monday, monthly on the first. Dates filter new/repeat counts; last visits remain current. All counts respect search/group; no customer counts are labelled KES.

Follow-up guidance asks the Owner to check existing laundry/issues, then consider a welcome personal reminder. It does not assume a customer is lost after seven days or invent contact permission. The existing customer-history screen remains the review destination.

Checks: hand-calculated fixtures cover Nairobi midnight, 7/29/30/89/90-day boundaries, same-day duplicates, cancellation, future orders, registration without visits, new/repeat counts, search/group filters, blank Excel cells, literal wildcard search, explicit oversize rejection, Owner-only JSON/Excel/CSV and private headers. PostgreSQL snapshot/export coverage is included. The shared binary-download allowlist and numeric display tests include returns.

Release gates remain exact candidate CI, fresh build/phone review, paired deployment/public smoke and a recorded source/API pair. No live fictional records. Actual Android file locate/open remains human acceptance if not performed.

Rollback: restore the previous frontend while retaining the compatible API; no tables or existing records change. If this report endpoint is removed, new report links stop working but operational intake/payment/corrections remain unchanged. Existing pending saves and account/API destinations are untouched.

Skills: Superpowers bounded design/TDD/debugging/verification; UI/UX Pro Max applied existing 48px filters, labelled search, compact dropdown, pagination, optional help, loading/error states and existing Qinetra styling. Ponytail reused Reports, downloads and history; no new subsystem or agents. No general motion/header/bell redesign in this release.
