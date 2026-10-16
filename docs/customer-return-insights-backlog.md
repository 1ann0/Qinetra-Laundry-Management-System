# Customer return insights — requested 15 October 2026

The Owner reprioritised this immediately after backup timing on 16 October. The first version is now deployed through Owner Reports and existing customer history, including Excel/CSV downloads; see [release proof](customer-return-insights-check.md). No new database tables or automatic messages. Pickup/delivery follows, then secure-cookie sessions. Suggestions based on a customer's usual visit interval and attributed contact logs remain later refinements, not claims of this release.

The Owner wants days since a customer's last visit, 7-day/30-day/90-day views, weekly/monthly new-customer counts and practical retention/re-engagement guidance. Follow-up should be searchable and reachable from the Owner dashboard and customer history. Preserve employee access boundaries and the existing shared calculations/export patterns.

Bounded starting definitions for design review:

- Visit means a saved, non-cancelled laundry intake, not a payment, collection, profile edit or message. Count new customers by their first such order in the selected Nairobi date range. Show registered profiles with no orders separately.
- Use distinct last-visit groups of 7–29, 30–89 and 90+ days, plus a precise last-visit date/days on customer history. State that available history begins at pilot start; imported catalogue creates no customer history.
- Show recent new customers and repeat visits. Do not infer that a customer is lost after seven days or attribute a return to a campaign without evidence.
- Owner reviews prior services and visit pattern before a personal follow-up. A later contact log can prevent repeated approaches. Any customer message remains previewed and manually sent; no automatic campaign or fictional-demo contact.
- Suggested actions: check satisfaction after a first collection, offer a useful reminder at the customer's usual interval, and review an inactive customer's history before sending a personal invitation. Do not invent discounts or promises.

User experience requirement: clear task names, search on long lists, connected next actions, preserved entered details, visible save state and short optional help at difficult decisions. Review each approved feature against the real intake/payment/ready/collection flow; avoid a separate navigation redesign that delays the current release.
