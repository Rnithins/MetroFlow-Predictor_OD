# API Specification

Base URL: `/api/v1`

All protected endpoints require:

```text
Authorization: Bearer <jwt-token>
```

## Authentication

### `POST /auth/register`

Request:

```json
{
  "email": "planner@metroflow.ai",
  "full_name": "Aarav Menon",
  "password": "securePass1",
  "job_title": "Transit Planner",
  "organization": "MetroFlow Transit",
  "commute_line": "Blue"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "planner@metroflow.ai",
    "full_name": "Aarav Menon",
    "role": "user",
    "is_active": true,
    "job_title": "Transit Planner",
    "organization": "MetroFlow Transit",
    "commute_line": "Blue",
    "theme_preference": "system",
    "created_at": "2026-04-02T12:00:00Z",
    "updated_at": "2026-04-02T12:00:00Z"
  }
}
```

### `POST /auth/login`

Request:

```json
{
  "email": "admin@metroflow.ai",
  "password": "admin12345"
}
```

### `GET /auth/me`

Returns the currently authenticated user profile.

## Stations

### `GET /stations`

Response:

```json
[
  {
    "id": "station-uuid",
    "code": "CEN",
    "name": "Central Square",
    "line": "Blue",
    "zone": "A",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "baseline_capacity": 820,
    "is_interchange": true
  }
]
```

## Dashboard

### `GET /dashboard/overview?station_id=<station-id>`

Returns:

- KPI cards
- actual vs forecast trend series
- hourly distribution
- 7-day heatmap
- recent flow rows
- recent stored predictions
- alert cards

## Historical Analytics

### `GET /historical/analytics?station_id=<station-id>&days=14`

Response shape:

```json
{
  "generated_at": "2026-04-02T12:00:00Z",
  "station_id": "station-uuid",
  "station_name": "Central Square",
  "days": 14,
  "daily_totals": [
    { "label": "20 Mar", "total_passengers": 6430 }
  ],
  "hourly_average": [
    { "label": "08:00", "value": 642 }
  ],
  "heatmap": [
    { "day_label": "20 Mar", "values": [42, 31, 26, 25] }
  ],
  "latest_records": []
}
```

## Profile

### `GET /profile`

Returns the authenticated user wrapped as:

```json
{
  "user": {
    "id": "uuid",
    "email": "admin@metroflow.ai",
    "full_name": "Metro Admin"
  }
}
```

### `PUT /profile`

Request:

```json
{
  "full_name": "Metro Admin",
  "job_title": "Operations Director",
  "organization": "MetroFlow Transit",
  "commute_line": "Blue",
  "theme_preference": "dark"
}
```

## Prediction

### `POST /predict`

Request:

```json
{
  "station_id": "station-uuid",
  "horizon_hours": 2,
  "weather_factor": 1.1,
  "event_factor": 1.15
}
```

Response:

```json
{
  "id": "prediction-uuid",
  "station_id": "station-uuid",
  "station_name": "Central Square",
  "line": "Blue",
  "target_timestamp": "2026-04-02T14:00:00Z",
  "predicted_count": 684.42,
  "baseline_count": 612.18,
  "confidence_score": 0.88,
  "anomaly_score": 0.12,
  "recommended_action": "Pre-position standby train and stagger platform dispatch announcements.",
  "model_version": "metroflow-baseline-regression-v2",
  "generated_at": "2026-04-02T12:00:00Z"
}
```

## Admin

### `GET /admin/flows`

Returns the latest flow rows for admin review.

### `POST /admin/flows`

Request:

```json
{
  "station_id": "station-uuid",
  "timestamp": "2026-04-02T13:00:00Z",
  "passenger_count": 420,
  "avg_dwell_minutes": 3.3,
  "weather_code": "rain",
  "event_flag": true,
  "event_name": "Concert dispersal",
  "source": "admin-upload"
}
```

### `PUT /admin/flows/{flow_id}`

Example body:

```json
{
  "passenger_count": 430
}
```

### `DELETE /admin/flows/{flow_id}`

Deletes a flow row.

## Model Maintenance

### `POST /train`

Admin-only request:

```json
{
  "epochs": 24,
  "learning_rate": 0.001,
  "lookback_steps": 24
}
```

Response:

```json
{
  "status": "completed",
  "model_version": "metroflow-baseline-regression-v2",
  "rmse": 8.2,
  "mae": 6.0,
  "message": "Re-trained forecast weights for 24 epochs with lookback 24."
}
```

## Error Handling

- `401`: missing or invalid JWT
- `403`: admin access required
- `404`: station or flow record not found
- `422`: request validation error
- `500`: unexpected server error
