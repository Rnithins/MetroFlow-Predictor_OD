import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.gtfs_pipeline import create_sample_gtfs_zip_bytes, parse_gtfs_zip


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def login_admin(client: TestClient) -> str:
    res = client.post("/api/v1/auth/login", json={"email": "admin@metroflow.ai", "password": "admin12345"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_parse_sample_gtfs_zip_bytes() -> None:
    zip_bytes = create_sample_gtfs_zip_bytes()
    parsed = parse_gtfs_zip(zip_bytes)
    assert parsed["total_stops"] >= 4
    assert parsed["total_connections"] >= 3
    assert "stations" in parsed
    assert "connections" in parsed


def test_sample_gtfs_ingest_and_graph_endpoints(client: TestClient) -> None:
    admin_token = login_admin(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    ingest_res = client.post("/api/v1/gtfs/sample-ingest?city=Delhi", headers=headers)
    assert ingest_res.status_code == 200
    payload = ingest_res.json()
    assert "feed_details" in payload
    assert payload["feed_details"]["total_stops"] >= 4

    feeds_res = client.get("/api/v1/gtfs/feeds?city=Delhi", headers=headers)
    assert feeds_res.status_code == 200
    feeds = feeds_res.json()
    assert len(feeds) > 0

    graph_res = client.get("/api/v1/gtfs/graph?city=Delhi", headers=headers)
    assert graph_res.status_code == 200
    graph = graph_res.json()
    assert graph["total_nodes"] > 0
    assert "nodes" in graph
    assert "edges" in graph
