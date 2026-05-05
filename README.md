# MetroFlow Predictor

MetroFlow Predictor is a full-stack metro passenger forecasting application built with Next.js, FastAPI, MongoDB, and a modular Python ML layer. It includes JWT-based authentication, protected dashboard routes, historical station analytics, admin CRUD for flow records, dark mode, and CSV export for recent predictions.

## What Is Included

- Apple-style responsive frontend with smooth glassmorphism-inspired panels
- Combined login/register experience with client-side validation
- Protected dashboard, history, profile, and admin routes
- Interactive charts using Recharts
- FastAPI backend with JWT auth and bcrypt password hashing
- MongoDB-oriented data layer with a `mongomock` local fallback for development/tests
- Modular Python prediction service wired to `ml-model/src/serving/inference.py`
- Seeded metro stations and historical passenger flow data

## Stack

- Frontend: React 18, TypeScript, Tailwind CSS, Recharts
- Backend: FastAPI, JWT 
- Database: MongoDB
- ML module: Python inference helper in `ml-model/`

## Project Structure

```text
frontend/
  app/
    auth/         Login/register page
    dashboard/    Prediction dashboard
    history/      Historical analytics
    profile/      User profile
    admin/        Admin upload + model maintenance
  components/     Layout, theme, prediction, heatmap UI
  lib/            API, auth/session, export, formatting helpers
  middleware.ts   Protected route middleware

backend/
  app/
    api/routes/   Auth, dashboard, historical, profile, predict, admin APIs
    core/         Settings and JWT/bcrypt security helpers
    db/           Mongo client bootstrap
    schemas/      Pydantic request/response models
    services/     Seed data, analytics, prediction logic
  tests/          Backend API tests

ml-model/
  src/serving/    Reusable inference helper consumed by the backend
  src/training/   Training scaffold for future model refreshes

docs/
  architecture.md
  api-spec.md
  database-design.md
  deployment.md
```

## Core User Flows

### 1. Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### 2. Dashboard

- KPI cards for next-hour forecast, 24h volume, utilization, and model confidence
- Actual vs forecast chart
- Hourly distribution chart
- 7-day heatmap
- Recent predictions and recent station records tables
- CSV export for generated predictions

### 3. Historical Analytics

- Daily total passenger trend
- Average hourly distribution
- Multi-day hour-by-hour heatmap
- Recent observed station records

### 4. Profile

- Editable user metadata
- Theme preference
- Stored role and security metadata

### 5. Admin

- Create station flow records
- View latest uploaded/seeded flow rows
- Trigger model retraining simulation endpoint

## MongoDB Collections

- `users`
- `stations`
- `passenger_flows`
- `predictions`

See [docs/database-design.md](/c:/Users/Asus/Desktop/destop/1phase/docs/database-design.md) for the document schema.

## Local Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Recommended local `.env` for immediate startup:

```env
APP_NAME=MetroFlow Predictor API
API_PREFIX=/api/v1
SECRET_KEY=change-this-secret
ACCESS_TOKEN_EXPIRE_MINUTES=180
MONGODB_URI=mongomock://localhost
MONGODB_DATABASE=metroflow_predictor
CORS_ORIGINS=http://localhost:3000
MODEL_VERSION=metroflow-baseline-regression-v2
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Frontend env:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### Start Both Services

```powershell
.\start-dev.ps1
```

## Demo Credentials

- Admin: `admin@metroflow.ai` / `admin12345`
- User: `user@metroflow.ai` / `user12345`

## API Summary

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/stations`
- `GET /api/v1/dashboard/overview`
- `GET /api/v1/historical/analytics`
- `GET /api/v1/profile`
- `PUT /api/v1/profile`
- `POST /api/v1/predict`
- `POST /api/v1/train`
- `GET /api/v1/admin/flows`
- `POST /api/v1/admin/flows`
- `PUT /api/v1/admin/flows/{flow_id}`
- `DELETE /api/v1/admin/flows/{flow_id}`

Full request/response examples live in [docs/api-spec.md](/c:/Users/Asus/Desktop/destop/1phase/docs/api-spec.md).

## Testing And Verification

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
cd frontend
npm run build
```

Verified in this workspace:

- Backend tests: `6 passed`
- Frontend build: successful production build on Next.js 14

## Deployment Notes

- Frontend: deploy `frontend/` to Vercel or Netlify
- Backend: deploy `backend/` to Render, Railway, AWS App Runner, or EC2
- Database: use MongoDB Atlas and set `MONGODB_URI`
- Secrets: store `SECRET_KEY`, `MONGODB_URI`, and `NEXT_PUBLIC_API_BASE_URL` as platform env vars

Detailed deployment steps are in [docs/deployment.md](/c:/Users/Asus/Desktop/destop/1phase/docs/deployment.md).
