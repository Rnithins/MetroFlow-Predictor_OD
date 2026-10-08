from __future__ import annotations

import sys
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from pymongo.database import Database
from app.api.deps import get_db
from app.services.documents import utc_now

from app.core.ml_path import setup_ml_path

setup_ml_path()

from src.data.od_matrix_pipeline import process_raw_tap_logs, generate_sample_tap_logs  # noqa: E402

router = APIRouter(tags=["upload_od_pipeline"])


@router.post("/upload")
async def upload_tap_logs(
    file: UploadFile | None = File(None),
    city: str = Query("Delhi", description="Metro City Name"),
    time_interval: str = Query("15m", description="Aggregation interval: 5m, 10m, 15m, 30m, 60m, 1h, 1d"),
    impute_missing_tapout: bool = Query(True, description="Statistically impute missing tap-out timestamps (+20m median)"),
    db: Database = Depends(get_db)
) -> dict:
    """
    Automated OD Matrix Generation Pipeline.
    Upload raw smart-card tap logs (CSV) to clean, anonymize (SHA-256), deduplicate rapid re-taps (<30s),
    filter invalid journeys (<2m or >4h), and generate structured Origin-Destination matrices.
    """
    try:
        if file is not None:
            content = await file.read()
            pipeline_result = process_raw_tap_logs(
                content,
                time_interval=time_interval,
                impute_missing_tapout=impute_missing_tapout,
            )
        else:
            # Fallback to generating sample smart card tap log pipeline execution
            sample_df = generate_sample_tap_logs(num_records=300)
            pipeline_result = process_raw_tap_logs(
                sample_df,
                time_interval=time_interval,
                impute_missing_tapout=impute_missing_tapout,
            )

        edge_list = pipeline_result["edge_list"]
        matrix_dense = pipeline_result["matrix_dense"]
        quality_metrics = pipeline_result["quality_metrics"]
        od_matrix_df = pipeline_result["dataframe"]
        records = od_matrix_df.to_dict(orient="records") if not od_matrix_df.empty else []

        # Persist to database od_matrices collection
        if edge_list and hasattr(db, "od_matrices"):
            db.od_matrices.insert_one({
                "city": city,
                "timestamp": edge_list[0]["window_start"] if edge_list else utc_now().isoformat(),
                "time_interval": time_interval,
                "data_source": "HISTORICAL",
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
            "message": f"Successfully processed {len(edge_list)} OD matrix flow pairs.",
            "city": city,
            "time_interval": time_interval,
            "record_count": len(edge_list),
            "quality_metrics": quality_metrics,
            "edge_list": edge_list[:100],
            "matrix_dense": matrix_dense,
            "data": records[:100],  # Return preview rows for backward compatibility
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to process tap log file: {str(exc)}") from exc
