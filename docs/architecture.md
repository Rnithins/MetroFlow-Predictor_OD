# MetroFlow Predictor Architecture

## Overview

MetroFlow Predictor is implemented as a modular full-stack application:

1. Next.js frontend for authenticated UI and visualization
2. FastAPI backend for auth, analytics, profile, admin, and prediction APIs
3. MongoDB for users, stations, historical passenger flow, and cached predictions
4. Python ML helper module in `ml-model/` for reusable inference logic

## Architecture Diagram

```text
                 +-----------------------------+
                 |        Next.js Frontend     |
                 | auth / dashboard / history  |
                 | profile / admin / exports   |
                 +--------------+--------------+
                                |
                                | HTTPS + JWT
                                v
                 +-----------------------------+
                 |        FastAPI Backend      |
                 | auth / stations / dashboard |
                 | historical / profile        |
                 | predict / admin / train     |
                 +--------------+--------------+
                                |
            +-------------------+-------------------+
            |                                       |
            v                                       v
  +------------------------+             +------------------------+
  | MongoDB Collections    |             | Python ML Module       |
  | users                  |             | ml-model/src/serving   |
  | stations               |             | inference.py           |
  | passenger_flows        |             | training scaffolds     |
  | predictions            |             +------------------------+
  +------------------------+
```

## Backend Flow

1. User logs in or registers.
2. Backend creates a JWT and returns user metadata.
3. Frontend stores the token and protects app routes via middleware.
4. Dashboard and historical pages request station data and analytics from FastAPI.
5. Prediction requests call the ML inference helper plus recent historical statistics.
6. Generated predictions are written back to the `predictions` collection.
7. Admin users can upload new flow records or trigger model retraining simulation.

## Prediction Design

The prediction service blends:

- latest observed station load
- same-hour historical averages
- recent short-term trend
- weather/event multipliers
- ML helper output from `ml-model/src/serving/inference.py`

This keeps the serving layer modular while remaining easy to replace with a stronger model later.

## Frontend Design Notes

- App Router based Next.js structure
- Client-side session persistence plus cookie-based route protection
- Recharts for trend and distribution charts
- CSS-variable-driven light/dark theme
- CSV export for recent predictions
