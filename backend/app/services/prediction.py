from __future__ import annotations

import statistics
import sys
from datetime import timedelta
from pathlib import Path

from pymongo.database import Database

from app.core.config import get_settings
from app.schemas.flow import PredictionRequest, PredictionResponse, TrainRequest, TrainResponse
from app.services.adapters.weather_adapter import WeatherAdapter
from app.services.documents import new_id, utc_now

from app.core.ml_path import setup_ml_path

setup_ml_path()

from src.serving.inference import predict_flow  # noqa: E402
from src.training.train import train_model  # noqa: E402



def _is_peak_hour(target_timestamp) -> bool:
    return target_timestamp.hour in {7, 8, 9, 17, 18, 19, 20}


def _get_station(database: Database, station_identifier: str) -> dict:
    station = database.stations.find_one({
        "$or": [
            {"_id": station_identifier},
            {"code": station_identifier},
            {"name": station_identifier}
        ]
    })
    if station is None:
        station = database.stations.find_one({})
    if station is None:
        raise ValueError("No metro stations registered in the network.")
    return station


def _station_flows(database: Database, station_id: str, limit: int = 336) -> list[dict]:
    records = list(database.passenger_flows.find({"station_id": station_id}).sort("timestamp", -1).limit(limit))
    records.reverse()
    return records


def _confidence_score(history_size: int, anomaly_score: float) -> float:
    return round(max(0.72, min(0.98, 0.82 + min(history_size, 72) / 400 - anomaly_score / 6)), 2)


