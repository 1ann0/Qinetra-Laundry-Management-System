# Qinetra Laundry Management System

QLMS is a staff-only laundry order tracking system developed for Qinetra Laundry in Riruta, Nairobi. It replaces paper receipts and spreadsheet-based tracking with one system for customers, laundry orders and collections.

This project is part of the KCA University Diploma in IT final project (STU 701).

## Users

- Owner: views the dashboard, manages staff accounts and exports order records.
- Employee: registers customers, creates laundry orders and updates order status.

There is no customer portal. Online payments, multiple branches and automatic messaging are outside the project scope.

## Current features

- Staff login using JWT authentication
- Owner and employee role checks
- Customer registration and search
- Duplicate phone number warning
- Service selection and price preview
- Backend price calculation
- Daily laundry ticket generation
- Protected staff pages

## Technology used

- Frontend: Next.js, React and Tailwind CSS
- Backend: FastAPI and Python
- Database: PostgreSQL hosted on Supabase
- Database access: SQLAlchemy
- Authentication: bcrypt password hashing and JWT

## Project folders

- `backend/` contains the FastAPI routes, database models and business logic.
- `frontend/` contains the Next.js staff interface.
- `docs/diagrams/evidence/` contains screenshots captured during feature testing.

## Running the backend locally

Create `backend/.env` with the required `DATABASE_URL` and `SECRET_KEY` values. Do not commit this file.

```powershell
Set-Location backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

## Running the frontend locally

Copy `frontend/.env.example` to `frontend/.env.local`, then run:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:3000` in a browser.

## Project status

The backend is complete. Frontend phases 1 to 3 are complete, covering authentication, customers, order entry, pricing and ticket display.
