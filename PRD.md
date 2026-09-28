# QLMS product requirements

Approved direction, 28 September 2026. Requirements are not a completion claim. The [roadmap](IMPLEMENTATION_ROADMAP.md) owns sequence and status; the [premortem](docs/pilot-premortem.md) owns failure scenarios.

## Purpose and users

Help Qinetra Laundry, a family business in Riruta, find customer records, receive and identify clothes, quote consistently, track work, record money, return the right items and reconcile the day. Start with one shop and individual owner/employee accounts on potentially shared devices.

Employees need quick intake, customer/ticket search, clear clothing checks, status updates and confirmed payment entry. The owner also needs staff/catalogue control, attributed corrections, refunds, discounts, financial summaries and exports. Customers do not log in during this pilot.

## Required daily outcomes

| Outcome | Acceptance |
| --- | --- |
| Retrieve a customer or ticket | Search name/normalized phone/ticket; shared phone numbers do not merge different people; history identifies the correct customer |
| Receive and price laundry | Mixed services use saved rates, explicit discounts, physical piece records and a promised ready time; billable units and physical pieces remain distinct |
| Follow work and custody | Received → In Progress → Ready → Collected; holds, checks and outsourced returns block misleading progress |
| Record and correct money | Confirm actual receipt/return, preserve originals, distinguish mistaken entry/service refund/excess return, and keep receipt/Finance/CSV consistent |
| Control access | Owner grants individual staff access; backend restrictions survive hidden-button bypass and disabled accounts |
| Recover a disrupted save | Unknown outcomes retain the same request/reference; confirmed rejections unlock correction; retry never duplicates money or orders |
| Close the day | Reconcile tickets, receipts, refunds, outstanding balances and collections without treating bookings or cash flow as profit |

Employee discretionary discounts have an owner-configured whole-order percentage ceiling, initially 0%. The owner may change the policy; employees cannot bypass it by splitting discounts between service lines. This policy is approved but not yet implemented.

## Pilot and success measures

No spending is authorized. Finish the release gates before entering real trial records. Use a separate database project, restricted access and a proved restoration procedure. Retain existing receipts during ten trading days and reconcile daily; extend the observation if important workflows were not exercised.

Record baseline and observed intake, lookup and closing times, coaching/hesitation, corrections, missing garments/instructions, unexplained balances and duplicate saves. Pass means staff can complete the agreed workflows, money agrees and recovery works. Set numeric task-time targets with the operator before measuring; do not invent improvements from a demonstration.

Stop new trial entry for missing/disclosed records, unexplained money, duplicate writes or failed recovery. Preserve evidence, use receipts and reconcile before resuming. One day reconstructed from receipts and four working hours to restore are targets until tested.

## Later value and boundaries

The full inventory remains in the roadmap: improved work lists/trends, Google sign-in, care preferences, offers/templates, verified M-Pesa, costed laundry memberships/B2B/trips, selected operations modules, and eventually business isolation/software billing. Each has its own acceptance gate.

Google sign-in follows a stable pilot and session hardening. Branches, customer portals and offline synchronization are separate projects. AWS learning does not require moving the shop.

For future clients, establish the specific operational problem before choosing full QLMS or a focused solution. Reuse a maintainable core where needs repeat; do not create a general platform before demand or divergent customer copies without a maintenance plan. Use measured, anonymized Qinetra results as evidence, not promised revenue gains.
