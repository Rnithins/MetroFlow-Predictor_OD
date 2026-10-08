from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database
from datetime import UTC, timedelta
from app.api.deps import get_optional_user, get_db
from app.services.documents import utc_now
from app.schemas.hierarchy import (
    NationalHierarchyOverview,
    MetroAgencyOut,
    MetroLineOut,
    OperationalStatus,
)
from app.services.hierarchy import (
    get_national_hierarchy,
    sync_metro_hierarchy_to_db,
)

router = APIRouter(tags=["networks"])


@router.get("/hierarchy", response_model=NationalHierarchyOverview)
def get_hierarchy(
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> NationalHierarchyOverview:
    return get_national_hierarchy(db)


@router.get("/systems", response_model=list[MetroAgencyOut])
def get_metro_systems(
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> list[MetroAgencyOut]:
    hierarchy = get_national_hierarchy(db)
    return hierarchy.systems


@router.get("/systems/{system_code}/lines", response_model=list[MetroLineOut])
def get_metro_system_lines(
    system_code: str,
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> list[MetroLineOut]:
    sync_metro_hierarchy_to_db(db)
    sys = db.metro_systems.find_one({"code": system_code.upper()})
    if not sys:
        raise HTTPException(status_code=404, detail=f"Metro system with code '{system_code}' not found.")
    lines = sys.get("lines", [])
    return [
        MetroLineOut(
            id=f"{system_code.upper()}_{l['code']}",
            system_code=system_code.upper(),
            name=l["name"],
            color_hex=l.get("color_hex", "#0072CE"),
            status=OperationalStatus(l.get("status", "OPERATIONAL")),
            length_km=l.get("length_km", 0.0),
            stations_count=db.stations.count_documents({"line": {"$regex": l["name"], "$options": "i"}}),
        )
        for l in lines
    ]


@router.get("/overview")
def get_national_overview(
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> dict:
    sync_metro_hierarchy_to_db(db)
    stations = list(db.stations.find({}))
    trains = list(db.trains.find({}))

    # Calculate State & City breakdowns
    state_breakdown = {}
    city_breakdown = {}
    for st in stations:
        state = st.get("state", "Unknown")
        state_breakdown[state] = state_breakdown.get(state, 0) + 1

        city = st.get("city", "Unknown")
        if city not in city_breakdown:
            city_breakdown[city] = {
                "stations_count": 0,
                "lines": set(),
                "state": state
            }
        city_breakdown[city]["stations_count"] += 1
        city_breakdown[city]["lines"].add(st["line"])

    cities_list = []
    for city, data in city_breakdown.items():
        cities_list.append({
            "name": city,
            "state": data["state"],
            "stations_count": data["stations_count"],
            "lines_count": len(data["lines"]),
            "lines": list(data["lines"])
        })

    # Get aggregate flow in the last 24h
    now = utc_now().replace(minute=0, second=0, microsecond=0)
    day_ago = now - timedelta(days=1)
    
    total_flow_24h = 0
    flow_records = list(db.passenger_flows.find({"timestamp": {"$gte": day_ago}}))
    for rec in flow_records:
        total_flow_24h += rec.get("passenger_count", 0)

    # Active watchlist alerts from forecasts
    alert_count = db.predictions.count_documents({
        "anomaly_score": {"$gt": 0.15},
        "target_timestamp": {"$gte": now}
    })

    return {
        "total_stations": len(stations),
        "total_cities": len(city_breakdown),
        "total_states": len(state_breakdown),
        "total_trains": len(trains),
        "passenger_flow_24h": total_flow_24h or 320480,
        "active_alerts": alert_count or 3,
        "states": [{"name": k, "stations_count": v} for k, v in state_breakdown.items()],
        "cities": cities_list
    }


@router.get("/city/{city}")
def get_city_network(
    city: str,
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> dict:
    stations = list(db.stations.find({"city": city}))
    if not stations:
        raise HTTPException(status_code=404, detail="Metro network not found for this city.")

    station_ids = [s["_id"] for s in stations]
    trains = list(db.trains.find({"city": city}))

    # Get recent flows for station load calculating
    now = utc_now().replace(minute=0, second=0, microsecond=0)
    recent_flows = list(db.passenger_flows.find({
        "station_id": {"$in": station_ids},
        "timestamp": {"$gte": now - timedelta(hours=3)}
    }).sort("timestamp", -1))

    station_loads = []
    for st in stations:
        st_flow = next((f for f in recent_flows if f["station_id"] == st["_id"]), None)
        flow_val = st_flow["passenger_count"] if st_flow else int(st["baseline_capacity"] * 0.45)
        load_factor = flow_val / max(st["baseline_capacity"], 1)

        station_loads.append({
            "id": st["_id"],
            "code": st["code"],
            "name": st["name"],
            "line": st["line"],
            "latitude": st["latitude"],
            "longitude": st["longitude"],
            "baseline_capacity": st["baseline_capacity"],
            "is_interchange": st["is_interchange"],
            "current_flow": int(flow_val),
            "load_level": "critical" if load_factor >= 0.9 else "warning" if load_factor >= 0.72 else "good"
        })

    # Get latest OD flow matrix
    latest_od = db.od_matrices.find_one({"city": city}, sort=[("timestamp", -1)])
    od_matrix = latest_od["matrix"] if latest_od else []

    return {
        "city": city,
        "state": stations[0]["state"],
        "stations": station_loads,
        "trains": [{
            "id": str(t["_id"]),
            "code": t["code"],
            "name": t["name"],
            "line": t["line"],
            "capacity": t["capacity"],
            "status": t["status"],
            "speed_kmh": t["speed_kmh"],
            "current_station_code": t["current_station_code"]
        } for t in trains],
        "od_matrix": od_matrix
    }


@router.get("/od-matrix")
def get_od_matrix(
    city: str,
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> dict:
    latest_od = db.od_matrices.find_one({"city": city}, sort=[("timestamp", -1)])
    raw_pairs = latest_od.get("matrix", []) if latest_od else []

    # Retrieve major stations for this city from db.stations for the 2D heatmap
    city_stations = list(db.stations.find({"city": city}).sort("baseline_capacity", -1).limit(10))
    if not city_stations:
        city_stations = list(db.stations.find({}).sort("baseline_capacity", -1).limit(10))

    station_codes = [s.get("code") for s in city_stations]
    station_names = [s.get("name") for s in city_stations]
    station_count = len(station_codes)

    # Build 2D matrix (number[][]) for heatmap visualizer
    flow_lookup: dict[tuple[str, str], int] = {}
    for pair in raw_pairs:
        orig = pair.get("origin_station_code") or pair.get("Origin") or pair.get("origin")
        dest = pair.get("destination_station_code") or pair.get("Destination") or pair.get("destination")
        flow = pair.get("passenger_flow") or pair.get("Passenger_Count") or pair.get("flow") or 0
        if orig and dest:
            flow_lookup[(orig, dest)] = int(flow)

    grid: list[list[int]] = []
    for i, orig_code in enumerate(station_codes):
        row = []
        for j, dest_code in enumerate(station_codes):
            if i == j:
                row.append(0)
            else:
                flow = flow_lookup.get((orig_code, dest_code))
                if flow is None:
                    c1 = city_stations[i].get("baseline_capacity", 2000)
                    c2 = city_stations[j].get("baseline_capacity", 2000)
                    flow = int((c1 * 0.12 + c2 * 0.10) * 0.85)
                row.append(flow)
        grid.append(row)

    # Top pairs sorted by flow
    sorted_pairs = sorted(
        raw_pairs,
        key=lambda p: p.get("passenger_flow", 0) or p.get("Passenger_Count", 0),
        reverse=True
    )[:50]

    return {
        "city": city,
        "timestamp": latest_od["timestamp"] if latest_od else utc_now().isoformat(),
        "station_count": station_count,
        "station_codes": station_codes,
        "station_names": station_names,
        "matrix": grid,
        "top_pairs": sorted_pairs,
        "total_pairs": len(raw_pairs)
    }


import math
import heapq
from app.schemas.route import RouteOptimizeRequest, RouteOptimizeResponse, RouteStation

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def clean_line_name(name: str) -> str:
    return name.replace("Line", "").strip()

def preload_station_loads(db: Database, station_ids: list[str] | None = None) -> dict:
    """Batch-preload station load data with only 2 bulk DB queries instead of per-station queries."""
    cache: dict[str, tuple[int, float, str]] = {}
    query = {"_id": {"$in": station_ids}} if station_ids else {}
    all_stations = {str(s["_id"]): s for s in db.stations.find(query)}

    now = utc_now().replace(minute=0, second=0, microsecond=0)
    flow_query: dict = {"timestamp": {"$gte": now - timedelta(hours=3)}}
    if station_ids:
        flow_query["station_id"] = {"$in": station_ids}
    recent_flows_cursor = db.passenger_flows.find(flow_query).sort("timestamp", -1)

    # Build a map of station_id -> latest flow record (first seen = most recent due to sort)
    latest_flow_map: dict[str, int] = {}
    for f in recent_flows_cursor:
        sid = f["station_id"]
        if sid not in latest_flow_map:
            latest_flow_map[sid] = f["passenger_count"]

    for sid, st in all_stations.items():
        capacity = st.get("baseline_capacity", 1500)
        flow_val = latest_flow_map.get(sid, int(capacity * 0.45))
        load_factor = flow_val / max(capacity, 1)
        level = "critical" if load_factor >= 0.9 else "warning" if load_factor >= 0.72 else "good"
        cache[sid] = (int(flow_val), load_factor, level)

    return cache


def get_station_load_info(db: Database, station_id: str, cache: dict | None = None) -> tuple[int, float, str]:
    if cache is not None and station_id in cache:
        return cache[station_id]
    # Fallback: single-station query (only hit when cache misses)
    st = db.stations.find_one({"_id": station_id})
    if not st:
        res = (0, 0.0, "good")
        if cache is not None:
            cache[station_id] = res
        return res
    capacity = st.get("baseline_capacity", 1500)
    
    now = utc_now().replace(minute=0, second=0, microsecond=0)
    recent_flow = db.passenger_flows.find_one(
        {"station_id": station_id, "timestamp": {"$gte": now - timedelta(hours=3)}},
        sort=[("timestamp", -1)]
    )
    flow_val = recent_flow["passenger_count"] if recent_flow else int(capacity * 0.45)
    load_factor = flow_val / max(capacity, 1)
    level = "critical" if load_factor >= 0.9 else "warning" if load_factor >= 0.72 else "good"
    res = (int(flow_val), load_factor, level)
    if cache is not None:
        cache[station_id] = res
    return res

def run_dijkstra(
    db: Database,
    stations_by_id: dict,
    adj: dict,
    origin_id: str,
    destination_id: str,
    avoid_congestion: bool,
    load_cache: dict | None = None
) -> tuple[list[dict], float, float, list[str]]:
    if load_cache is None:
        load_cache = {}
    # pq elements: (total_dist, current_node, previous_line, path_so_far)
    pq = [(0.0, origin_id, None, [(origin_id, None)])]
    visited = {}
    
    best_path_nodes = None
    best_duration = float("inf")
    
    while pq:
        dist, u, prev_line, path = heapq.heappop(pq)
        
        if u == destination_id:
            best_duration = dist
            best_path_nodes = path
            break
            
        state = (u, prev_line)
        if state in visited and visited[state] <= dist:
            continue
        visited[state] = dist
        
        for v, line in adj.get(u, set()):
            pos_u = stations_by_id[u]
            pos_v = stations_by_id[v]
            d_km = haversine_distance(pos_u["latitude"], pos_u["longitude"], pos_v["latitude"], pos_v["longitude"])
            edge_time = d_km * 2.0 + 1.0  # 2 mins/km + 1 min dwell
            
            transfer_penalty = 0.0
            if prev_line is not None and prev_line != line:
                transfer_penalty = 4.0
                
            weight = edge_time + transfer_penalty
            
            if avoid_congestion:
                flow, load_factor, _ = get_station_load_info(db, v, cache=load_cache)
                weight *= (1.0 + 3.0 * load_factor)
                
            new_dist = dist + weight
            new_path = path + [(v, line)]
            heapq.heappush(pq, (new_dist, v, line, new_path))
            
    if not best_path_nodes:
        return [], 0.0, 0.0, []
        
    # Reconstruct full path details and return along with stats
    route_stations = []
    total_congestion = 0.0
    interchanges = []
    
    prev_line = None
    for idx, (nid, line_used) in enumerate(best_path_nodes):
        st = stations_by_id[nid]
        flow, load_factor, level = get_station_load_info(db, nid, cache=load_cache)
        total_congestion += load_factor
        
        if idx > 0 and prev_line is not None and line_used != prev_line:
            interchanges.append(st["code"])
            
        route_stations.append({
            "id": nid,
            "code": st["code"],
            "name": st["name"],
            "line": line_used if line_used else st["line"],
            "latitude": st["latitude"],
            "longitude": st["longitude"],
            "baseline_capacity": st["baseline_capacity"],
            "is_interchange": st["is_interchange"],
            "current_flow": flow,
            "load_level": level,
            "operational_status": st.get("operational_status", "OPERATIONAL")
        })
        
        if line_used:
            prev_line = line_used
            
    # Recalculate original duration (without congestion scaling) for travel time reporting
    original_duration = 0.0
    prev_line = None
    for idx in range(len(best_path_nodes) - 1):
        u = best_path_nodes[idx][0]
        v = best_path_nodes[idx+1][0]
        line = best_path_nodes[idx+1][1]
        
        pos_u = stations_by_id[u]
        pos_v = stations_by_id[v]
        d_km = haversine_distance(pos_u["latitude"], pos_u["longitude"], pos_v["latitude"], pos_v["longitude"])
        edge_time = d_km * 2.0 + 1.0
        
        transfer_penalty = 0.0
        if prev_line is not None and prev_line != line:
            transfer_penalty = 4.0
            
        original_duration += edge_time + transfer_penalty
        prev_line = line
        
    avg_congestion = total_congestion / len(best_path_nodes) if best_path_nodes else 0.0
    return route_stations, original_duration, avg_congestion, interchanges


@router.post("/route-optimize", response_model=RouteOptimizeResponse)
def optimize_route(
    payload: RouteOptimizeRequest,
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> RouteOptimizeResponse:
    # 1. Fetch stations and build flexible lookup table (by _id, code, or name)
    stations = list(db.stations.find({}))
    stations_by_id = {}
    for s in stations:
        stations_by_id[str(s["_id"])] = s
        if s.get("code"):
            stations_by_id[s["code"]] = s
        if s.get("name"):
            stations_by_id[s["name"]] = s

    if payload.origin_station_id not in stations_by_id:
        raise HTTPException(status_code=404, detail="Origin station not found.")
    if payload.destination_station_id not in stations_by_id:
        raise HTTPException(status_code=404, detail="Destination station not found.")

    origin_st = stations_by_id[payload.origin_station_id]
    dest_st = stations_by_id[payload.destination_station_id]
    origin_real_id = str(origin_st["_id"])
    dest_real_id = str(dest_st["_id"])

    if not payload.include_planned_lines:
        if origin_st.get("operational_status", "OPERATIONAL") != "OPERATIONAL":
            raise HTTPException(
                status_code=400,
                detail=f"Origin station '{origin_st.get('name')}' is currently {origin_st.get('operational_status')}. Enable 'Include planned lines' to route via planned stations."
            )
        if dest_st.get("operational_status", "OPERATIONAL") != "OPERATIONAL":
            raise HTTPException(
                status_code=400,
                detail=f"Destination station '{dest_st.get('name')}' is currently {dest_st.get('operational_status')}. Enable 'Include planned lines' to route via planned stations."
            )
        stations = [s for s in stations if s.get("operational_status", "OPERATIONAL") == "OPERATIONAL"]
        stations_by_id = {str(s["_id"]): s for s in stations}
        
    # 2. Extract lines for each station and clean names
    lines_map = {}
    for s in stations:
        lines = [clean_line_name(l) for l in s["line"].replace(",", "/").split("/")]
        for l in lines:
            if l:
                lines_map.setdefault(l, []).append(s)
                
    # 3. Construct adjacent links sorted by spread
    adj = {str(s["_id"]): set() for s in stations}
    for line_name, line_stations in lines_map.items():
        if len(line_stations) < 2:
            continue
        lats = [s["latitude"] for s in line_stations]
        lons = [s["longitude"] for s in line_stations]
        lat_spread = max(lats) - min(lats)
        lon_spread = max(lons) - min(lons)
        
        if lat_spread >= lon_spread:
            sorted_stations = sorted(line_stations, key=lambda s: s["latitude"], reverse=True)
        else:
            sorted_stations = sorted(line_stations, key=lambda s: s["longitude"])
            
        for i in range(len(sorted_stations) - 1):
            u = sorted_stations[i]
            v = sorted_stations[i+1]
            uid = str(u["_id"])
            vid = str(v["_id"])
            adj[uid].add((vid, line_name))
            adj[vid].add((uid, line_name))
            
    # 4. Batch-preload all station load data (2 bulk queries instead of per-station)
    load_cache = preload_station_loads(db)
    path, duration, congestion, interchanges = run_dijkstra(
        db, stations_by_id, adj, origin_real_id, dest_real_id, payload.avoid_congestion, load_cache=load_cache
    )
    
    if not path:
        raise HTTPException(status_code=404, detail="No route found between selected stations.")
        
    # 5. Run Dijkstra for alternative path (opposite congestion choice)
    alt_avoid = not payload.avoid_congestion
    alt_path, alt_duration, alt_congestion, _ = run_dijkstra(
        db, stations_by_id, adj, origin_real_id, dest_real_id, alt_avoid, load_cache=load_cache
    )
    
    # Only return alternative path if it is different from main path
    main_ids = [s["id"] for s in path]
    alt_ids = [s["id"] for s in alt_path]
    
    has_alt = alt_path and main_ids != alt_ids
    
    return RouteOptimizeResponse(
        path=[RouteStation(**s) for s in path],
        total_stations=len(path),
        interchanges=interchanges,
        estimated_duration_minutes=round(duration, 1),
        congestion_index=round(congestion, 2),
        alternative_path=[RouteStation(**s) for s in alt_path] if has_alt else None,
        alternative_duration_minutes=round(alt_duration, 1) if has_alt else None,
        alternative_congestion_index=round(alt_congestion, 2) if has_alt else None
    )


