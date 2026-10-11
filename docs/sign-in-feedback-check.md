# Sign-in feedback and QLMS address — 11 October 2026

Current address: **https://qlms.qinetra.workers.dev/login**. The former name `qlms-pilot-qualification` marked the temporary hosting investigation. The same Worker was renamed to `qlms` through Cloudflare's Worker PATCH API; its immutable ID and existing deployed version were preserved. Final-origin API CORS and public login private/security headers pass. Owner credentials and the database were not replaced.

## Failure and bounded change

The user's screenshot reported QLMS-TIMEOUT. The frontend gave every request 30 seconds; Render documents a roughly one-minute startup after 15 idle minutes. That mismatch is reproduced with a delayed fictional sign-in. Separately, actual public readiness/OpenAPI requests timed out at 90/60 seconds and a Linux root check timed out at 60 seconds. Render reported the deploy live/not suspended, with no new failure event establishing the cause. Redeploying the same candidate recovered readiness in 1.13 seconds. The actual stall's cause and idle recovery remain open; a longer browser deadline is not evidence of service recovery.

The sign-in button now contains the existing styled spinner and polite status text. The form explains a possible two-minute wait. Password reentry uses the same feedback treatment; authentication requests do not also display the floating request indicator. Concurrent record requests still display their normal status. Reduced-motion users retain a stationary indicator and readable text.

Only `/auth/login` gets a 120-second deadline. No credentials are automatically resent. Other requests, including saves and token refresh, retain the original deadline, retry rules and uncertain-save recovery. No dependency, auth contract, role or schema changed.

## Evidence and remaining checks

Three new regressions failed before the change: form-scoped feedback, successful 60-second sign-in and exact two-minute termination. The focused 31 API/feedback/retry checks pass after it. All 84 frontend tests, lint, 16-page static export and the offline strict Wrangler upload dry-run passed in the credential-free Linux build. Image `sha256:1e1e9f34960ae70a42ea3e66805f58effbb1675e5b3c7726d005af541f843e56` retains 108 static assets/27 JS files with the compiled HTTPS API and no fictional loopback URL. The ignored complete hash manifest is `tmp/qlms-sign-in-manifest-20261011.json`. Actual hosted button behaviour remains pending publication and a credential-private human check.

Fictional UI-only browser evidence at 375 × 812: `58-sign-in-button-mobile-fictional.jpg` shows inline progress during a deliberately delayed 45-second rejection; DOM confirms `aria-busy=true`, a spinner inside the button, no floating status and client/scroll widths both 360. `59-sign-in-error-mobile-fictional.jpg` shows the existing readable wrong-password error and enabled form after the reply. This fixture has no database, real staff, tokens or retained records. The temporary viewport was reset and its tab closed. It proves the changed interface, not Android internet/Owner authentication or actual cold-start recovery.

After publication, open the current address on the Owner laptop and Android work phone. Enter credentials privately and select Sign in once. While pending, the button shows Signing in with an inline spinner; no separate sign-in popup should appear. A successful Owner sign-in opens Finance; a wrong password restores the enabled form with the existing readable error. If the service is unavailable, the form exits its busy state within two minutes. Never share a filled form or credentials. Employee operational access and Owner-only denial remain part of the final staff session.

## Release and rollback

The address rename retained version `cc0b8f7c-bce5-48b2-a4d4-f57521e1e205`, deployment `a4937381-539a-4ccc-81ff-40f31f05bb39`, paired with HTTPS API candidate `9768670`. The recovery API deploy is `dep-db5pnics728c738kq2d0`. New frontend upload/activation metadata must be recorded here after readback; the button change is not yet live merely because a build passes. Frontend rollback uses the retained HTTPS version. A name rollback must be coordinated with public links and API origins; do not move stored pending drafts to a new destination.
