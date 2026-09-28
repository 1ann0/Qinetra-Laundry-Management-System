# QLMS architecture

Source reviewed 28 September 2026. The [roadmap](IMPLEMENTATION_ROADMAP.md) distinguishes implemented, unfinished and future work.

## Architecture essentials

1. Next.js/React/Tailwind staff UI → HTTPS FastAPI API → SQLAlchemy → PostgreSQL. Browser code never connects to the database.
2. Plain React state/context and the existing fetch helper. Keep one backend application; no microservices or speculative framework replacement.
3. FastAPI derives permissions from the current active database user, not browser-provided roles.
4. PostgreSQL transactions, locks and idempotency protect money and corrections. Keep original facts and attributed changes.
5. Store saved prices and use decimal money. Payment entry corrections, service refunds and excess returns have different meanings.
6. Separate real and fictional environments. Migrations use a different identity from the restricted runtime database login.
7. Keep Render/Supabase while proving Qinetra's value; Cloudflare qualification is an independent experiment. No spending or live cutover by implication.

This outline replaces a duplicate architecture-essentials file. Detailed data meanings and recovery requirements belong in [DATA.md](DATA.md), threat boundaries in [SECURITY.md](SECURITY.md), product intent in [PRD.md](PRD.md).

## Current components and contracts

`frontend/src/app` contains App Router screens. The dynamic order page uses `/orders/[orderId]`; customer/order data loads through the fetch helper using `NEXT_PUBLIC_API_URL`. The public API address is configuration, not a credential. React Context owns the current staff session and inactivity lock.

`backend/main.py` and its imported business modules implement HTTP routes. Pydantic validates request/response models; SQLAlchemy maps users, customers, catalogues, orders/service lines, physical items, payments, handling records and correction histories. Read source/OpenAPI before changing a wire contract; historical documentation is not authoritative over the implementation.

`POST /auth/login` accepts form-encoded username/password. The current API issues a 30-minute HS256 bearer JWT with user identity and session version. Protected requests use `Authorization: Bearer ...`; the backend reloads the user and rejects inactive/revoked sessions. Passwords are bcrypt hashes. Session tokens currently live in browser sessionStorage, an acknowledged exposure to script execution.

The backend opens its database using DATABASE_URL and pool_pre_ping. Current configuration does not prove a restricted production role, explicit schema isolation or migration version. Those are D1 work, not existing guarantees.

## Writes, concurrency and history

Frontend previews are advisory; the backend calculates accepted prices and authorizes the action. Save attempts carry their original idempotency reference through lost replies, refresh and retry. Replay of an accepted request must return the accepted result even after a catalogue/policy change. Conflicting reuse or an unknown response remains uncertain; only recognized not-saved responses clear the attempt.

Use one database transaction for a business action and its event history. Lock the affected records before concurrent balance/custody checks. Test these semantics against disposable PostgreSQL, not just SQLite. Do not change physical collection status to make a monetary correction possible.

Planned interfaces include owner refund creation with net_charge/refund_due, authenticated discount-policy retrieval with owner-only changes, completed contact-correction history and database-readiness reporting. Existing endpoints remain compatible unless the increment explicitly documents and tests the migration.

## Deployment and release

Build and test on fictional data. Record frontend revision, API revision, schema revision, API origin and release checks together. Apply reviewed compatible migrations before code that needs them; code rollback does not reverse actual money or safely undo every migration.

Keep health liveness separate from database readiness. Alerts need demonstrated delivery and recovery; a green process check does not prove customer saves work. The independent backup and receipt reconciliation procedure is part of release readiness.

Cloudflare qualification preserves Next.js, order URLs, authentication and API boundaries. Use a compatible pinned OpenNext adapter and Linux build check in an isolated experiment. Verify worker CPU/bundle/runtime limits, images, direct navigation, exports, logout and private caching before choosing hosting. Do not auto-provision cache buckets or enable paid plans. A failing free deployment leaves local practice available; it does not justify a silent framework rewrite.

## Later boundaries

- Secure cookie sessions require a designed same-origin boundary and CSRF/origin checks before Google identity integration; business authorization stays in FastAPI.
- Google identities link verified issuer/subject to owner-approved users. Google API scopes are separate from sign-in; no public account creation or email-only automatic linking.
- Before shared multi-business hosting, derive business scope from verified memberships and enforce it across queries, writes, exports, jobs, callbacks and relational constraints. A business_id column alone is insufficient.
- Laundry memberships consume service allowances; QLMS subscriptions grant software access. Their ledgers and commercial rules must stay separate.
