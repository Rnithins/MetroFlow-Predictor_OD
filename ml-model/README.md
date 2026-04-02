# ML Module

## Pipeline

1. Preprocess raw OD flow data.
2. Build temporal, spatial, and external-context features.
3. Train a hybrid LSTM + graph encoder model.
4. Evaluate with RMSE and MAE.
5. Export approved model artifacts for backend inference.

## Feature Engineering

- Time-based: hour, day of week, weekend, peak-hour flags
- Spatial graph-based: station connectivity embeddings
- External context: weather factor, event factor

## Deployment Strategy

- bundle artifacts in container image for starter deployments
- move artifacts to S3/GCS for scaled deployments
- expose predictions through FastAPI inference endpoints
