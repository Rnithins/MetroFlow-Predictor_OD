from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pymongo.database import Database

from app.api.deps import get_optional_user, get_db, require_admin, get_current_user
from app.services.gtfs_pipeline import (
    create_sample_gtfs_zip_bytes,
    parse_gtfs_zip,
    save_gtfs_feed_to_db,
)

router = APIRouter(tags=["gtfs"])


@router.post("/upload")
async def upload_gtfs_feed(
    file: UploadFile = File(...),
    city: str = Form("Delhi"),
    feed_name: str = Form("Official GTFS Feed"),
    db: Database = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> dict:
    """
    Accepts an official GTFS feed ZIP archive containing stops.txt, routes.txt, trips.txt, stop_times.txt.
    Performs Pandas data cleaning, builds connection graphs, and stores GeoJSON stations in MongoDB.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a valid GTFS .zip archive.")

    try:
        contents = await file.read()
        parsed_gtfs = parse_gtfs_zip(contents)
        result = save_gtfs_feed_to_db(db, parsed_gtfs, city_name=city, feed_name=feed_name)
        return {
            "message": f"Successfully processed GTFS feed '{feed_name}' for city {city}.",
            "feed_details": result
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process GTFS feed: {str(e)}")


@router.post("/sample-ingest")
def sample_ingest_gtfs(
    city: str = "Delhi",
    db: Database = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> dict:
    """
    Ingests a synthetic sample GTFS feed for instant testing and demonstration.
    """
    zip_bytes = create_sample_gtfs_zip_bytes()
    parsed_gtfs = parse_gtfs_zip(zip_bytes)
    result = save_gtfs_feed_to_db(db, parsed_gtfs, city_name=city, feed_name="Sample Delhi GTFS Feed")
    return {
        "message": "Sample GTFS feed successfully ingested into network database.",
        "feed_details": result
    }


@router.get("/feeds")
def list_gtfs_feeds(
    city: str | None = None,
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
) -> list[dict]:
    """
    Lists ingested GTFS feed manifests with stop counts, routes, and interchange statistics.
    """
    query = {"city": city} if city else {}
    feeds = list(db.gtfs_feeds.find(query).sort("uploaded_at", -1))
    for f in feeds:
        f["id"] = f.pop("_id")
    return feeds


@router.get("/graph")
def get_gtfs_network_graph(
    city: str = "Delhi",
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
) -> dict:
    """
    Returns station network graph nodes, directed sequence edges, and interchange transfers.
    """
    stations = list(db.stations.find({"city": city}))
    if not stations:
        stations = list(db.stations.find({}))

    connections = list(db.station_connections.find({"city": city}))
    if not connections:
        connections = list(db.station_connections.find({}))

    nodes = []
    for st in stations:
        nodes.append({
            "code": st.get("code"),
            "name": st.get("name"),
            "line": st.get("line"),
            "latitude": st.get("latitude"),
            "longitude": st.get("longitude"),
            "is_interchange": st.get("is_interchange", False),
            "capacity": st.get("baseline_capacity", 1500)
        })

    edges = []
    for conn in connections:
        edges.append({
            "from_station": conn.get("from_station_code"),
            "to_station": conn.get("to_station_code"),
            "route_name": conn.get("route_name", "Metro Line"),
            "route_color": conn.get("route_color", "3B82F6"),
            "travel_seconds": conn.get("estimated_travel_seconds", 180)
        })

    return {
        "city": city,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "interchange_count": sum(1 for n in nodes if n["is_interchange"]),
        "nodes": nodes,
        "edges": edges
    }
