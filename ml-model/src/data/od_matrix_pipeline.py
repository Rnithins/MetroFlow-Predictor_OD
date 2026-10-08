from __future__ import annotations

import hashlib
import io
from datetime import datetime, timedelta
import random
from typing import Any
import numpy as np
import pandas as pd


def anonymize_card_id(card_id: Any) -> str:
    """Anonymizes smart card ID using salted SHA-256 hashing."""
    raw = str(card_id).strip()
    return hashlib.sha256(f"metro_salt_{raw}".encode("utf-8")).hexdigest()[:16]


def parse_interval_to_timedelta_and_freq(time_interval: str) -> tuple[str, timedelta]:
    """
    Maps interval string (5m, 10m, 15m, 30m, 60m, 1h, 1d) to pandas frequency string and timedelta.
    """
    clean = str(time_interval).strip().lower()
    mapping = {
        "5m": ("5min", timedelta(minutes=5)),
        "5min": ("5min", timedelta(minutes=5)),
        "10m": ("10min", timedelta(minutes=10)),
        "10min": ("10min", timedelta(minutes=10)),
        "15m": ("15min", timedelta(minutes=15)),
        "15min": ("15min", timedelta(minutes=15)),
        "30m": ("30min", timedelta(minutes=30)),
        "30min": ("30min", timedelta(minutes=30)),
        "60m": ("60min", timedelta(minutes=60)),
        "1h": ("60min", timedelta(minutes=60)),
        "1hour": ("60min", timedelta(minutes=60)),
        "1d": ("1D", timedelta(days=1)),
        "daily": ("1D", timedelta(days=1)),
    }
    return mapping.get(clean, ("15min", timedelta(minutes=15)))


