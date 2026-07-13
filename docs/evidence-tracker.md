# QLMS Evidence Tracker

Track evidence for the final presentation/viva here. Check items off as you capture them.
Screenshots go in docs/diagrams/evidence/ using the naming pattern: 01-description.png, 02-description.png...

## Backend Feature Tests (screenshots of /docs responses)

- [x] 01 - Database connection test (test-db route, before removal)
- [x] 02 - Customer creation (POST /customers)
- [ ] 03 - Order creation with ticket number (POST /orders)
- [ ] 04 - Order listing with status filter (GET /orders)
- [ ] 05 - Order status update, ready_at timestamp (PATCH /orders/{id}/status)
- [x] 06 - Overdue flagging working (GET /orders/overdue)
- [ ] 07 - Login success with JWT returned
- [ ] 08 - Employee blocked from owner-only route (403 Forbidden)

## Frontend Screens (once built)

- [x] 09 - Login screen
- [ ] 10 - Owner dashboard
- [x] 11 - Customer registration form
- [ ] 12 - Customer search screen
- [ ] 13 - Order entry screen
- [ ] 14 - Order status update (staff view)
- [ ] 15 - Overdue orders section (staff/owner view)
- [ ] 16 - Reports/CSV export screen

## Content Evidence (not screenshots — actual documents)

- [ ] Real pricing rates confirmed with owner (update logic.py placeholders)
- [ ] Interview notes written up and saved (docs/interview-notes.md or similar)
- [ ] SRS updated with finalized out-of-scope section
- [ ] Usability test session with owner completed (target rating >= 4/5)
- [ ] Usability test notes/rating recorded (docs/usability-test-results.md)

## Notes

- Screenshot = browser response body from /docs, or the actual frontend screen
- Capture immediately after confirming a feature works — don't wait
- Git commit history is backup evidence too (git log --oneline shows progression)
- Screenshot 10 stays open until the real owner dashboard is built in Phase 5
