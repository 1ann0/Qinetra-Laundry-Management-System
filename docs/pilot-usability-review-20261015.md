# Existing pilot sign-in review — 15 October

Read-only review of the live expense-release frontend (`e6d9d2b`), no credentials entered and no app changes. This is a verified **375 × 812 CSS-pixel Chrome viewport**, not an actual Android test. Screenshot [72](diagrams/evidence/72-live-sign-in-phone-review-20261015.jpg) captures the initial page.

**Useful finding:** the branding block pushes the password below the initial screen and the Sign in button to **y=848**, below the 812px viewport. The username starts at y=679; staff must scroll before completing the first routine task. The logo/introduction occupy roughly the first 450px. This is a phone-efficiency issue rather than a failed login or lost-data defect.

**Existing strengths:** input heights 51px, Show button 51px, Sign in 46px and backup links 44px meet the 44px touch target. Document width 360px inside the 375px viewport shows no horizontal overflow. Inputs have visible associated labels; inline status is present on Sign in. No password value was inspected.

**Next bounded improvement, after the current backup release gate:** reuse `globals.css` mobile login rules and existing login form/API feedback to reduce the mobile branding height and make the credential task reachable sooner. Keep Qinetra identity, clear labels and inline loading/errors; do not introduce a second login flow. Any waking/readiness changes must preserve one credential submission and all pending-save/reauthentication safeguards. Tell the Owner why the mobile layout changes, then use focused UI/UX guidance, regression checks and actual phone-width screenshots before deployment.

UI/UX Pro Max informed the review's task-first layout, touch targets and plain feedback checks. Superpowers verification prevented a false phone claim: the first viewport override applied to a different tab and measured 1280px; it was corrected and measured at 375px before capturing the retained screenshot. Only the corrected capture remains under filename 72. Independent Android keyboard/login behavior was not retested.