def process_raw_tap_logs(
    raw_data: pd.DataFrame | bytes | str | list[dict],
    time_interval: str = "15m",
    impute_missing_tapout: bool = True,
    anonymize: bool = True,
) -> dict[str, Any]:
    """
    Origin-Destination (OD) Matrix Aggregator Pipeline.
    Turns raw tap-in / tap-out logs into OD matrices over configurable windows (5m, 10m, 15m, 30m, 60m).

    Pipeline stages:
      1. Parse & standardize schema.
      2. Anonymize passenger card IDs.
      3. Deduplicate rapid re-taps within 30 seconds.
      4. Filter invalid journeys (tap-out before tap-in, duration < 2 mins, duration > 240 mins).
      5. Handle missing tap-out (statistical imputation or exclude).
      6. Aggregate flows across temporal buckets into Edge List and N x N dense matrix.
    """
    quality_metrics = {
        "total_records_ingested": 0,
        "exact_duplicates_removed": 0,
        "retaps_within_30s_removed": 0,
        "missing_tapout_imputed": 0,
        "missing_tapout_excluded": 0,
        "invalid_negative_duration_removed": 0,
        "short_duration_under_2m_removed": 0,
        "excessive_duration_over_4h_removed": 0,
        "valid_journeys_aggregated": 0,
        "unique_od_pairs": 0,
        "time_interval": time_interval,
    }

    # 1. Parse input
    if isinstance(raw_data, bytes):
        df = pd.read_csv(io.BytesIO(raw_data))
    elif isinstance(raw_data, str):
        df = pd.read_csv(raw_data)
    elif isinstance(raw_data, list):
        df = pd.DataFrame(raw_data)
    elif isinstance(raw_data, pd.DataFrame):
        df = raw_data.copy()
    else:
        raise ValueError(f"Unsupported raw_data type: {type(raw_data)}")

    if df.empty:
        return {
            "edge_list": [],
            "matrix_dense": {"stations": [], "matrix": []},
            "quality_metrics": quality_metrics,
            "dataframe": pd.DataFrame(),
        }

    quality_metrics["total_records_ingested"] = len(df)

    # Standardize column names
    col_map = {col: str(col).strip().lower() for col in df.columns}
    df.rename(columns=col_map, inplace=True)

    field_alias = {
        "card_id": ["card_id", "cardid", "smartcard_id", "user_id", "passenger_id", "card"],
        "tap_in_time": ["tap_in_time", "tapin_time", "tap_in", "in_time", "entry_time"],
        "origin_station": ["origin_station", "origin", "tap_in_station", "orig", "from_station", "entry_station"],
        "tap_out_time": ["tap_out_time", "tapout_time", "tap_out", "out_time", "exit_time"],
        "destination_station": ["destination_station", "destination", "tap_out_station", "dest", "to_station", "exit_station"],
    }

    resolved: dict[str, str] = {}
    for target, aliases in field_alias.items():
        for col in df.columns:
            if col in aliases:
                resolved[target] = col
                break

    # If simple aggregated flow format passed directly
    if ("origin" in df.columns or "origin_station" in df.columns) and ("destination" in df.columns or "destination_station" in df.columns) and ("passenger_count" in df.columns or "passenger_flow" in df.columns):
        orig_col = resolved.get("origin_station", "origin")
        dest_col = resolved.get("destination_station", "destination")
        cnt_col = "passenger_count" if "passenger_count" in df.columns else "passenger_flow"
        time_col = "time" if "time" in df.columns else ("timestamp" if "timestamp" in df.columns else None)
        
        edge_list = []
        for _, row in df.iterrows():
            edge_list.append({
                "origin_station_code": str(row[orig_col]),
                "destination_station_code": str(row[dest_col]),
                "window_start": str(row[time_col]) if time_col else datetime.utcnow().isoformat(),
                "window_end": (pd.to_datetime(row[time_col]) + timedelta(minutes=15)).isoformat() if time_col else datetime.utcnow().isoformat(),
                "passenger_count": int(row[cnt_col]),
                "avg_travel_minutes": float(row.get("avg_travel_minutes", 15.0)),
            })
        return {
            "edge_list": edge_list,
            "matrix_dense": _build_dense_matrix(edge_list),
            "quality_metrics": quality_metrics,
            "dataframe": df,
        }

    # Verify minimum required columns
    card_col = resolved.get("card_id")
    in_time_col = resolved.get("tap_in_time")
    orig_col = resolved.get("origin_station")

    if not card_col or not in_time_col or not orig_col:
        raise ValueError(f"Missing mandatory columns. Found columns: {list(df.columns)}. Expected card_id, tap_in_time, origin_station.")

    dest_col = resolved.get("destination_station")
    out_time_col = resolved.get("tap_out_time")

    # 2. Anonymize Card ID
    if anonymize:
        df["card_hash"] = df[card_col].apply(anonymize_card_id)
        card_key = "card_hash"
    else:
        card_key = card_col

    # Drop null origin or tap_in_time
    df = df.dropna(subset=[in_time_col, orig_col])

    # Convert timestamps
    df["dt_tap_in"] = pd.to_datetime(df[in_time_col], errors="coerce")
    df = df.dropna(subset=["dt_tap_in"])

    # 3. Deduplicate exact records & rapid re-taps within 30 seconds
    before_dedup = len(df)
    df = df.drop_duplicates()
    quality_metrics["exact_duplicates_removed"] = before_dedup - len(df)

    # Sort to detect 30s re-taps
    df = df.sort_values(by=[card_key, orig_col, "dt_tap_in"])
    time_diff = df.groupby([card_key, orig_col])["dt_tap_in"].diff().dt.total_seconds()
    is_retap = time_diff < 30.0
    quality_metrics["retaps_within_30s_removed"] = int(is_retap.sum())
    df = df[~is_retap].copy()

    # 4. Handle Missing Tap-Out
    if out_time_col and out_time_col in df.columns:
        df["dt_tap_out"] = pd.to_datetime(df[out_time_col], errors="coerce")
    else:
        df["dt_tap_out"] = pd.NaT

    missing_out = df["dt_tap_out"].isna()
    if impute_missing_tapout:
        # Impute tap_out = tap_in + median duration (20 minutes default)
        quality_metrics["missing_tapout_imputed"] = int(missing_out.sum())
        df.loc[missing_out, "dt_tap_out"] = df.loc[missing_out, "dt_tap_in"] + pd.Timedelta(minutes=20)
    else:
        quality_metrics["missing_tapout_excluded"] = int(missing_out.sum())
        df = df[~missing_out].copy()

    # Destination handling
    if dest_col and dest_col in df.columns:
        # If dest missing, default to orig or placeholder
        df["dest_clean"] = df[dest_col].fillna(df[orig_col])
    else:
        df["dest_clean"] = df[orig_col]

    # 5. Journey Duration Filtering
    df["duration_minutes"] = (df["dt_tap_out"] - df["dt_tap_in"]).dt.total_seconds() / 60.0

    # Negative duration (tap-out before tap-in)
    neg_duration = df["duration_minutes"] < 0
    quality_metrics["invalid_negative_duration_removed"] = int(neg_duration.sum())
    df = df[~neg_duration].copy()

    # Duration < 2 minutes (immediate turn-around)
    short_duration = df["duration_minutes"] < 2.0
    quality_metrics["short_duration_under_2m_removed"] = int(short_duration.sum())
    df = df[~short_duration].copy()

    # Duration > 240 minutes (4 hours timeout / evasion)
    long_duration = df["duration_minutes"] > 240.0
    quality_metrics["excessive_duration_over_4h_removed"] = int(long_duration.sum())
    df = df[~long_duration].copy()

    quality_metrics["valid_journeys_aggregated"] = len(df)

    if df.empty:
        return {
            "edge_list": [],
            "matrix_dense": {"stations": [], "matrix": []},
            "quality_metrics": quality_metrics,
            "dataframe": pd.DataFrame(),
        }

    # 6. Temporal Aggregation by Configurable Interval
    pandas_freq, interval_delta = parse_interval_to_timedelta_and_freq(time_interval)
    df["window_start"] = df["dt_tap_in"].dt.floor(pandas_freq)
    df["window_end"] = df["window_start"] + interval_delta

    # Group into Edge List
    grouped = df.groupby([orig_col, "dest_clean", "window_start", "window_end"]).agg(
        passenger_count=(card_key, "count"),
        avg_travel_minutes=("duration_minutes", "mean")
    ).reset_index()

    quality_metrics["unique_od_pairs"] = len(grouped)

    edge_list = []
    for _, row in grouped.iterrows():
        edge_list.append({
            "origin_station_code": str(row[orig_col]),
            "destination_station_code": str(row["dest_clean"]),
            "window_start": row["window_start"].strftime("%Y-%m-%d %H:%M:%S"),
            "window_end": row["window_end"].strftime("%Y-%m-%d %H:%M:%S"),
            "passenger_count": int(row["passenger_count"]),
            "avg_travel_minutes": round(float(row["avg_travel_minutes"]), 2),
        })

    # Sort edge list by window_start and passenger_count descending
    edge_list.sort(key=lambda x: (x["window_start"], -x["passenger_count"]))

    # Also build DataFrame representation for backward compatibility
    summary_df = pd.DataFrame([
        {
            "Origin": item["origin_station_code"],
            "Destination": item["destination_station_code"],
            "Time": item["window_start"],
            "Passenger_Count": item["passenger_count"],
            "Avg_Travel_Minutes": item["avg_travel_minutes"]
        }
        for item in edge_list
    ])

    return {
        "edge_list": edge_list,
        "matrix_dense": _build_dense_matrix(edge_list),
        "quality_metrics": quality_metrics,
        "dataframe": summary_df,
    }


