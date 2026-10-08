# Owner backup and alert preferences — 8 October 2026

Implemented and checked locally. The user approved owner settings now and a creator console after the pilot. This increment records private preferences; it does not activate a scheduler, connect Drive credentials or send email.

## Data flow and boundaries

- Shop setup shows owner-only alert email and preferred daily time. The default is 22:00 Nairobi, independent of device timezone. FastAPI validates one ordinary email and HH:mm, stores the time as minutes since midnight, and attributes each change.
- `GET /settings/alerts`, `GET /settings/alerts/history` and `POST /settings/alerts` require the current active Owner. POST requires `{owner_email, backup_time, expected_revision}` and the original `Idempotency-Key`. Extra privilege/provider/status fields are rejected. Employees receive neither contacts nor history.
- A PostgreSQL transaction lock serializes the singleton even before its first row exists. A stale revision is definitely not saved; an accepted key replays once and returns current preferences without reverting a later edit. An unknown reply preserves its original body/reference.
- The API reports `automation_status: not_configured`. Saving a preference is not proof of mailbox ownership, alert delivery or a scheduled backup. The UI explains that connection/delivery/recovery checks remain pending. The actual runner still uses private operations configuration; this form is not connected to an active job.
- Qinetra's approved initial owner/stakeholder address and time are recorded in the account-restricted ignored private setup file. They are absent from source, screenshots and fixtures. No email grants login or creator authority. Qinetra's stakeholder recipient is separate private operations configuration and is not copied to other clients.

## Fresh verification

The first HTTP run failed with 404 before the feature existed. The frontend input checks failed before their helper existed. The broader suite then exposed FastAPI's lazy included-router metadata conflicting with existing route-permission inspections. Wiring explicit API routes restored those checks without weakening tests.

- 204 backend tests passed with disposable PostgreSQL and no skips, including concurrent stale edits, same-key replay, disabled-owner rejection, field tampering, email/time bounds and repeat migration.
- 77 frontend tests, lint and production build passed. Shared request progress and pending-save recovery were reused.
- Full migration application/reapplication, schema restore and restricted-role encrypted recovery passed in 5.8 seconds locally. The restored owner preferences/history matched alongside the existing clothing/contact/payment/refund checks. Runtime UPDATE of preference history was denied. This timing is not operational recovery evidence.
- Browser fixture: invalid email showed nearby feedback and focused its field. A controlled lost POST reply left revision 1 and one history event; explicit retry confirmed the same revision/event. Keyboard focus reached the time control. At 375 × 812, document width did not exceed viewport width. Screenshot: [55-owner-alert-preferences.png](diagrams/evidence/55-owner-alert-preferences.png). It shows fictional contact details and a clear inactive-automation message.
- Applied Supabase `add_owner_alert_preferences` to the separate pilot after rehearsal. Fresh readback: 22 tables/22 RLS tables, history UPDATE/DELETE denied, backup writes denied, browser schema usage denied; operational counts remain zero, catalogue remains 22 services/30 garments. The database starts with no owner email, default 1320 minutes and revision 0. The initial private address is not imported until private owner setup; no customer data or provider credentials were introduced.

## Files

- `backend/alert_settings.py`, `main.py`: owner endpoints and route wiring.
- `backend/models.py`, `schemas.py`, `transaction_safety.py`: preferences, attributed history, validation and current-value replay.
- `backend/migrations/024_add_alert_settings.sql`, `schema/pilot.sql`, `schema/manifest.json`: repeatable private schema and regenerated rehearsal snapshot.
- `backend/ops/schema_setup.py`, `ops/rehearse_recovery.py`: immutable history privileges and restored preferences proof.
- `backend/tests/test_alert_settings.py`: HTTP permissions/input/replay and PostgreSQL race/migration acceptance.
- `frontend/src/components/settings/alert-settings.js`, `app/(protected)/settings/catalog/page.js`: owner form, inline feedback, focus and history.
- `frontend/src/lib/alert-settings.js`, `frontend/tests/alert-settings.test.mjs`: early field feedback and clock-time boundaries.
- Current check record, handover, creator guide, roadmap, this evidence record and screenshot: scope, private setup status and release limits. Ignored learning/presentation/evidence notes are updated separately. Preserve the unrelated save-rejection draft.

## Final staff acceptance steps

Use only the local fictional `discount_owner` / `DiscountTest123!` fixture. No real password or email belongs in this exercise.

1. Open Shop setup. Find Backup and alert preferences; confirm its automation warning and Nairobi time label.
2. Enter `wrong`, select Save preferences: the email must show feedback and receive focus. Nothing is saved.
3. Enter `owner-fixture@example.test`, choose 22:00, save: confirmation/history appear. Refresh: the same preferences remain; no alert delivery is claimed.
4. Open a second owner tab before an edit. Save 04:30 in the first; saving old preferences in the second must reject the stale revision. Reload there to see 04:30. An accepted retry must not restore 22:00 over a later edit.
5. Sign in as the fictional employee. Shop setup/contact/history are inaccessible; direct API checks above verify this boundary. Return the fixture preference to 22:00 afterward.

## Automation next

`pg_dump` supports a consistent export while normal reads/writes continue, but consumes resources; measure load and keep it away from schema migration work. [PostgreSQL documentation](https://www.postgresql.org/docs/17/app-pgdump.html). The application page need not be open. The existing Windows task, however, needs an awake, connected, signed-in computer; it is not a cloud job. For unattended operation with the shop PC off, qualify a separate hosted schedule, restricted credentials, private Drive upload/readback, key recovery and missed-run/failure alerts within zero-spend limits. A hosted scheduler may start late; do not promise an exact 22:00 execution without measuring its behavior.

Private first-owner/staff credentials, actual Drive account authorization, backup/alert qualification, staff acceptance, commercial hosting and the exact release remain open. No GitHub push or application deployment occurred.
