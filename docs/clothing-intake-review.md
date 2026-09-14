# Clothing intake and outsourced dry cleaning

Reviewed 11 September 2026. Source audit and existing contract tests only. No application, catalogue or live database change was made in this review.

## Business requirement

Staff must account for what the customer handed over, identify each outsourced garment, record existing damage and serious stains, and show the agreed record on the customer's receipt. This is required for the Qinetra pilot, before subscription or commercial expansion work.

Confirmed practice: Qinetra currently identifies outsourced garments using descriptions without numbered tags. Preserve those descriptions. On 15 September the user accepted simple physical references alongside descriptions; the method must be agreed with the cleaner. Staff usually check clothes before washing after drop-off, and physical separation practices vary. Pending checks must be explicit and completed before processing; later observations must not be presented as witnessed by the customer.

## What exists and what is missing

| Need | Evidence in the current source | Limit |
| --- | --- | --- |
| Laundry item tally | `frontend/src/components/orders/service-item-entry.js` provides per-type plus/minus counts and a piece total. Orders save the item name and quantity. | The temporary review fixture sets Wash & Fold to `item_recording_mode="none"` and seeds no clothing types. That hides the existing tally in the test UI; it does not establish a production regression. |
| Individual dry-cleaning garments | Detailed mode provides a garment type, description, Yes/No existing-damage choice, damage note and stain note. Fixed garment services retain their linked type. | Description and damage details can be blank. There is no permanent operational tag number to distinguish identical garments. |
| On-screen receipt | Both order entry and saved order details render clothing quantities, descriptions, damage and stain notes. | Existing completed tests did not include clothing in the simplified local demo. A representative browser check is still required. |
| Customer WhatsApp receipt draft | Both order pages build a message with customer, ticket, service names, total, paid amount and balance. | Both omit clothing counts and condition notes. The on-screen record and customer message do not currently contain the same detail. |
| Laundry condition exceptions | The API item schema has optional description/damage/stain fields. | The tally UI exposes counts only, and the tally payload explicitly sends those note fields as null. A damaged or badly stained laundry item cannot be documented through that path. |
| Pending checks | Staff can choose Record items now or Do this later. The backend blocks Ready while a service has a pending clothing check. | It can still enter In Progress before that check. There is no distinct outsourcing handover gate. Intake notes should be captured before handling changes the original condition. |
| Edits | Revision checks reject an outdated editor, and ready/collected orders block item changes. | Editing replaces the saved item list. There is no condition-change history retaining the earlier observation, author, time and reason. Database row IDs must not be treated as permanent garment tags. |
| Outsourced work | No dedicated partner, external tag, sent/returned event or garment reconciliation model was found in the inspected source. | A receipt description alone does not track which garment left the shop or whether all garments returned. |

## Verification

Ran the existing `test_detailed_order_contract.py` suite with `DATABASE_URL=sqlite://` and a local test secret: **25 tests passed**, no skips, in 1.429 seconds. These cover mixed orders, item checks, service/garment matching, saved records, payments and status rules. They do not prove missing features exist or verify the current live catalogue. Earlier PostgreSQL concurrency results remain separately documented.

## Proposed order of work

### 3A — Clothing intake and complete receipts

Work in two separately approved increments. **3A1 first:** make the existing tally/detailed editors visible in representative local test data and include saved clothing details in both customer receipt drafts; verify a mixed order with the student. This increment needs fixture/receipt UI work and tests, not an application database migration. **3A2 next:** add laundry condition exceptions, stronger required details and observation history after reviewing the completed first increment.

1. Prepare representative disposable catalogue fixtures: Wash & Fold with Quick tally, real clothing type names and at least one per-garment Dry Cleaning service. Preserve the student's existing test orders and never invent historical tallies for them. Check live catalogue settings separately before any live configuration change.
2. Keep quantity counting fast. Allow a counted laundry item to have an individual exception record when it is damaged, stained or needs identification. Link it to the counted type without charging or counting it twice.
3. Require a useful garment description for detailed dry cleaning. When damage is marked Yes, require the damage description. Keep serious stain details explicit. Avoid a long mandatory form for every ordinary laundry piece.
4. Show the same saved clothing record in order confirmation, order details and the customer receipt draft. Include pending-check wording when applicable. Building a draft does not authorize sending it to a customer.
5. Record who checked the intake and when. Preserve the original condition and subsequent corrections with a reason; do not silently replace evidence. Keep this limited to clothing observations, with the broader correction workflow still in Phase 4.

