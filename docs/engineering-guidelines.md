# QLMS maintenance standard

Confirmed by the student on 11 September 2026. Apply across future codebase changes; do not rewrite working modules merely to enforce style.

- Make the smallest complete change for the approved business problem. Review one feature at a time.
- Use direct, readable functions and descriptive names. Extract shared logic when real duplication would cause inconsistent behaviour, such as the two customer receipt drafts.
- Keep business validation and permissions in FastAPI. UI checks improve usability but must not be the only enforcement.
- Preserve existing API contracts, saved data and price snapshots unless an approved migration explicitly changes them.
- Keep plain React state/context, fetch helpers and existing styling. Add dependencies only when a demonstrated need justifies them.
- Keep configuration separate from code and credentials out of source control. Explain every required environment variable and safe default.
- Add short comments explaining non-obvious reasons. Avoid comments that repeat the code.
- Test observable business outcomes, especially counts, payments, permissions and concurrent changes. Run focused checks; avoid redundant tests and unnecessary full-suite reruns.
- Keep migrations bounded and reviewable, verify their effect, and document recovery implications. Do not regenerate or delete customer history during setup.
- Document the files changed, how data flows and exact manual checks. Keep updates concise and capture only distinct, genuine evidence.
- Prefer incremental repairs over a broad refactor. Identify the next high-value improvement in the pilot checklist and stop after the approved phase.