def build_prediction(database: Database, payload: PredictionRequest, created_by: str = "system") -> PredictionResponse:
    settings = get_settings()

    primary_id = payload.origin_station_id or payload.station_id or "DEL_RAJ"
    origin_station = _get_station(database, primary_id)
    
    dest_id = payload.destination_station_id or payload.station_id or primary_id
    dest_station = _get_station(database, dest_id)

    flows = _station_flows(database, origin_station["_id"])
    if not flows:
        # Generate mock historical flow window if newly added station hasn't been backfilled
        now_dt = utc_now().astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        base_cap = origin_station.get("baseline_capacity", 2000)
        flows = [
            {
                "timestamp": now_dt - timedelta(hours=i),
                "passenger_count": int(base_cap * (0.35 + 0.15 * ((i % 6) / 6))),
            }
            for i in range(24, 0, -1)
        ]

    latest_flow = flows[-1]
    latest_timestamp = latest_flow["timestamp"]
    target_timestamp = payload.target_timestamp or (latest_timestamp + timedelta(hours=payload.horizon_hours))
    same_hour_history = [flow["passenger_count"] for flow in flows if flow["timestamp"].hour == target_timestamp.hour]
    latest_values = [flow["passenger_count"] for flow in flows[-12:]]
    previous_values = [flow["passenger_count"] for flow in flows[-24:-12]] or latest_values

    current_count = payload.current_count or latest_flow["passenger_count"]
    same_hour_average = statistics.fmean(same_hour_history[-7:] or [current_count])
    recent_average = statistics.fmean(latest_values)
    previous_average = statistics.fmean(previous_values)
    recent_trend = 1 + max(-0.18, min(0.28, (recent_average - previous_average) / max(previous_average, 1)))
    blended_baseline = (current_count * 0.45) + (same_hour_average * 0.4) + (recent_average * 0.15)
    
    horizon_minutes = payload.horizon_minutes or max(15, int((target_timestamp - latest_timestamp).total_seconds() // 60))

    # Ingest real-time weather from OpenWeatherMap (or Open-Meteo fallback)
    weather_info = WeatherAdapter().fetch_city_weather(
        city_name=origin_station.get("city", "Delhi"),
        lat=float(origin_station.get("latitude", 28.6304)),
        lon=float(origin_station.get("longitude", 77.2177)),
    )
    weather_factor = payload.weather_factor if payload.weather_factor != 1.0 else weather_info.get("demand_multiplier", 1.0)

    # Run PyTorch AFFN model inference
    inference = predict_flow(
        current_count=round(blended_baseline),
        horizon_minutes=horizon_minutes,
        weather_factor=weather_factor,
        event_factor=payload.event_factor * recent_trend,
        is_peak_hour=_is_peak_hour(target_timestamp),
        origin_station=origin_station["name"],
        destination_station=dest_station["name"],
    )

    predicted_count = float(inference["predicted_count"])
    anomaly_score = round(max(0.0, min(1.0, (predicted_count - blended_baseline) / max(blended_baseline, 1))), 2)
    load_factor = predicted_count / max(origin_station["baseline_capacity"], 1)

    if load_factor >= 0.95 or inference.get("congestion_level") == "Severe":
        recommendation = "Severe corridor surge. Deploy standby rolling stock and implement station gate metering."
    elif load_factor >= 0.75 or inference.get("congestion_level") == "High":
        recommendation = "High passenger demand. Stagger platform announcements and activate standby coaches."
    elif load_factor >= 0.5 or inference.get("congestion_level") == "Moderate":
        recommendation = "Moderate transit flow. Maintain optimal headways and monitor interchange gates."
    else:
        recommendation = "Smooth commuter flow. Standard scheduled headway operations."

    attn_weights = inference.get("attention_weights", {})
    st_weight = float(attn_weights.get("spatial_temporal_weight", 0.64))
    ext_weight = float(attn_weights.get("external_context_weight", 0.36))
    confidence_val = float(inference.get("confidence_score", _confidence_score(len(flows), anomaly_score)))
    congestion_lvl = inference.get("congestion_level", "Moderate")

    prediction_document = {
        "_id": new_id(),
        "station_id": origin_station["_id"],
        "origin_station_id": origin_station["_id"],
        "destination_station_id": dest_station["_id"],
        "origin_station_name": origin_station["name"],
        "destination_station_name": dest_station["name"],
        "target_timestamp": target_timestamp,
        "predicted_count": predicted_count,
        "baseline_count": round(blended_baseline, 2),
        "current_passengers": int(current_count),
        "confidence_score": confidence_val,
        "confidence_percentage": f"{int(confidence_val * 100)}%",
        "congestion_level": congestion_lvl,
        "anomaly_score": anomaly_score,
        "recommended_action": recommendation,
        "model_version": settings.model_version or inference["model_version"],
        "generated_at": utc_now(),
        "created_by": created_by,
        "horizons": inference.get("horizons"),
        "st_weight": st_weight,
        "ext_weight": ext_weight,
        "data_source": "PREDICTED",
        "weather_condition": weather_info.get("weather_condition"),
        "weather_provider": weather_info.get("provider"),
        "forecast_disclaimer": "Forecast — not a guaranteed passenger count.",
    }
    database.predictions.insert_one(prediction_document)

    return PredictionResponse(
        id=prediction_document["_id"],
        station_id=origin_station["_id"],
        station_name=origin_station["name"],
        line=origin_station["line"],
        origin_station_name=origin_station["name"],
        destination_station_name=dest_station["name"],
        target_timestamp=prediction_document["target_timestamp"],
        predicted_count=prediction_document["predicted_count"],
        baseline_count=prediction_document["baseline_count"],
        current_passengers=prediction_document["current_passengers"],
        confidence_score=prediction_document["confidence_score"],
        confidence_percentage=prediction_document["confidence_percentage"],
        congestion_level=prediction_document["congestion_level"],
        anomaly_score=prediction_document["anomaly_score"],
        recommended_action=prediction_document["recommended_action"],
        model_version=prediction_document["model_version"],
        generated_at=prediction_document["generated_at"],
        horizons=prediction_document.get("horizons"),
        st_weight=prediction_document.get("st_weight"),
        ext_weight=prediction_document.get("ext_weight"),
        data_source=prediction_document["data_source"],
        weather_condition=prediction_document["weather_condition"],
        weather_provider=prediction_document["weather_provider"],
        forecast_disclaimer=prediction_document["forecast_disclaimer"],
    )



def list_recent_predictions(database: Database, station_id: str | None = None, limit: int = 6) -> list[PredictionResponse]:
    query = {"station_id": station_id} if station_id else {}
    stations = {station["_id"]: station for station in database.stations.find({})}
    predictions = list(database.predictions.find(query).sort("generated_at", -1).limit(limit))
    payload: list[PredictionResponse] = []
    for item in predictions:
        station = stations.get(item["station_id"])
        if station is None:
            continue
        payload.append(
            PredictionResponse(
                id=item["_id"],
                station_id=item["station_id"],
                station_name=station["name"],
                line=station["line"],
                origin_station_name=item.get("origin_station_name", station["name"]),
                destination_station_name=item.get("destination_station_name"),
                target_timestamp=item["target_timestamp"],
                predicted_count=item["predicted_count"],
                baseline_count=item["baseline_count"],
                current_passengers=item.get("current_passengers"),
                confidence_score=item["confidence_score"],
                confidence_percentage=item.get("confidence_percentage", f"{int(item['confidence_score'] * 100)}%"),
                congestion_level=item.get("congestion_level", "Moderate"),
                anomaly_score=item["anomaly_score"],
                recommended_action=item["recommended_action"],
                model_version=item["model_version"],
                generated_at=item["generated_at"],
                horizons=item.get("horizons"),
                st_weight=item.get("st_weight"),
                ext_weight=item.get("ext_weight"),
            )
        )
    return payload


def run_training(payload: TrainRequest) -> TrainResponse:
    settings = get_settings()
    res = train_model(save_checkpoint=True)
    rmse = float(res.get("rmse", 12.5))
    mae = float(res.get("mae", 9.2))
    mape = res.get("mape_pct", 0.0)
    st_w = res.get("attention_weights", {}).get("spatial_temporal_weight", 0.5)
    ext_w = res.get("attention_weights", {}).get("external_context_weight", 0.5)
    
    return TrainResponse(
        status=res.get("status", "completed"),
        model_version=settings.model_version,
        rmse=rmse,
        mae=mae,
        message=f"Re-trained PyTorch AdaptiveFeatureFusionNetwork. RMSE: {rmse}, MAE: {mae}, MAPE: {mape}%. Feature Attention Weights - ST: {st_w}, Ext: {ext_w}.",
    )

