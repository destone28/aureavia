# AureaVia - Project Context

## Overview
AureaVia is an NCC (Noleggio Con Conducente) management platform that acts as intermediary between external booking portals (Booking.com, travel platforms, digital concierges) and NCC driver/company networks. The system automates booking reception via API, driver assignment, ride monitoring, and multi-level financial reporting.

**Client**: Società intermediaria di trasporto NCC
**Developer**: 3DSprinted di Destratis Emilio
**Budget v1.0**: €32,500
**Deadline v1.0**: March 1, 2026
**Current phase**: Development kickoff

## Business Model
```
Cliente Prenotante → Portale Esterno (Booking.com) → API → AureaVia → Società NCC / Driver
```
- Il cliente finale prenota su portale esterno (NON accede ad AureaVia)
- Il portale vende la corsa alla società intermediaria
- La società intermediaria distribuisce le corse ai driver (propri o di società NCC partner)
- AureaVia monitora esecuzione e consolida dati economici/operativi

## Actors & Roles

| Ruolo | Accesso | Descrizione |
|-------|---------|-------------|
| **Admin Intermediario** | Webapp (desktop-first) | Gestione completa: corse, driver, NCC, rendicontazione, report |
| **Assistente Operativo** | Webapp | Come Admin ma senza gestione finanziaria (solo lettura fatture) |
| **Operatore Finanziario** | Webapp | Rendicontazione, fatturazione, export dati |
| **Driver** | Mobile app (Android/iOS) | Riceve notifiche, accetta corse, avvia/chiude, profilo |
| **Società NCC** | NO accesso diretto | Riceve rendicontazioni e report prodotti dall'app |
| **Cliente Prenotante** | NO accesso | Prenota solo su portale esterno |

## Ride Lifecycle (Stati della corsa)
```
Da Assegnare → Prenotata → In Esecuzione → Completata
                    ↓
               Cancellata

Da Assegnare → CRITICA (se < 3h all'esecuzione e non assegnata)
```

### Corse Critiche
- Corsa non assegnata/prenotata a meno di 3 ore dall'esecuzione
- Stato automatico → "Critica"
- Notifica push ad Admin e Assistente
- Possibilità assegnazione forzata
- Modalità GPS "strong" attivabile (campionamento ogni 5 min invece di 20 min, max 30 min)

## Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy + Alembic (migrations)
- **Auth**: JWT + 2FA via email
- **Task Queue**: Celery + Redis (notifiche push, corse critiche check)
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **API External**: Booking.com API integration
- **Export**: CSV generation (ReportLab per PDF futuri)

### Frontend - Driver App (Mobile)
- **Framework**: React + Capacitor
- **UI**: Tailwind CSS
- **Build**: Vite
- **Target**: Android + iOS + Browser fallback
- **Push**: FCM via Capacitor plugin

### Frontend - Admin Webapp (Desktop-first)
- **Framework**: React
- **UI**: Tailwind CSS
- **Build**: Vite
- **Charts**: Recharts
- **Tables**: TanStack Table
- **Target**: Browser (desktop-first, mobile-responsive)

### Infrastructure
- **Hosting**: Cloud europeo (GDPR compliant)
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Reverse Proxy**: Nginx/Caddy