Likely files: shared `service-item-entry.js`, order entry and order details pages, receipt formatting helper and tests, `backend/models.py`, `schemas.py`, clothing routes in `main.py`, an additive migration if the exception/history design needs it, and contract tests. No new state library or service split is needed.

Learning point: one saved clothing record should drive every receipt view; a tally describes quantity while an exception identifies a particular affected piece.

### 3B — Identify and reconcile outsourced garments

Current practice is description-only. Before implementing physical labels, agree how staff would attach and use a short QLMS reference, such as a ticket plus garment suffix. A permanent QLMS garment reference and any future cleaner-supplied tag are different fields. Preserve references through edits and link each physical garment to its order. A barcode printer is not required for the proposed initial approach.

Provide a small handover register: partner, garment references sent, staff member and sent time, expected return, returned garments, return condition and unresolved discrepancies. Support partial returns. Block completion of outsourced work while garments are missing or unchecked. Keep the existing overall order stages and add these details to the outsourced service rather than introducing a second unrelated order system.

Proposed supporting controls: a readable printable or handwritten tag reference, a sent/returned checklist, and a record of the customer's review of the intake details. Photos may be useful for material damage or serious stains, but storage, access and retention need a separate scoped design before adding uploads. The customer receipt should not expose internal supplier costs or unnecessary staff/supplier details.

### 3C — Add customers without leaving the order

Continue the already proposed customer-intake work after the clothing record is dependable. Preserve clothing counts, descriptions and condition notes when creating or switching the customer. Google OAuth and AWS learning remain separate phases.

## Acceptance and evidence

- Create a fictional mixed order with a quick tally and two similar dry-cleaning garments. Mark an existing tear on one and a serious stain on the other.
- Save, refresh and compare the stored details with both on-screen receipts and the generated customer message. Do not send the message.
- Verify that a laundry condition exception does not increase the garment count or price. A missing required damage description must be rejected by both UI and API.
- Edit the condition with a reason, then verify the original record is still available. Repeat with two editors to finish the remaining stale-edit check.
- For the outsourcing phase, send two garments and return one. The remaining garment must stay outstanding. Unknown or duplicate returned tags must not silently close the handover.
- Keep old orders without invented item records or condition observations. Test migrations on disposable data before any release.
- Run the focused backend and receipt tests, frontend lint and production build after implementation. Perform the representative browser workflow with the student.
- Capture at most two distinct milestone screenshots: clothing/condition intake and the matching receipt or partial-return result. Label fictional test data and link the images from the development journal. Do not fill screenshot numbers with redundant images.

## Pre-mortem

| Failure | Prevention to verify |
| --- | --- |
| Staff cannot find the tally | Representative service defaults and fixtures; visible Record items controls; do not silently use No clothing list for normal Qinetra wash services. |
| A customer's receipt omits the recorded damage | Generate each customer receipt from the saved clothing fields; test both entry-page and details-page drafts. |
| Two similar shirts are mixed up | Permanent garment reference plus useful description; map any external cleaner tag explicitly. |
| A note is changed after a complaint | Preserve the original observation and a dated correction history. |
| Garments leave before they are checked | Complete intake/condition checks before the outsourcing handover; display outstanding work. |
| A partial return is marked complete | Reconcile individual references and retain an outstanding count. |
| Recording is too slow and staff skip it | Fast tally for ordinary pieces; individual detail for dry cleaning and condition exceptions. Observe use during a busy intake. |
| Old receipts change after catalogue edits | Keep saved name/price snapshots and do not retroactively invent clothing counts or condition checks. |

Current identification method: descriptions without numbered tags. Simple physical references were accepted on 15 September; confirm the attachment method before the outsourcing subphase. Phase 3A1 is approved but not started. Follow the current implementation contract and delivery order in IMPLEMENTATION_ROADMAP.md.
