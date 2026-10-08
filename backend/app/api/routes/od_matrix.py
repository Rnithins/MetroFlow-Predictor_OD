from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from pydantic import BaseModel, Field
from pymongo.database import Database
from app.api.deps import get_db
from app.services.documents import utc_now

from app.core.ml_path import setup_ml_path

setup_ml_path()

from src.data.od_matrix_pipeline import process_raw_tap_logs  # noqa: E402

router = APIRouter(tags=["od_matrix"])


class TapLogRecord(BaseModel):
    card_id: str = Field(description="Passenger smart card identifier")
    tap_in_time: str = Field(description="ISO or standard timestamp of tap-in")
    origin_station: str = Field(description="Origin station code or name")
    tap_out_time: str | None = Field(default=None, description="Optional tap-out timestamp")
    destination_station: str | None = Field(default=None, description="Optional destination station code")


class IngestTapLogsPayload(BaseModel):
    city: str = Field(default="Delhi", description="Metro city name")
    time_interval: str = Field(default="15m", description="Interval: 5m, 10m, 15m, 30m, 60m")
    impute_missing_tapout: bool = Field(default=True, description="Impute missing tap-outs with median travel duration")
    records: list[TapLogRecord] = Field(description="List of raw smart card tap log records")


@router.get("/od-matrix")
def get_od_matrix(
    city: str = Query("Delhi", description="Metro City Name"),
    time_interval: str = Query("15m", description="Time interval: 5m, 10m, 15m, 30m, 60m, 1h, 1d"),
    output_format: str = Query("edge_list", description="Output format: 'edge_list' or 'dense'"),
    origin: str | None = Query(None, description="Filter by Origin Station Code"),
    destination: str | None = Query(None, description="Filter by Destination Station Code"),
    db: Database = Depends(get_db)
) -> dict:
    """
    Returns the latest processed Origin-Destination Passenger Flow Matrix.
    Supports both edge list format and N x N dense matrix format.
    """
    query: dict[str, Any] = {}
    if city:
        query["city"] = city

    doc = db.od_matrices.find_one(query, sort=[("timestamp", -1)])

    if not doc:
        # Generate dynamic default OD matrix
        stations = ["DEL_RAJ", "DEL_KAS", "DEL_HOU", "DEL_NOI", "DEL_ND03"]
        matrix_rows = []
        for o in stations:
            for d in stations:
                if o != d:
                    matrix_rows.append({
                        "origin_station_code": o,
                        "destination_station_code": d,
                        "passenger_flow": 850 if (o == "DEL_RAJ" or d == "DEL_RAJ") else 320,
                        "avg_travel_minutes": 18.5,
                    })
        return {
            "city": city,
            "time_interval": time_interval,
            "timestamp": "2026-07-30T15:30:00Z",
            "format": output_format,
            "data_source": "SIMULATED",
            "total_pairs": len(matrix_rows),
            "matrix": matrix_rows
        }

    matrix_rows = doc.get("matrix", [])
    if origin:
        matrix_rows = [r for r in matrix_rows if r.get("origin_station_code") == origin or origin in str(r.get("origin_station_code"))]
    if destination:
        matrix_rows = [r for r in matrix_rows if r.get("destination_station_code") == destination or destination in str(r.get("destination_station_code"))]

    response: dict[str, Any] = {
        "city": doc.get("city", city),
        "time_interval": doc.get("time_interval", time_interval),
        "timestamp": doc.get("timestamp"),
        "format": output_format,
        "data_source": doc.get("data_source", "HISTORICAL"),
        "total_pairs": len(matrix_rows),
        "quality_metrics": doc.get("quality_metrics"),
    }

    if output_format == "dense":
        if "matrix_dense" in doc:
            response["matrix_dense"] = doc["matrix_dense"]
        else:
            stations = sorted(list({r["origin_station_code"] for r in matrix_rows} | {r["destination_station_code"] for r in matrix_rows}))
            idx_map = {st: i for i, st in enumerate(stations)}
            n = len(stations)
            dense_grid = [[0] * n for _ in range(n)]
            for r in matrix_rows:
                i = idx_map.get(r["origin_station_code"])
                j = idx_map.get(r["destination_station_code"])
                if i is not None and j is not None:
                    dense_grid[i][j] += r.get("passenger_flow", 0)
            response["matrix_dense"] = {
                "stations": stations,
                "matrix": dense_grid,
                "dimension": n,
            }
    else:
        response["matrix"] = matrix_rows

    return response


@router.post("/od-matrix/ingest")
def ingest_tap_logs_programmatic(
    payload: IngestTapLogsPayload,
    db: Database = Depends(get_db)
) -> dict:
    """
    Programmatic API ingestion of raw smart card tap logs.
    Runs the automated OD matrix pipeline with SHA-256 card hashing, rapid retap pruning,
    duration anomaly filtering, and persists to the database.
    """
    if not payload.records:
        raise HTTPException(status_code=400, detail="Payload must contain at least one tap log record.")

    raw_dicts = [r.model_dump() for r in payload.records]
    try:
        pipeline_result = process_raw_tap_logs(
            raw_dicts,
            time_interval=payload.time_interval,
            impute_missing_tapout=payload.impute_missing_tapout,
        )

        edge_list = pipeline_result["edge_list"]
        matrix_dense = pipeline_result["matrix_dense"]
        quality_metrics = pipeline_result["quality_metrics"]

        # Persist to od_matrices
        if edge_list and hasattr(db, "od_matrices"):
            db.od_matrices.insert_one({
                "city": payload.city,
                "timestamp": edge_list[0]["window_start"] if edge_list else utc_now().isoformat(),
                "time_interval": payload.time_interval,
                "data_source": "REALTIME",
                "quality_metrics": quality_metrics,
                "matrix": [
                    {
                        "origin_station_code": r["origin_station_code"],
                        "destination_station_code": r["destination_station_code"],
                        "passenger_flow": r["passenger_count"],
                        "avg_travel_minutes": r["avg_travel_minutes"],
                    }
                    for r in edge_list
                ],
                "matrix_dense": matrix_dense,
            })

        return {
            "status": "success",
            "message": f"Successfully ingested and aggregated {len(edge_list)} OD flow pairs.",
            "city": payload.city,
            "time_interval": payload.time_interval,
            "quality_metrics": quality_metrics,
            "edge_list_preview": edge_list[:50],
            "matrix_dense": matrix_dense,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to ingest tap logs: {str(exc)}") from exc
