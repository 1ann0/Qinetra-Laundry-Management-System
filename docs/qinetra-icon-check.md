# Qinetra browser and phone shortcut icon

14 October 2026. The Owner requested Qinetra's logo as the free-plan website/app icon. The existing JPEG artwork remains unchanged, embedded in a square SVG with a white background. Root metadata links that icon and a web manifest named QLMS. The Next.js starter favicon is removed. No service worker, offline claim, permission change, dependency or paid service is added.

The frontend-only candidate passed 99 frontend tests, lint, a 20-route Linux build and strict offline Wrangler upload qualification. Image `sha256:ac34cbd3673a3e4c49573726be97ebb614d3bcaaf6b9ce814cf90ab131beee31` compiles the existing HTTPS pilot API. Artifact checks prove login icon/manifest links, `/login` start URL, unchanged embedded artwork and absence of the starter favicon. Actual browser inspection renders the complete logo on its square white background.

Deployment is pending. The pilot API and database require no change. Preserve the preceding Worker `975d3ecc-87d9-4d55-bb6e-52456a38dd15` for rollback.

After deployment, privately open QLMS in Android Chrome, refresh it, choose the browser menu -> Add to Home screen, and use QLMS as the name. If an older shortcut remains, remove that shortcut and add it again. The shortcut still requires internet. Actual phone shortcut creation/opening remains a human check; it is separate from the already passed Dashboard and spreadsheet acceptance.
