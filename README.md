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

### Quick start with Docker (recommended)

```bash
docker compose up --build
```

This spins up Postgres, the Django backend (with migrations and demo data seeded
automatically on first run), and the Vite frontend. Once the logs settle:

- Frontend: http://localhost:5173
- Backend:  http://localhost:8001
- Postgres: localhost:5434 (user/db/password = `ibook`)

Stop with `Ctrl+C`, or clear everything with `docker compose down -v` (the `-v`
also wipes the database volume so the next run re-seeds).

### Manual setup (no Docker)

Run the backend and frontend in **two separate terminals**. Defaults use SQLite,
so no Postgres install is required.

#### Prerequisites

- Python 3.11+
- Node.js 18+ and npm

#### Terminal 1 — Backend (Django on port 8000)

```bash
cd backend

# 1. Create and activate a virtualenv
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Seed demo data (10 shops, barbers, appointments, reviews, photos)
#    Skip this if you want an empty DB.
python manage.py seed_demo

# 5. Start the API server
python manage.py runserver
```

Backend is now serving at **http://localhost:8000**.

#### Terminal 2 — Frontend (Vite on port 5173)

```bash
cd frontend

# 1. Tell Vite where the backend is (default points to the docker port 8001)
echo "VITE_BACKEND_URL=http://localhost:8000" > .env.local

# 2. Install Node dependencies
npm install

# 3. Start the dev server
npm run dev
```

Open **http://localhost:5173** in your browser.

#### Optional env vars

`backend/.env` (only if you want to override defaults):

```
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
STRIPE_SECRET_KEY=sk_test_...        # optional, for online payments
STRIPE_PUBLISHABLE_KEY=pk_test_...   # optional
```

`frontend/.env.local`:

```
VITE_BACKEND_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...   # optional
```

Stripe keys are optional — the app works without them (just use "Pay at Shop").

#### Stop everything

In each terminal: `Ctrl+C`. Backend SQLite data lives in `backend/db.sqlite3`;
delete that file to start fresh.

#### Demo Accounts

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
  tests/         # pytest test suite

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
python -m pytest -x -q
```
