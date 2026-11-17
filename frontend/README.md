# Priority-Based Medicine Booking & Allocation — Frontend (React + Vite)

Priority-Based Medicine Booking & Allocation — customer, pharmacy staff and
administrator portals wired to the existing Flask backend.

## Prerequisites
- Python (existing `venv/` at the repo root) for the Flask backend
- Node.js 18+ and npm for the frontend

## Local startup (Windows)

Run **two** processes:

**1) Flask backend** (from the repo root, port 5000) — do not modify it:
```powershell
python run.py
```

**2) Vite frontend** (from `frontend/`, port 5173):
```powershell
cd frontend
npm install        # first time only
npm run dev
```

Open http://localhost:5173

The Vite dev server proxies `/api/*` and `/health` to Flask (5000), so the
browser stays same-origin and Flask session cookies work with no backend CORS
changes. Axios is configured with `withCredentials: true`.

## Accounts
- **Customer** accounts can self-register at `/register` (the backend always
  creates a `Customer` role and does **not** start a session — sign in after).
- **Pharmacy Staff** and **Administrator** accounts have no public signup
  endpoint. Create them once with a Python shell in the repo `venv`:
  ```python
  from app import create_app
  from app.models import db, User
  from werkzeug.security import generate_password_hash
  app = create_app()
  with app.app_context():
      db.session.add(User(full_name='Pharmacist', email='pharm@example.com',
          phone='9999999999', password_hash=generate_password_hash('pharm123'),
          role='Pharmacy Staff'))
      db.session.add(User(full_name='Admin', email='admin@example.com',
          phone='9999999998', password_hash=generate_password_hash('admin123'),
          role='Administrator'))
      db.session.commit()
  ```
  Then sign in at `/login` with those emails/passwords.

## Build
```powershell
cd frontend
npm run build
```

## Known backend limitations (respected, not worked around)
- No "list my bookings" endpoint → a customer's booking history is stored only
  in the current browser (localStorage). Clearing storage or using another
  device loses it; save the booking IDs returned when you create a booking.
- Prescriptions are **reference details** (text), not file uploads.
- No medicine-create endpoint → inventory "add" only restocks existing medicines.
- No user activate/deactivate endpoint → admin user management supports role changes only.
- No staff "list all bookings/prescriptions" endpoint → staff look up by ID
  (customers can copy their prescription ID to share).
- Customers cannot cancel a waitlist entry (the cancel endpoint needs a
  waitlist ID not exposed to customers) — staff handle that.
