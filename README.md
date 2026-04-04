# IBook - Barbershop Booking Platform

A web application for booking barbershop appointments in Tashkent, Uzbekistan. Built as a final year project for BSc Business Information Systems at WIUT.

Customers can find nearby barbershops, browse barber profiles, book appointments, leave reviews, and pay online. Barbers and shop owners get dashboards with analytics.

## Tech Stack

- **Frontend:** Vue 3 + Vite + TypeScript
- **Backend:** Django 5.2 + Django REST Framework
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Payments:** Stripe (test mode)
- **Maps:** Leaflet + OpenStreetMap
- **Charts:** Chart.js via vue-chartjs

## Features

- User registration and login (Customer, Barber, Shop Owner roles)
- Shop registration with photos, location, and working hours
- Barber profiles with service catalogs and availability
- Interactive map to discover nearby barbershops
- Real-time slot availability and booking flow
- Online payment (Stripe) or pay at shop
- Appointment management (cancel, reschedule, mark complete)
- Star ratings and text reviews after appointments
- Barber analytics dashboard (bookings, revenue, trends)
- Owner analytics with barber comparison table
- Mobile responsive with bottom tab navigation

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_test_users  # creates test accounts
python manage.py seed_demo         # populates demo data (shops, barbers, appointments, reviews)
python manage.py runserver
```

Backend runs at http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

### Environment Variables

Create `backend/.env`:
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
STRIPE_SECRET_KEY=sk_test_...      # optional, for online payments
STRIPE_PUBLISHABLE_KEY=pk_test_... # optional
```

Create `frontend/.env`:
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...  # optional
```

Stripe keys are optional - the app works without them (just use "Pay at Shop" option).

### Demo Accounts

After running `seed_demo`:

| Role | Email | Password |
|------|-------|----------|
| Customer | customer1@ibook.demo | demo1234 |
| Barber | barber1@ibook.demo | demo1234 |
| Shop Owner | owner1@ibook.demo | demo1234 |

## Project Structure

```
backend/
  apps/
    users/       # auth, profiles, roles
    shops/       # shop registration, photos, hours
    services/    # barber services, schedule, blocked dates
    bookings/    # appointments, slots, analytics
    reviews/     # ratings and reviews
  config/        # Django settings, urls
  tests/         # pytest test suite (99 tests)

frontend/
  src/
    views/       # page components (customer, barber, owner)
    components/  # reusable UI components
    layouts/     # role-based layouts with navigation
    lib/         # axios config, utilities
    router/      # Vue Router config
    stores/      # Pinia auth store
```

## Running Tests

```bash
cd backend
python -m pytest -x -q    # run all 99 tests
```

## Academic Report

To generate the BISP report:
```bash
pip install python-docx matplotlib
python scripts/generate_final_report.py
```

This creates `IBook_Final_Report.docx` with all required sections, survey analysis charts, and references.

## Author

Tabassum Allamova - WIUT BIS 2026