## Project Structure
```
aureavia/
├── CLAUDE.md                    # This file
├── README.md                    # Project documentation
├── docs/                        # Architecture documents
├── mockup/                      # Existing HTML/CSS/JS mockup (11 pages)
│   ├── index.html               # Driver login
│   ├── admin-login.html         # Admin login
│   ├── rides-list.html          # Driver rides dashboard
│   ├── ride-detail.html         # Ride details + accept/decline
│   ├── profile.html             # Driver profile
│   ├── activity.html            # Driver activity
│   ├── vehicle.html             # Vehicle info
│   ├── reviews.html             # Driver reviews
│   ├── admin-dashboard.html     # Admin dashboard (4 tabs)
│   ├── add-driver.html          # Add driver form
│   ├── add-partner.html         # Add partner form
│   ├── assets/                  # Images (logo, backgrounds)
│   ├── js/                      # navigation.js, styles.css
│   └── data/                    # ncc-rides-export.csv
├── backend/                     # Python FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # API routes
│   │   │   ├── auth.py
│   │   │   ├── rides.py
│   │   │   ├── drivers.py
│   │   │   ├── companies.py
│   │   │   └── reports.py
│   │   ├── services/            # Business logic
│   │   ├── tasks/               # Celery tasks (critical rides, notifications)
│   │   └── utils/               # Helpers (email, csv export)
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # React app (shared codebase)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── driver/          # Driver pages
│   │   │   └── admin/           # Admin pages
│   │   ├── hooks/
│   │   ├── services/            # API calls
│   │   ├── store/               # State management
│   │   └── utils/
│   ├── package.json
│   ├── capacitor.config.ts      # Capacitor config for mobile
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
└── docker-compose.yml
```

## Database Schema (Core Entities)

### users
- id, email, password_hash, role (admin/assistant/finance/driver)
- first_name, last_name, phone, status (active/suspended/unavailable)
- created_at, updated_at, last_login
- two_factor_code, two_factor_expires

### ncc_companies
- id, name, contact_email, contact_phone
- status (active/inactive), created_at

### drivers (extends users where role=driver)
- user_id (FK), ncc_company_id (FK, nullable - null = direct admin driver)
- license_number, license_expiry
- vehicle_make, vehicle_model, vehicle_plate, vehicle_year
- vehicle_seats, vehicle_luggage_capacity
- insurance_number, insurance_expiry, vehicle_inspection_date
- special_permits (JSON), rating_avg, total_km, total_rides

### rides
- id, external_id (booking platform reference)
- source_platform (booking.com, etc.)
- status (to_assign/booked/in_progress/completed/cancelled/critical)
- pickup_address, pickup_lat, pickup_lng
- dropoff_address, dropoff_lat, dropoff_lng
- scheduled_at, started_at, completed_at
- passenger_name, passenger_phone, passenger_count
- route_type (urban/extra_urban), distance_km, duration_min
- price, driver_share, notes
- driver_id (FK, nullable), assigned_by (FK, nullable)
- critical_at, critical_resolved_at, critical_resolution_type
- created_at, updated_at

### ride_history
- id, ride_id (FK), old_status, new_status
- changed_by (FK), changed_at, notes

### assignment_rules
- id, priority, ncc_company_id (FK, nullable)
- time_slot_start, time_slot_end, day_of_week
- is_blocked, created_by (FK)

### gps_positions
- id, driver_id (FK), lat, lng, recorded_at
- is_strong_mode

### reviews
- id, ride_id (FK), driver_id (FK)
- rating (1-5), comment, source_platform
- created_at

### notifications
- id, user_id (FK), type, title, body
- ride_id (FK, nullable), read_at, sent_at

## API Endpoints (v1.0 Core)

### Auth
- POST /api/auth/login
- POST /api/auth/verify-2fa
- POST /api/auth/refresh
- POST /api/auth/forgot-password
- POST /api/auth/reset-password

### Rides
- GET /api/rides (filtri: status, date_from, date_to, driver_id, source)
- GET /api/rides/{id}
- POST /api/rides (webhook da booking platform)
- PUT /api/rides/{id}
- PUT /api/rides/{id}/assign
- PUT /api/rides/{id}/accept (driver)
- PUT /api/rides/{id}/start (driver)
- PUT /api/rides/{id}/complete (driver)
- PUT /api/rides/{id}/cancel

### Drivers
- GET /api/drivers
- GET /api/drivers/{id}
- POST /api/drivers
- PUT /api/drivers/{id}
- GET /api/drivers/{id}/stats
- GET /api/drivers/{id}/reviews

### Companies
- GET /api/companies
- POST /api/companies
- PUT /api/companies/{id}

