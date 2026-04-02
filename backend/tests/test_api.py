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