def _build_dense_matrix(edge_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Constructs an N x N dense matrix from edge list records."""
    stations = sorted(list({e["origin_station_code"] for e in edge_list} | {e["destination_station_code"] for e in edge_list}))
    idx_map = {st: i for i, st in enumerate(stations)}
    n = len(stations)
    matrix = [[0] * n for _ in range(n)]

    for e in edge_list:
        i = idx_map.get(e["origin_station_code"])
        j = idx_map.get(e["destination_station_code"])
        if i is not None and j is not None:
            matrix[i][j] += e["passenger_count"]

    return {
        "stations": stations,
        "matrix": matrix,
        "dimension": n,
    }


def generate_sample_tap_logs(num_records: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic raw smart card tap-in/tap-out log records for testing."""
    random.seed(seed)
    np.random.seed(seed)

    stations = ["DEL_RAJ", "DEL_KAS", "DEL_HOU", "DEL_NOI", "DEL_ND03", "DEL_INA", "DEL_CP"]
    cards = [f"METROCARD_{10000 + i}" for i in range(120)]
    start_time = datetime(2026, 7, 30, 8, 0, 0)

    data = []
    for _ in range(num_records):
        card_id = random.choice(cards)
        orig = random.choice(stations)
        dest = random.choice([s for s in stations if s != orig])
        offset_mins = random.randint(0, 180)
        travel_duration = random.randint(5, 55)

        tap_in = start_time + timedelta(minutes=offset_mins)
        tap_out = tap_in + timedelta(minutes=travel_duration)

        data.append({
            "Card_ID": card_id,
            "Tap_In_Time": tap_in.strftime("%Y-%m-%d %H:%M:%S"),
            "Origin_Station": orig,
            "Tap_Out_Time": tap_out.strftime("%Y-%m-%d %H:%M:%S"),
            "Destination_Station": dest,
        })

    # Add a few deliberate anomalies to test filtering
    # 1. 25-second re-tap (should be filtered out)
    data.append({
        "Card_ID": "METROCARD_10001",
        "Tap_In_Time": (start_time + timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "Origin_Station": "DEL_RAJ",
        "Tap_Out_Time": (start_time + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "Destination_Station": "DEL_KAS",
    })
    data.append({
        "Card_ID": "METROCARD_10001",
        "Tap_In_Time": (start_time + timedelta(seconds=25)).strftime("%Y-%m-%d %H:%M:%S"),
        "Origin_Station": "DEL_RAJ",
        "Tap_Out_Time": (start_time + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "Destination_Station": "DEL_KAS",
    })
    # 2. 1-minute duration (should be filtered out)
    data.append({
        "Card_ID": "METROCARD_10002",
        "Tap_In_Time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "Origin_Station": "DEL_RAJ",
        "Tap_Out_Time": (start_time + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "Destination_Station": "DEL_RAJ",
    })

    return pd.DataFrame(data)
