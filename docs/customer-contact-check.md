# Owner customer-contact corrections

29 September 2026. Local increment; no remote migration or deployment.

## Behavior and boundaries

- Customer search links owners to `/customers/{id}`. Name/phone corrections keep the customer ID and all order/payment links; older order screens show the corrected contact. No customer merge or money change.
- The owner supplies the displayed name/phone, new values, reason and confirmation. The API stores before/after values, owner and timestamp. Extra request fields are rejected.
- Changing to another customer's normalized phone requires explicit shared-number approval. The UI shows matching customers before offering that confirmation. A name-only edit on an already shared number needs no new phone approval.
- A row lock and expected values reject stale edits. PostgreSQL phone locks coordinate corrections and new registrations. Same-key retries return the current customer without adding history, including after later edits.
- Keep browser database access denied. Migration 020 enables RLS and revokes table/sequence access from public/browser roles, consistent with [Supabase API protection guidance](https://supabase.com/docs/guides/api/securing-your-api). The owner checks are enforced in FastAPI, using the existing active-account/session-version checks and 30-minute Bearer tokens.

## Contract and files

- Owner-only `GET /customers/{id}` returns `id`, `name`, `phone`, `created_at`. It is registered after `/customers/phone-match` to preserve that route.
- Owner-only `GET /customers/{id}/corrections` returns history without internal request keys/hashes.
- Owner-only `POST /customers/{id}/corrections` requires `Idempotency-Key` and `{expected_name, expected_phone, new_name, new_phone, reason, confirmed, allow_shared_phone}`. It returns the updated customer. Recognized stale/shared-phone conflicts are explicitly `not_saved`; uncertain outcomes keep the original request for retry.
- Backend: `main.py` routes/phone locking; `models.py` audit model; `schemas.py` validation; `transaction_safety.py` customer replay; `migrations/020_add_customer_corrections.sql` existing draft migration completed for release; HTTP and PostgreSQL tests in `tests/test_save_rejection_http.py` and `tests/test_transaction_safety.py`.
- Frontend: `src/app/(protected)/customers/search/page.js` owner link; `src/app/(protected)/customers/[customerId]/page.js` editor/history using the existing pending-save helper. No new dependency.
- Acceptance/continuation: this record, pilot handoff, development journal, roadmap and local learning/presentation notes. Earlier refund acceptance is preserved in `refund-check.md`.

## Verification

- 156 backend tests passed with disposable PostgreSQL 17, including repeated migration/browser-role denial, concurrent same-key retry, stale edits, phone collisions with edits/registrations, permissions, disabled account, field tampering, validation, legacy-phone repair and stable order links. No skipped cases.
- 52 frontend tests, lint and Next.js production build passed.
- Browser: owner search link opened the editor; a shared-phone rejection preserved the form and displayed customer #2 before confirmation. A deliberately lost reply survived refresh/retry with exactly one audit event. A subsequent name-only correction on the shared phone saved without another sharing prompt. Search returned both distinct customers; the existing receipt showed corrected contact details with its unchanged KES 300 charge/balance. Screenshot 45 shows the two attributed before/after events. Student customer #3 remains untouched.

## Student check — fictional data only

The separate ignored `tmp/contact-fixture.py` runs on port 8001, with the frontend on 3100. It uses `tmp/contact-fixture.sqlite`; the earlier refund API/data remain separate on 8000. Local dummy accounts remain `nav_owner` / `nav_employee`, password `NavTest123!`.

1. As owner, open Customers, search `Student contact test`, and choose **Contact details** (customer #3).
2. Change the name to `Student contact checked`, phone to `0733333334`, and reason to `Checked spelling and phone with customer`. Confirm and save.
3. Refresh. Expect the corrected name/phone and exactly one history entry showing the previous details and `nav_owner`. Search the new phone and confirm it finds the same customer.

Student acceptance/explain-back are pending. The developer check uses customer #1; do not repeat those saves on the student record.

## Release

Apply migration 020 in the reviewed migration sequence before deploying the API; deploy its matching frontend after API readiness. Existing customer/order rows are not rewritten by this migration. Preserve audit history on rollback. Launch security, separate real dataset, restricted runtime access, recovery rehearsal and hosting qualification remain separate gates.