### Reports
- GET /api/reports/earnings (filtri: period, company_id, driver_id)
- GET /api/reports/rides/export (CSV)
- GET /api/reports/critical-rides

### GPS
- POST /api/gps/position (driver reports position)
- GET /api/gps/drivers (admin: all active drivers positions)

### Notifications
- GET /api/notifications
- PUT /api/notifications/{id}/read

## v1.0 Scope (2 weeks - MVP)
Focus su funzionalità core per demo con 1 admin + 30 driver:

### Must Have
1. **Auth**: Login email + password + 2FA email
2. **Rides API Integration**: Ricezione corse da Booking.com API (o simulatore)
3. **Driver App**: Login, lista corse, dettaglio, accettazione, avvio, completamento
4. **Admin Dashboard**: Overview KPI, lista corse, gestione driver, gestione partner
5. **Notifiche Push**: Nuova corsa disponibile, assegnazione forzata
6. **Profilo Driver**: Dati anagrafici, veicolo, attività, recensioni

### Nice to Have (v1.0)
7. Corse critiche (auto-detection < 3h)
8. Assegnazione forzata da admin
9. Export CSV base
10. Regole di assegnamento

### v2.0 (Future)
- Scale 30 → 1000 driver
- GPS tracking + strong mode
- App store publication
- Multiple booking platform integrations
- Advanced reporting & analytics
- Società NCC self-management

## Design System
- **Primary**: #FF8C00 (Orange AureaVia)
- **Secondary**: #FFA500
- **Text Primary**: #2D2D2D
- **Text Secondary**: #666666
- **Background**: #F5F5F5
- **Success**: #4CAF50
- **Error**: #F44336
- **Info**: #2196F3
- **Font**: Open Sans (400, 600, 700)
- **Border Radius**: 12-16px cards, 8-12px inputs, 12px buttons

## Authentication Flow
1. User enters email + password
2. Backend validates credentials
3. Backend generates 6-digit code, sends via email
4. User enters 2FA code
5. Backend returns JWT (access + refresh tokens)
6. All subsequent requests include Bearer token

## Key Business Rules
- Driver vede SOLO le proprie corse e quelle disponibili
- Driver NON vede dati economici di altri driver/società
- Driver NON può modificare prezzi o condizioni
- Admin ha pieni poteri operativi su tutto
- Assistente = Admin senza scrittura finanziaria
- Corse assegnate prioritariamente ai driver diretti dell'admin, poi alle società NCC partner
- Data retention: 3 anni per compliance contabile e reclami
- GDPR: consensi espliciti in fase di registrazione

## Development Commands
```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install
npm run dev          # Development server
npm run build        # Production build
npx cap sync         # Sync with Capacitor
npx cap open android # Open Android Studio
npx cap open ios     # Open Xcode

# Docker
docker-compose up -d          # Start all services
docker-compose logs -f        # View logs

# Database
alembic upgrade head          # Run migrations
alembic revision --autogenerate -m "description"  # Create migration
```

## Environment Variables
```
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/aureavia
SECRET_KEY=<random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
SMTP_HOST=smtp.provider.com
SMTP_PORT=587
SMTP_USER=noreply@aureavia.com
SMTP_PASSWORD=<smtp-password>
BOOKING_API_KEY=<booking-api-key>
BOOKING_API_URL=<booking-api-endpoint>
FCM_SERVER_KEY=<firebase-server-key>
REDIS_URL=redis://localhost:6379/0

# Frontend
VITE_API_URL=http://localhost:8000/api
VITE_FCM_VAPID_KEY=<firebase-vapid-key>
```

## Existing Mockup Reference
The `mockup/` directory contains the complete HTML/CSS/JS prototype with:
- 11 HTML pages covering all driver and admin flows
- Pixel-perfect implementation of Figma designs
- 6 sample rides, 5 drivers, 4 partners, 87 reviews
- Interactive filters, charts, modals, toast notifications
- Brand-consistent design (orange/black, Open Sans)

Use these as the definitive UI/UX reference for React implementation.
