# Frontend hosting check — 8 October 2026

9 October continuation: Cloudflare account/Workers Free is verified; the published candidate now passes isolated build/dry-run and local route/header/asset checks. Browser transport and actual cloud CPU/startup remain unqualified. See [cloudflare-qualification-check.md](cloudflare-qualification-check.md), which supersedes account-unknown/no-retained-image observations below. No production cutover or cloud deployment occurred.

Authenticated Vercel inspection is complete. Existing hosting is on Hobby, so it does not qualify for the real shop pilot under Vercel's non-commercial-personal-use rule. No upgrade, purchase, account creation or production promotion was performed.

## Observed deployments

| Environment | Vercel deployment | Full source revision | State |
| --- | --- | --- | --- |
| Production | `dpl_DzjTqjGJJHm2vQCthra6omHEq1ML` | `5da24e577e6c373ca79b7318ded9c50e1d983a45` | Ready, created 10 August; production domain still serves the old demonstration. |
| Feature-branch preview | `dpl_G6HccjNfVyqrH8Pk5RgRFVqeji1W` | `1bfdf4a3b607a3349769fe3c4b46c64e0fb1790b` | Ready, created 8 October at 19:26 Nairobi; triggered automatically by the approved branch push. |

The preview does not establish a working pilot pair: Render still runs `5da24e5`, the preview's runtime/API configuration and staff workflows have not been qualified, and real pilot accounts/recovery remain incomplete. Do not promote it to production or use it for real shop records.

Vercel's authenticated team navigation explicitly showed `1ann0's projects Hobby`. The [Hobby plan documentation](https://vercel.com/docs/plans/hobby) restricts the plan to non-commercial personal use. The actual-plan uncertainty and private-login handoff are now resolved; hosting eligibility has failed rather than remaining unknown.

## Zero-spend continuation

- The approved roadmap already permits an isolated Cloudflare/OpenNext experiment that preserves Next.js, existing order URLs and the FastAPI boundary. Continue that option; no framework replacement, database move, paid resource or library installation in the working app is approved merely by this hosting check.
- The earlier prototype built and passed an upload dry-run, but browser/runtime/CPU qualification did not pass. Its container was removed. Current checks found no retained Docker volumes or prototype files matching the relevant names/content in `tmp`; reconstruct any next experiment from the exact published candidate rather than claiming reuse or old-build acceptance.
- A Cloudflare account has not been verified. Asked whether an account already exists; do not infer account creation, terms acceptance or broad GitHub permissions from the question. Its actual plan, free allowance and commercial eligibility must be verified before activation.
- Cloudflare qualification must cover login, owner/employee permissions, direct receipt links/refresh, logo, CSV, logout/account switching and retained uncertain saves with fictional data. Measure worker CPU/bundle constraints and headers; any necessary adapter changes need relevant candidate checks again. No Cloudflare deployment occurred in this check.
- Read-only Render inventory found only the existing free API. A native Next.js web service is technically supported, but another free web service is not a qualified daily-hosting fallback: free services sleep after 15 idle minutes, take about a minute to restart and share 750 active hours per workspace/month. Bandwidth/build excess can bill when a payment method exists. Actual billing/spend settings remain unverified. Do not silently create a service, add keep-awake traffic or promise availability.

Sources: [Vercel Hobby rules](https://vercel.com/docs/plans/hobby), [Render Next.js deployment](https://render.com/docs/deploy-nextjs-app), [Render Free limitations](https://render.com/docs/free), [Cloudflare Next.js paths](https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/). The Cloudflare prototype remains an option to qualify, not a recommendation inferred from a successful build alone.
