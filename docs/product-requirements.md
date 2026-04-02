# MetroFlow Predictor Product Requirements

## Goal

Build a full-stack metro analytics application that predicts hourly and daily passenger flow, visualizes historical demand, and gives authenticated users an operations dashboard with modern UX.

## Required Modules

### Frontend

- Login/register page with validation
- Dashboard with KPI cards, charts, tables, alerts, and forecast generation
- Historical analytics page with line chart, hourly distribution, and heatmap
- User profile page
- Admin page for uploading new flow records and retraining the model
- Responsive layout
- Dark mode toggle
- CSV export for predictions

### Backend

- FastAPI REST API
- JWT authentication
- bcrypt password hashing
- Historical data endpoints
- Prediction endpoint
- Profile endpoint
- Admin CRUD for passenger flow records

### Database

- MongoDB collections for users, stations, passenger flows, and predictions

### ML Integration

- Reusable Python inference helper
- Modular prediction logic so the model can be replaced later without rewriting the API layer
