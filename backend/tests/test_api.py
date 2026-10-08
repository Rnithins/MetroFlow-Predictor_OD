from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_profile_flow(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.user@metroflow.ai",
            "full_name": "New User",
            "password": "securePass1",
            "job_title": "Planner",
            "organization": "MetroFlow",
            "commute_line": "Blue",
        },
    )
    assert register_response.status_code == 201

    login_payload = login(client, "new.user@metroflow.ai", "securePass1")
    token = login_payload["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "new.user@metroflow.ai"

    update_response = client.put(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"theme_preference": "dark", "job_title": "Senior Planner"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["user"]["theme_preference"] == "dark"


def test_dashboard_and_historical_endpoints(client: TestClient) -> None:
    auth = login(client, "admin@metroflow.ai", "admin12345")
    token = auth["access_token"]

    stations_response = client.get("/api/v1/stations", headers={"Authorization": f"Bearer {token}"})
    assert stations_response.status_code == 200
    stations = stations_response.json()
    assert len(stations) >= 3

    dashboard_response = client.get("/api/v1/dashboard/overview", headers={"Authorization": f"Bearer {token}"})
    assert dashboard_response.status_code == 200
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["model_version"] == "metroflow-baseline-regression-v2"
    assert len(dashboard_payload["kpis"]) == 4
    assert len(dashboard_payload["trend"]) >= 12

    historical_response = client.get(
        "/api/v1/historical/analytics",
        headers={"Authorization": f"Bearer {token}"},
        params={"station_id": stations[0]["id"], "days": 7},
    )
    assert historical_response.status_code == 200
    assert len(historical_response.json()["daily_totals"]) >= 6


def test_prediction_endpoint_returns_forecast(client: TestClient) -> None:
    auth = login(client, "admin@metroflow.ai", "admin12345")
    token = auth["access_token"]
    stations = client.get("/api/v1/stations", headers={"Authorization": f"Bearer {token}"}).json()

    response = client.post(
        "/api/v1/predict",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "station_id": stations[0]["id"],
            "horizon_hours": 2,
            "weather_factor": 1.1,
            "event_factor": 1.15,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_count"] > 0
    assert payload["recommended_action"]


def test_admin_can_crud_flows(client: TestClient) -> None:
    admin_token = login(client, "admin@metroflow.ai", "admin12345")["access_token"]
    stations = client.get("/api/v1/stations", headers={"Authorization": f"Bearer {admin_token}"}).json()

    create_response = client.post(
        "/api/v1/admin/flows",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "station_id": stations[0]["id"],
            "timestamp": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "passenger_count": 420,
            "avg_dwell_minutes": 3.3,
            "weather_code": "rain",
            "event_flag": True,
            "event_name": "Concert dispersal",
            "source": "admin-upload",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()

    update_response = client.put(
        f"/api/v1/admin/flows/{created['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"passenger_count": 430},
    )
    assert update_response.status_code == 200
    assert update_response.json()["passenger_count"] == 430

    delete_response = client.delete(
        f"/api/v1/admin/flows/{created['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_response.status_code == 204


def test_train_requires_admin(client: TestClient) -> None:
    user_token = login(client, "user@metroflow.ai", "user12345")["access_token"]
    response = client.post(
        "/api/v1/train",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"epochs": 16, "learning_rate": 0.001, "lookback_steps": 24},
    )
    assert response.status_code == 403


def test_route_optimization_endpoint(client: TestClient) -> None:
    auth = login(client, "admin@metroflow.ai", "admin12345")
    token = auth["access_token"]
    stations = client.get("/api/v1/stations", headers={"Authorization": f"Bearer {token}"}).json()

    # Find two stations in Delhi to route between
    delhi_stations = [s for s in stations if s["city"] == "Delhi"]
    assert len(delhi_stations) >= 2

    response = client.post(
        "/api/v1/networks/route-optimize",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "origin_station_id": delhi_stations[0]["id"],
            "destination_station_id": delhi_stations[1]["id"],
            "avoid_congestion": True
        }
    )

    assert response.status_code == 200
    payload = response.json()
    assert "path" in payload
    assert payload["total_stations"] > 0
    assert "estimated_duration_minutes" in payload
    assert "congestion_index" in payload


def test_dispatch_and_od_matrix_endpoints(client: TestClient) -> None:
    auth = login(client, "admin@metroflow.ai", "admin12345")
    token = auth["access_token"]

    dispatch_res = client.get("/api/v1/dispatch/recommendations?city=Delhi", headers={"Authorization": f"Bearer {token}"})
    assert dispatch_res.status_code == 200
    dispatch_data = dispatch_res.json()
    assert dispatch_data["city"] == "Delhi"
    assert "line_recommendations" in dispatch_data
    assert len(dispatch_data["line_recommendations"]) > 0

    matrix_res = client.get("/api/v1/networks/od-matrix?city=Delhi", headers={"Authorization": f"Bearer {token}"})
    assert matrix_res.status_code == 200
    matrix_data = matrix_res.json()
    assert matrix_data["city"] == "Delhi"
    assert "matrix" in matrix_data
    assert len(matrix_data["matrix"]) > 0


def test_data_sources_live_status(client: TestClient) -> None:
    res = client.get("/api/v1/data-sources/status")
    assert res.status_code == 200
    data = res.json()
    assert "feeds" in data
    assert len(data["feeds"]) >= 3
    # Verify feed provenance labeling
    provenances = {feed["data_source"] for feed in data["feeds"]}
    assert "REALTIME" in provenances
    assert "SIMULATED" in provenances

    weather_res = client.get("/api/v1/data-sources/weather?city=Delhi&lat=28.6304&lon=77.2177")
    assert weather_res.status_code == 200
    w_data = weather_res.json()
    assert "temperature_celsius" in w_data
    assert w_data["data_source"] in {"REALTIME", "SIMULATED"}


def test_metro_hierarchy_and_planned_filtering(client: TestClient) -> None:
    # 1. Test National Hierarchy
    res = client.get("/api/v1/networks/hierarchy")
    assert res.status_code == 200
    hierarchy = res.json()
    assert hierarchy["country"] == "India"
    assert hierarchy["total_metro_systems"] >= 14
    assert hierarchy["operational_stations"] > 0
    assert len(hierarchy["systems"]) >= 14
    assert len(hierarchy["cities"]) >= 10

    # 2. Test Systems endpoint
    sys_res = client.get("/api/v1/networks/systems")
    assert sys_res.status_code == 200
    systems = sys_res.json()
    sys_codes = {s["code"] for s in systems}
    assert "DMRC" in sys_codes
    assert "BMRCL" in sys_codes
    assert "MMRDA" in sys_codes
    assert "CMRL" in sys_codes
    assert "LT_HYD" in sys_codes

    # 3. Test Lines endpoint for DMRC
    lines_res = client.get("/api/v1/networks/systems/DMRC/lines")
    assert lines_res.status_code == 200
    lines = lines_res.json()
    line_names = {l["name"] for l in lines}
    assert "Red Line" in line_names
    assert "Yellow Line" in line_names

    # 4. Test Planned Station Rejection in Route Optimization
    stations = client.get("/api/v1/stations").json()
    # Find Mumbai CSMT (under construction)
    csmt = next((s for s in stations if s["code"] == "MUM_CST"), None)
    andheri = next((s for s in stations if s["code"] == "MUM_AND"), None)
    if csmt and andheri:
        # Route should be rejected when planned lines excluded
        rej_res = client.post(
            "/api/v1/networks/route-optimize",
            json={
                "origin_station_id": csmt["id"],
                "destination_station_id": andheri["id"],
                "avoid_congestion": False,
                "include_planned_lines": False,
            }
        )
        assert rej_res.status_code == 400
        assert "planned" in rej_res.json()["detail"].lower()


def test_od_pipeline_and_programmatic_ingestion(client: TestClient) -> None:
    # 1. Test CSV/Sample Upload with configurable interval (10m)
    upload_res = client.post("/api/v1/upload?time_interval=10m&city=Delhi")
    assert upload_res.status_code == 200
    up_data = upload_res.json()
    assert up_data["status"] == "success"
    assert up_data["time_interval"] == "10m"
    assert "quality_metrics" in up_data
    assert "matrix_dense" in up_data
    assert up_data["quality_metrics"]["retaps_within_30s_removed"] >= 1
    assert up_data["quality_metrics"]["short_duration_under_2m_removed"] >= 1

    # 2. Test Programmatic API Ingestion
    ingest_payload = {
        "city": "Delhi",
        "time_interval": "5m",
        "impute_missing_tapout": True,
        "records": [
            {
                "card_id": "TEST_CARD_999",
                "tap_in_time": "2026-08-01 09:00:00",
                "origin_station": "DEL_RAJ",
                "tap_out_time": "2026-08-01 09:22:00",
                "destination_station": "DEL_KAS"
            },
            # Rapid re-tap within 15 seconds (should be filtered out)
            {
                "card_id": "TEST_CARD_999",
                "tap_in_time": "2026-08-01 09:00:15",
                "origin_station": "DEL_RAJ",
                "tap_out_time": "2026-08-01 09:22:00",
                "destination_station": "DEL_KAS"
            },
            # Missing tap-out (should be imputed with +20m)
            {
                "card_id": "TEST_CARD_888",
                "tap_in_time": "2026-08-01 09:05:00",
                "origin_station": "DEL_NOI",
                "tap_out_time": None,
                "destination_station": "DEL_RAJ"
            }
        ]
    }
    ingest_res = client.post("/api/v1/od-matrix/ingest", json=ingest_payload)
    assert ingest_res.status_code == 200
    ing_data = ingest_res.json()
    assert ing_data["status"] == "success"
    assert ing_data["time_interval"] == "5m"
    metrics = ing_data["quality_metrics"]
    assert metrics["retaps_within_30s_removed"] == 1
    assert metrics["missing_tapout_imputed"] == 1
    assert metrics["valid_journeys_aggregated"] == 2

    # 3. Test Dense Format Retrieval
    dense_res = client.get("/api/v1/od-matrix?city=Delhi&output_format=dense")
    assert dense_res.status_code == 200
    dense_data = dense_res.json()
    assert dense_data["format"] == "dense"
    assert "matrix_dense" in dense_data
    assert "stations" in dense_data["matrix_dense"]
    assert "matrix" in dense_data["matrix_dense"]


def test_ml_benchmarks_and_metrics_slices(client: TestClient) -> None:
    res = client.get("/api/v1/benchmarks?city=Delhi")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "Historical_Average" in data["metrics"]
    assert "Ridge_Regression" in data["metrics"]
    assert "Random_Forest" in data["metrics"]
    assert "MetroFlowNet_AFFN" in data["metrics"]

    # Verify metrics structure
    for model_name, m in data["metrics"].items():
        assert "mae" in m
        assert "rmse" in m
        assert "mape" in m
        assert "wape" in m
        assert "r2" in m

    # Verify AFFN superiority over baselines
    affn = data["metrics"]["MetroFlowNet_AFFN"]
    ha = data["metrics"]["Historical_Average"]
    assert affn["mae"] < ha["mae"]
    assert affn["rmse"] < ha["rmse"]

    # Verify slices
    assert "slices" in data
    assert data["best_model"] == "MetroFlowNet_AFFN"


def test_cumulative_segment_loads_and_journey_advisory(client: TestClient) -> None:
    # 1. Test Cumulative Segment Loads
    seg_res = client.get("/api/v1/routes/segment-loads?city=Delhi")
    assert seg_res.status_code == 200
    seg_data = seg_res.json()
    assert seg_data["total_segments_analyzed"] > 0
    assert "segments" in seg_data
    assert "actionable_intelligence" in seg_data
    assert "headway_adjustment" in seg_data["actionable_intelligence"]
    assert "platform_crowd_control" in seg_data["actionable_intelligence"]

    for s in seg_data["segments"]:
        assert s["status"] in {"NORMAL", "WARNING", "CRITICAL"}
        assert s["load_factor"] >= 0.0
        assert "recommended_action" in s

    # 2. Test Smart Journey Advisory
    adv_res = client.get("/api/v1/routes/advisory?origin=Rajiv Chowk&destination=Noida Sector 62")
    assert adv_res.status_code == 200
    adv_data = adv_res.json()
    assert "next_train_predicted_fullness_pct" in adv_data
    assert "smart_crowd_advisory" in adv_data
    assert "recommended_boarding_coach" in adv_data
    assert "least_crowded_route" in adv_data
    assert "disclaimer" in adv_data


