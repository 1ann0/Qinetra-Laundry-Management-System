# Phone sign-in and on-demand startup

Release hygiene increment 1c. The deployed backup catch-ups are cloud-qualified; observation of the next natural schedule event remains explicitly open. That external timing observation continues while this independent UI part of release hygiene is checked. Do not call the whole release-hygiene milestone complete yet.

## Bounded design

- Existing live 375px review shows Sign in at y=848 on an 812px screen. Compact only the phone branding section in `globals.css`, retaining the Qinetra logo, heading, labelled fields, password toggle and inline sign-in feedback. Preserve desktop layout.
- Reuse `apiRequest` for one public `/health/ready` check when the signed-out form opens. No token, credentials, business records, scheduled polling or background keep-alive. Abort when the form is left. A healthy reply must explicitly say ready; a timeout/unavailable reply must never claim readiness or prevent the existing sign-in action.
- Give only login and public readiness their existing two-minute startup allowance. Ordinary record requests keep their current deadline and write requests remain single-attempt. Show connecting, possible wake-up after eight seconds, ready and unavailable feedback beside the form with accessible status text. Slow protected reads may explain a possible wake-up without claiming a measured cause.
- Tests first for readiness validation, sixty-second startup, two-minute timeout and cancellation; preserve all existing login/read/write retry tests. Review the actual production build at phone widths, delayed/unavailable fictional API and existing login routes. No passwords on live browser automation.
- No database/API migration or API deployment. Deploy only the verified frontend, preserve the current expense-release Worker for rollback, verify every public asset and protected API denial using the shared smoke checker. Record exact source/version/evidence and UI limits in handoff/learning notes.

## Shop fact for the next financial increment

The Owner confirms some expenses are paid from a separate personal pocket. Daily close must subtract only shop-funded cash expenses. Owner-funded payments remain business costs but do not reduce shop cash. Existing expense rows have no funding-source field; do not infer one from Cash/M-Pesa. Add compatible attributed confirmation/correction and an explicit unconfirmed state before using those rows in a close. Till additions and withdrawals remain separate movements; never invent a cash deposit to compensate for a personally paid expense.

## Skills

Superpowers systematic debugging ties the compact layout to measured geometry; TDD/verification checks readiness boundaries and no automatic write replay. UI/UX Pro Max supplies task-first phone layout, 44px targets and visible accessible waiting states. Ponytail reuses the existing API client, form and CSS, with no dependency or second authentication flow.
