# QLMS Learning Notes

This is a plain-language guide to the technical decisions made in each phase. It can be pasted into ChatGPT or Codex later for revision questions, presentation practice, or a refresher before the project demonstration.

## Phase 1 — Foundation, Authentication, and Pricing

### What was built

- A Qinetra-branded Next.js application with `/login`, `/workspace`, and an owner-only `/dashboard` route.
- A small `fetch` helper that knows the backend address, login format, error format, and Bearer-token header.
- React Context for the current login session, without Redux or another state package.
- Matching backend and frontend pricing codes for five laundry services.
- JWT protection on every customer and order endpoint. Owner-only endpoints keep their stricter role check.

### The login flow

1. A staff member enters a username and password on `/login`.
2. The frontend sends the credentials to `POST /auth/login` as form data. FastAPI expects form data here, not JSON.
3. The backend checks the password hash and returns a signed JWT plus the user's role.
4. The frontend stores the token, role, and expiry time in `sessionStorage` and updates `AuthContext`.
5. Protected pages read `AuthContext`. A user without a current session is sent back to `/login`.
6. Future API calls use the shared helper to add `Authorization: Bearer <token>`.
7. The backend verifies the signature and expiry before it handles a protected request.

### Why both frontend and backend checks matter

A frontend guard improves navigation, but it is not real data security by itself. Someone can call a public API without using the frontend. Customer and order endpoints therefore verify the JWT on the backend too. The owner-only endpoints perform one extra check: the database user's role must be `owner`.

The dashboard guard still has value because it gives employees a clear interface and prevents accidental navigation. The backend role check is the final authority.

### Why `sessionStorage` was chosen

`sessionStorage` keeps the login after a page refresh, but clears it when that browser session closes. It is simpler to explain than building a second Next.js server layer just to manage an HttpOnly cookie. The tradeoff is that browser JavaScript can access the token, so the application must avoid unsafe HTML and unnecessary third-party scripts.

The frontend reads the token's `exp` value only to know when to log out. It cannot verify the JWT signature because the signing secret must stay on the backend.

### Pricing contract

| API code | Display service | Rate |
|---|---|---:|
| `wash_fold` | Wash & Fold | KES 150/kg |
| `duvet` | Duvet | KES 800/piece |
| `dry_cleaning_shirt` | Dry Cleaning — Shirt | KES 350/item |
| `dry_cleaning_trouser` | Dry Cleaning — Trouser | KES 350/item |
| `dry_cleaning_suit` | Dry Cleaning — 2-piece Suit | KES 750/item |

The service code is the exact value exchanged with the backend. The label is what staff see. Keeping both in one frontend catalogue reduces the chance of spelling or pricing differences in later order forms.

Historical orders using the old generic `dry_cleaning` code can still be returned by the API, but new orders must choose a garment-specific code.

### Key terms

- **API:** The HTTP routes through which the frontend asks the backend to do work.
- **JWT:** A signed token proving that the backend accepted a login.
- **Bearer header:** The `Authorization: Bearer <token>` header sent to protected endpoints.
- **Authentication:** Proving that the user has a valid login.
- **Authorization:** Deciding what an authenticated role is allowed to do.
- **React Context:** A built-in way to share login state across client components.
- **Environment variable:** Configuration supplied outside source code; here it holds the public backend URL.

### A short demonstration explanation

“The login form sends credentials to FastAPI. FastAPI checks the stored password hash and returns an eight-hour JWT. React Context keeps that session available across the interface, while session storage preserves it after a refresh. Protected API calls send the JWT in the Bearer header, and the backend checks it before returning customer or order data. Owner routes also verify the user's role.”

### Self-check questions

1. Why does the login request use form data instead of JSON?
2. What is the difference between authentication and authorization?
3. Why is a frontend route guard not enough to secure customer records?
4. What information does the frontend store for a session?
5. Why must the backend JWT secret never appear in Next.js code?
6. What happens after the token's eight-hour expiry?
7. Why do dry-cleaning garments have separate API codes?

### Answers in one line each

1. FastAPI's `OAuth2PasswordRequestForm` expects URL-encoded form fields.
2. Authentication checks the login; authorization checks what that logged-in role may access.
3. An attacker can bypass the UI and call an API directly.
4. The signed token, role, and expiry timestamp.
5. Anyone with the secret could create fake valid tokens.
6. The frontend clears the session and the backend rejects the expired token.
7. They have different prices, and the backend needs an unambiguous value for its calculation.
