# Database Design

MetroFlow Predictor uses MongoDB collections instead of relational tables. Documents use string UUIDs as `_id` values for predictable API serialization.

## Collections

### `users`

```json
{
  "_id": "uuid",
  "email": "admin@metroflow.ai",
  "full_name": "Metro Admin",
  "password_hash": "<bcrypt-hash>",
  "role": "admin",
  "is_active": true,
  "job_title": "Operations Director",
  "organization": "MetroFlow Transit",
  "commute_line": "Blue",
  "theme_preference": "system",
  "created_at": "2026-04-02T12:00:00Z",
  "updated_at": "2026-04-02T12:00:00Z"
}
```

### `stations`

```json
{
  "_id": "uuid",
  "code": "CEN",
  "name": "Central Square",
  "line": "Blue",
  "zone": "A",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "baseline_capacity": 820,
  "is_interchange": true
}
```

### `passenger_flows`

```json
{
  "_id": "uuid",
  "station_id": "station-uuid",
  "timestamp": "2026-04-02T13:00:00Z",
  "passenger_count": 420,
  "avg_dwell_minutes": 3.3,
  "weather_code": "rain",
  "event_flag": true,
  "event_name": "Concert dispersal",
  "source": "seed"
}
```

### `predictions`

```json
{
  "_id": "uuid",
  "station_id": "station-uuid",
  "target_timestamp": "2026-04-02T14:00:00Z",
  "predicted_count": 684.42,
  "baseline_count": 612.18,
  "confidence_score": 0.88,
  "anomaly_score": 0.12,
  "recommended_action": "Pre-position standby train and stagger platform dispatch announcements.",
  "model_version": "metroflow-baseline-regression-v2",
  "generated_at": "2026-04-02T12:00:00Z",
  "created_by": "admin@metroflow.ai"
}
```

## Index Strategy

- `users.email` unique index
- `stations.code` unique index
- `passenger_flows (station_id, timestamp)` compound index
- `predictions (station_id, target_timestamp)` compound index

## Notes

- `mongomock` is used in local tests and can be used in local development via `MONGODB_URI=mongomock://localhost`.
- Production should use MongoDB Atlas or a managed MongoDB cluster.
- Prediction documents act as a lightweight cache of recently generated forecast results.
