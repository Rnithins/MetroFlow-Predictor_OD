from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
import pandas as pd
from pymongo.database import Database
from app.services.documents import new_id, utc_now


def clean_gtfs_stops(stops_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans, validates, and standardizes GTFS stops.txt dataframe.
    """
    df = stops_df.copy()
    
    # Required columns check
    req_cols = ["stop_id", "stop_name", "stop_lat", "stop_lon"]
    for col in req_cols:
        if col not in df.columns:
            raise ValueError(f"GTFS stops.txt is missing required column: '{col}'")

    # Clean data types & strings
    df["stop_id"] = df["stop_id"].astype(str).str.strip()
    df["stop_name"] = df["stop_name"].astype(str).str.strip().str.title()
    df["stop_lat"] = pd.to_numeric(df["stop_lat"], errors="coerce")
    df["stop_lon"] = pd.to_numeric(df["stop_lon"], errors="coerce")

    # Filter invalid coordinates
    df = df.dropna(subset=["stop_lat", "stop_lon"])
    df = df[(df["stop_lat"] >= -90.0) & (df["stop_lat"] <= 90.0)]
    df = df[(df["stop_lon"] >= -180.0) & (df["stop_lon"] <= 180.0)]

    # Deduplicate by stop_id or exact coordinates
    df = df.drop_duplicates(subset=["stop_id"])
    df = df.drop_duplicates(subset=["stop_lat", "stop_lon"])

    return df


def clean_gtfs_routes(routes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes GTFS routes.txt dataframe.
    """
    df = routes_df.copy()
    if "route_id" not in df.columns:
        raise ValueError("GTFS routes.txt is missing 'route_id' column")

    df["route_id"] = df["route_id"].astype(str).str.strip()
    
    # Construct display route name
    if "route_short_name" in df.columns and "route_long_name" in df.columns:
        df["route_name"] = df["route_short_name"].fillna("") + " " + df["route_long_name"].fillna("")
        df["route_name"] = df["route_name"].str.strip()
    elif "route_long_name" in df.columns:
        df["route_name"] = df["route_long_name"].astype(str)
    else:
        df["route_name"] = df["route_id"].astype(str)

    if "route_color" not in df.columns:
        df["route_color"] = "3B82F6"  # Default Blue

    return df


def build_connections_graph(
    stops_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    trips_df: pd.DataFrame,
    stop_times_df: pd.DataFrame,
    transfers_df: pd.DataFrame | None = None
) -> dict:
    """
    Builds station sequence graph links, interchanges, and route metadata.
    """
    stops_clean = clean_gtfs_stops(stops_df)
    routes_clean = clean_gtfs_routes(routes_df)

    stop_ids = set(stops_clean["stop_id"])

    # Merge trips and stop_times
    trips_df["trip_id"] = trips_df["trip_id"].astype(str).str.strip()
    trips_df["route_id"] = trips_df["route_id"].astype(str).str.strip()
    
    stop_times_df["trip_id"] = stop_times_df["trip_id"].astype(str).str.strip()
    stop_times_df["stop_id"] = stop_times_df["stop_id"].astype(str).str.strip()
    stop_times_df["stop_sequence"] = pd.to_numeric(stop_times_df["stop_sequence"], errors="coerce").fillna(0)

    # Filter stop_times for valid stops
    st_filtered = stop_times_df[stop_times_df["stop_id"].isin(stop_ids)].copy()
    st_filtered = st_filtered.sort_values(by=["trip_id", "stop_sequence"])

    merged = st_filtered.merge(trips_df[["trip_id", "route_id"]], on="trip_id", how="inner")
    merged = merged.merge(routes_clean[["route_id", "route_name", "route_color"]], on="route_id", how="inner")

    # Track routes per stop to identify interchange stations
    stop_routes = merged.groupby("stop_id")["route_id"].unique().to_dict()

    # Add interchange stops from transfers.txt if available
    transfer_stops = set()
    if transfers_df is not None and not transfers_df.empty:
        if "from_stop_id" in transfers_df.columns:
            transfer_stops.update(transfers_df["from_stop_id"].astype(str).str.strip())
        if "to_stop_id" in transfers_df.columns:
            transfer_stops.update(transfers_df["to_stop_id"].astype(str).str.strip())

    # Build station records with interchange flag & GeoJSON
    stations_list = []
    stop_to_code_map = {}
    for _, row in stops_clean.iterrows():
        sid = str(row["stop_id"])
        code = f"GTFS_{sid}"
        routes_served = list(stop_routes.get(sid, []))
        is_interchange = len(routes_served) > 1 or sid in transfer_stops

        stop_to_code_map[sid] = code
        stations_list.append({
            "_id": new_id(),
            "code": code,
            "name": str(row["stop_name"]),
            "line": "/".join(routes_served) if routes_served else "Metro Line",
            "zone": "GTFS Zone",
            "latitude": float(row["stop_lat"]),
            "longitude": float(row["stop_lon"]),
            "location": {
                "type": "Point",
                "coordinates": [float(row["stop_lon"]), float(row["stop_lat"])]
            },
            "baseline_capacity": 3000 if is_interchange else 1500,
            "is_interchange": is_interchange,
            "gtfs_stop_id": sid
        })

    # Generate consecutive station graph edges
    connections = {}
    for trip_id, group in merged.groupby("trip_id"):
        group_rows = group.to_dict("records")
        for i in range(len(group_rows) - 1):
            curr_stop = group_rows[i]
            next_stop = group_rows[i + 1]
            
            u_code = stop_to_code_map.get(curr_stop["stop_id"])
            v_code = stop_to_code_map.get(next_stop["stop_id"])

            if not u_code or not v_code or u_code == v_code:
                continue

            edge_key = f"{u_code}->{v_code}"
            if edge_key not in connections:
                connections[edge_key] = {
                    "from_station_code": u_code,
                    "to_station_code": v_code,
                    "route_id": curr_stop["route_id"],
                    "route_name": curr_stop["route_name"],
                    "route_color": curr_stop["route_color"],
                    "trip_count": 1,
                    "estimated_travel_seconds": 180  # Default 3 mins between stations
                }
            else:
                connections[edge_key]["trip_count"] += 1

    return {
        "stations": stations_list,
        "connections": list(connections.values()),
        "routes": routes_clean.to_dict("records"),
        "total_stops": len(stations_list),
        "total_connections": len(connections),
        "interchange_count": sum(1 for s in stations_list if s["is_interchange"])
    }


def parse_gtfs_zip(zip_bytes: bytes) -> dict:
    """
    Extracts and parses CSV files from a GTFS ZIP archive bytes buffer.
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        files = {name: name for name in z.namelist()}

        def get_df(filename: str) -> pd.DataFrame:
            # Match exact or nested filename
            matched = [f for f in files if f.endswith(filename)]
            if not matched:
                return pd.DataFrame()
            with z.open(matched[0]) as f:
                return pd.read_csv(f)

        stops_df = get_df("stops.txt")
        routes_df = get_df("routes.txt")
        trips_df = get_df("trips.txt")
        stop_times_df = get_df("stop_times.txt")
        transfers_df = get_df("transfers.txt")

        if stops_df.empty or routes_df.empty or trips_df.empty or stop_times_df.empty:
            raise ValueError("GTFS ZIP must contain stops.txt, routes.txt, trips.txt, and stop_times.txt")

        return build_connections_graph(stops_df, routes_df, trips_df, stop_times_df, transfers_df)


def save_gtfs_feed_to_db(database: Database, parsed_gtfs: dict, city_name: str = "Delhi", feed_name: str = "Official GTFS Feed") -> dict:
    """
    Persists parsed GTFS stations, connections graph, and feed manifest into MongoDB.
    """
    feed_id = new_id()
    now = utc_now()

    stations = parsed_gtfs["stations"]
    connections = parsed_gtfs["connections"]

    # Upsert stations into database
    for st in stations:
        st["city"] = city_name
        st["state"] = city_name
        st["feed_id"] = feed_id
        existing = database.stations.find_one({"code": st["code"]})
        if existing:
            st_data = {k: v for k, v in st.items() if k != "_id"}
            database.stations.update_one({"_id": existing["_id"]}, {"$set": st_data})
        else:
            if "_id" not in st:
                st["_id"] = new_id()
            database.stations.insert_one(st)

    # Store connection edges
    for conn in connections:
        conn["city"] = city_name
        conn["feed_id"] = feed_id
        existing = database.station_connections.find_one({
            "from_station_code": conn["from_station_code"],
            "to_station_code": conn["to_station_code"]
        })
        if existing:
            conn_data = {k: v for k, v in conn.items() if k != "_id"}
            database.station_connections.update_one({"_id": existing["_id"]}, {"$set": conn_data})
        else:
            if "_id" not in conn:
                conn["_id"] = new_id()
            database.station_connections.insert_one(conn)

    # Save GTFS feed manifest record
    feed_doc = {
        "_id": feed_id,
        "feed_name": feed_name,
        "city": city_name,
        "uploaded_at": now,
        "total_stops": parsed_gtfs["total_stops"],
        "total_connections": parsed_gtfs["total_connections"],
        "interchange_count": parsed_gtfs["interchange_count"],
        "status": "active"
    }
    database.gtfs_feeds.insert_one(feed_doc)

    return {
        "feed_id": feed_id,
        "feed_name": feed_name,
        "city": city_name,
        "total_stops": parsed_gtfs["total_stops"],
        "total_connections": parsed_gtfs["total_connections"],
        "interchange_count": parsed_gtfs["interchange_count"],
        "status": "active"
    }


def create_sample_gtfs_zip_bytes() -> bytes:
    """
    Generates a sample synthetic GTFS ZIP feed in memory for instant testing and demonstration.
    """
    stops_csv = (
        "stop_id,stop_name,stop_lat,stop_lon\n"
        "S1,Central Terminal,28.6304,77.2177\n"
        "S2,North Junction,28.6675,77.2282\n"
        "S3,South Hub,28.5433,77.2065\n"
        "S4,East Gate,28.6280,77.2780\n"
    )
    routes_csv = (
        "route_id,route_short_name,route_long_name,route_color\n"
        "R1,Red,Red Line Express,EF4444\n"
        "R2,Blue,Blue Line Main,3B82F6\n"
    )
    trips_csv = (
        "route_id,service_id,trip_id\n"
        "R1,FULL,T1\n"
        "R2,FULL,T2\n"
    )
    stop_times_csv = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "T1,08:00:00,08:00:00,S1,1\n"
        "T1,08:05:00,08:05:00,S2,2\n"
        "T1,08:12:00,08:12:00,S3,3\n"
        "T2,08:00:00,08:00:00,S1,1\n"
        "T2,08:08:00,08:08:00,S4,2\n"
    )
    transfers_csv = (
        "from_stop_id,to_stop_id,transfer_type,min_transfer_time\n"
        "S1,S1,2,180\n"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("stops.txt", stops_csv)
        z.writestr("routes.txt", routes_csv)
        z.writestr("trips.txt", trips_csv)
        z.writestr("stop_times.txt", stop_times_csv)
        z.writestr("transfers.txt", transfers_csv)

    return buf.getvalue()
