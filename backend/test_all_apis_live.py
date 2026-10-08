import json
import sys
import time
from datetime import UTC, datetime, timedelta
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

results = []

def request(method: str, path: str, body=None, token=None, content_type="application/json", timeout: int = 15):
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(body, bytes):
            data = body
            headers["Content-Type"] = content_type
        elif isinstance(body, str):
            data = body.encode("utf-8")
            headers["Content-Type"] = content_type
            
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            resp_body = resp.read().decode("utf-8")
            try:
                json_data = json.loads(resp_body)
            except Exception:
                json_data = resp_body
            return {
                "status_code": resp.status,
                "elapsed_ms": round(elapsed_ms, 2),
                "data": json_data,
                "error": None
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        resp_body = e.read().decode("utf-8")
        try:
            json_data = json.loads(resp_body)
        except Exception:
            json_data = resp_body
        return {
            "status_code": e.code,
            "elapsed_ms": round(elapsed_ms, 2),
            "data": json_data,
            "error": str(e)
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status_code": 0,
            "elapsed_ms": round(elapsed_ms, 2),
            "data": None,
            "error": str(e)
        }

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def log_test(category, endpoint, method, expected_status, res, details=""):
    passed = (res["status_code"] == expected_status)
    status_icon = "[PASS]" if passed else "[FAIL]"
    results.append({
        "category": category,
        "endpoint": endpoint,
        "method": method,
        "expected": expected_status,
        "actual": res["status_code"],
        "elapsed_ms": res["elapsed_ms"],
        "passed": passed,
        "details": details or (res["error"] if not passed else "OK")
    })
    print(f"{status_icon} {method:6} {endpoint:<45} | Code: {res['status_code']} ({res['elapsed_ms']}ms) {details}")

print(f"\n=======================================================")
print(f"  MetroFlow OD Passenger Flow Predictor - Live API Test")
print(f"  Target: {BASE_URL}")
print(f"=======================================================\n")

# 1. Health & Root Endpoints
print("--- 1. Health & Root Endpoints ---")
r = request("GET", "/health")
log_test("System", "/health", "GET", 200, r, f"Service: {r['data'].get('service') if isinstance(r['data'], dict) else ''}")

r = request("GET", "/")
log_test("System", "/", "GET", 200, r, f"Status: {r['data'].get('status') if isinstance(r['data'], dict) else ''}")

r = request("GET", "/api/v1/")
log_test("System", "/api/v1/", "GET", 200, r, f"Status: {r['data'].get('status') if isinstance(r['data'], dict) else ''}")

# 2. Authentication & Profile
print("\n--- 2. Authentication & Profile ---")
unique_suffix = int(time.time())
reg_email = f"test.user.{unique_suffix}@metroflow.ai"
r = request("POST", "/api/v1/auth/register", body={
    "email": reg_email,
    "full_name": "Test User Live",
    "password": "Password123!",
    "job_title": "Traffic Engineer",
    "organization": "DMRC",
    "commute_line": "Yellow Line"
})
log_test("Auth", "/api/v1/auth/register", "POST", 201, r, f"User created: {reg_email}")

# Login with created user
r = request("POST", "/api/v1/auth/login", body={"email": reg_email, "password": "Password123!"})
log_test("Auth", "/api/v1/auth/login (User)", "POST", 200, r)
user_token = r["data"].get("access_token") if isinstance(r["data"], dict) else None

# Login with admin user
r = request("POST", "/api/v1/auth/login", body={"email": "admin@metroflow.ai", "password": "admin12345"})
log_test("Auth", "/api/v1/auth/login (Admin)", "POST", 200, r)
admin_token = r["data"].get("access_token") if isinstance(r["data"], dict) else None

# User Profile GET & PUT
r = request("GET", "/api/v1/auth/me", token=user_token)
log_test("Auth", "/api/v1/auth/me", "GET", 200, r, f"Email: {r['data'].get('email') if isinstance(r['data'], dict) else ''}")

r = request("GET", "/api/v1/profile", token=user_token)
log_test("Profile", "/api/v1/profile", "GET", 200, r)

r = request("PUT", "/api/v1/profile", body={"theme_preference": "dark", "job_title": "Principal Engineer"}, token=user_token)
log_test("Profile", "/api/v1/profile", "PUT", 200, r, f"Updated Theme: {r['data'].get('user', {}).get('theme_preference') if isinstance(r['data'], dict) else ''}")

# 3. Stations & Network
print("\n--- 3. Stations & Networks ---")
r = request("GET", "/api/v1/stations", token=user_token)
stations_list = r["data"] if isinstance(r["data"], list) else []
log_test("Stations", "/api/v1/stations", "GET", 200, r, f"Count: {len(stations_list)} stations")

r = request("GET", "/api/v1/stations?city=Delhi", token=user_token)
delhi_stations = r["data"] if isinstance(r["data"], list) else []
log_test("Stations", "/api/v1/stations?city=Delhi", "GET", 200, r, f"Delhi Stations: {len(delhi_stations)}")

r = request("GET", "/api/v1/networks/overview", token=user_token)
log_test("Networks", "/api/v1/networks/overview", "GET", 200, r, f"Cities: {r['data'].get('total_cities') if isinstance(r['data'], dict) else ''}, Trains: {r['data'].get('total_trains') if isinstance(r['data'], dict) else ''}")

r = request("GET", "/api/v1/networks/city/Delhi", token=user_token)
log_test("Networks", "/api/v1/networks/city/Delhi", "GET", 200, r, f"Stations in Delhi Network: {len(r['data'].get('stations', [])) if isinstance(r['data'], dict) else 0}")

r = request("GET", "/api/v1/networks/od-matrix?city=Delhi", token=user_token)
log_test("Networks", "/api/v1/networks/od-matrix?city=Delhi", "GET", 200, r, f"Top Pairs: {len(r['data'].get('top_pairs', [])) if isinstance(r['data'], dict) else 0}")

# Route Optimization
if len(delhi_stations) >= 2:
    st_orig = delhi_stations[0]["id"]
    st_dest = delhi_stations[1]["id"]
    r = request("POST", "/api/v1/networks/route-optimize", body={
        "origin_station_id": st_orig,
        "destination_station_id": st_dest,
        "avoid_congestion": True
    }, token=user_token, timeout=30)
    log_test("Networks", "/api/v1/networks/route-optimize", "POST", 200, r, f"Est. Duration: {r['data'].get('estimated_duration_minutes') if isinstance(r['data'], dict) else ''} mins")

# 4. Dashboard & Analytics
print("\n--- 4. Dashboard & Analytics ---")
r = request("GET", "/api/v1/dashboard/overview", token=user_token)
log_test("Dashboard", "/api/v1/dashboard/overview", "GET", 200, r, f"KPIs: {len(r['data'].get('kpis', [])) if isinstance(r['data'], dict) else 0}")

sample_st_id = stations_list[0]["id"] if stations_list else ""
r = request("GET", f"/api/v1/dashboard/overview?station_id={sample_st_id}", token=user_token)
log_test("Dashboard", f"/api/v1/dashboard/overview?station_id=...", "GET", 200, r)

r = request("GET", f"/api/v1/historical/analytics?station_id={sample_st_id}&days=7", token=user_token)
log_test("Historical", "/api/v1/historical/analytics", "GET", 200, r, f"Daily Totals: {len(r['data'].get('daily_totals', [])) if isinstance(r['data'], dict) else 0}")

r = request("GET", f"/api/v1/analytics?station_id={sample_st_id}&days=14", token=user_token)
log_test("Historical", "/api/v1/analytics (alias)", "GET", 200, r)

# 5. Predict & Train
print("\n--- 5. Prediction & Training ---")
r = request("POST", "/api/v1/predict", body={
    "station_id": sample_st_id,
    "horizon_hours": 2,
    "weather_factor": 1.1,
    "event_factor": 1.2
}, token=user_token)
log_test("Predict", "/api/v1/predict", "POST", 200, r, f"Predicted Flow: {r['data'].get('predicted_count') if isinstance(r['data'], dict) else ''}")

# Retrain Model (Requires admin)
r = request("POST", "/api/v1/train", body={"epochs": 8, "learning_rate": 0.001, "lookback_steps": 24}, token=admin_token, timeout=120)
log_test("Predict", "/api/v1/train (Admin)", "POST", 200, r, f"Metrics: {r['data'].get('metrics') if isinstance(r['data'], dict) else ''}")

# 6. OD Matrix & Route Navigation
print("\n--- 6. OD Matrix & Navigation ---")
r = request("GET", "/api/v1/od-matrix?city=Delhi", token=user_token)
log_test("OD Matrix", "/api/v1/od-matrix?city=Delhi", "GET", 200, r, f"Total pairs: {r['data'].get('total_pairs') or len(r['data'].get('matrix', [])) if isinstance(r['data'], dict) else 0}")

r = request("GET", "/api/v1/routes?origin=Rajiv%20Chowk&destination=Noida%20Sector%2062")
log_test("Routes", "/api/v1/routes", "GET", 200, r, f"Best route time: {r['data'].get('best_route', {}).get('estimated_time_mins') if isinstance(r['data'], dict) else 0} mins")

# 7. Smart Card Tap Log Upload Pipeline
print("\n--- 7. Smart Card Tap Log Upload Pipeline ---")
r = request("POST", "/api/v1/upload?time_interval=15m")
log_test("Upload Pipeline", "/api/v1/upload (Sample Execution)", "POST", 200, r, f"Processed records: {r['data'].get('record_count') if isinstance(r['data'], dict) else 0}")

# 8. GTFS Pipeline
print("\n--- 8. GTFS Transit Pipeline ---")
r = request("POST", "/api/v1/gtfs/sample-ingest?city=Delhi", token=admin_token)
log_test("GTFS", "/api/v1/gtfs/sample-ingest", "POST", 200, r)

r = request("GET", "/api/v1/gtfs/feeds?city=Delhi", token=user_token)
log_test("GTFS", "/api/v1/gtfs/feeds?city=Delhi", "GET", 200, r, f"Feed count: {len(r['data']) if isinstance(r['data'], list) else 0}")

r = request("GET", "/api/v1/gtfs/graph?city=Delhi", token=user_token)
log_test("GTFS", "/api/v1/gtfs/graph?city=Delhi", "GET", 200, r, f"Nodes: {r['data'].get('total_nodes') if isinstance(r['data'], dict) else 0}, Edges: {r['data'].get('total_edges') if isinstance(r['data'], dict) else 0}")

# 9. Simulation Engine
print("\n--- 9. Real-time Simulation Engine ---")
r = request("POST", "/api/v1/simulation/run", body={
    "city": "Delhi",
    "scenario": "festival",
    "passenger_rate": 1.2,
    "train_speed": 1.0
}, token=user_token)
log_test("Simulation", "/api/v1/simulation/run (festival)", "POST", 200, r, f"Simulated Stations: {len(r['data'].get('stations', [])) if isinstance(r['data'], dict) else 0}")

r = request("POST", "/api/v1/simulation/run", body={
    "city": "Delhi",
    "scenario": "evacuation",
    "passenger_rate": 2.0,
    "train_speed": 0.0
}, token=user_token)
log_test("Simulation", "/api/v1/simulation/run (evacuation)", "POST", 200, r, f"Simulated Trains: {len(r['data'].get('trains', [])) if isinstance(r['data'], dict) else 0}")

# 10. Dispatch Recommendations
print("\n--- 10. AI Dispatch & Headway Recommendations ---")
r = request("GET", "/api/v1/dispatch/recommendations?city=Delhi", token=user_token)
log_test("Dispatch", "/api/v1/dispatch/recommendations", "GET", 200, r, f"Extra trains needed: {r['data'].get('total_extra_train_sets_needed') if isinstance(r['data'], dict) else 0}")

# 11. Admin Flow Management CRUD
print("\n--- 11. Admin Flow Management CRUD ---")
r = request("GET", "/api/v1/admin/flows", token=admin_token)
log_test("Admin CRUD", "/api/v1/admin/flows (List)", "GET", 200, r, f"Retrieved: {len(r['data']) if isinstance(r['data'], list) else 0}")

r = request("POST", "/api/v1/admin/flows", body={
    "station_id": sample_st_id,
    "timestamp": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
    "passenger_count": 550,
    "avg_dwell_minutes": 3.1,
    "weather_code": "clear",
    "event_flag": False,
    "source": "live-api-test"
}, token=admin_token)
log_test("Admin CRUD", "/api/v1/admin/flows (Create)", "POST", 201, r)
created_flow_id = r["data"].get("id") if isinstance(r["data"], dict) else None

if created_flow_id:
    r = request("PUT", f"/api/v1/admin/flows/{created_flow_id}", body={
        "passenger_count": 575,
        "avg_dwell_minutes": 3.4
    }, token=admin_token)
    log_test("Admin CRUD", f"/api/v1/admin/flows/{{id}} (Update)", "PUT", 200, r, f"New count: {r['data'].get('passenger_count') if isinstance(r['data'], dict) else ''}")

    r = request("DELETE", f"/api/v1/admin/flows/{created_flow_id}", token=admin_token)
    log_test("Admin CRUD", f"/api/v1/admin/flows/{{id}} (Delete)", "DELETE", 204, r)

# Summary
print("\n=======================================================")
passed_count = sum(1 for res in results if res["passed"])
failed_count = sum(1 for res in results if not res["passed"])
total_count = len(results)
print(f"Total API Endpoints Tested: {total_count}")
print(f"Passed: {passed_count}/{total_count} ({(passed_count/total_count)*100:.1f}%)")
print(f"Failed: {failed_count}/{total_count}")
print(f"=======================================================\n")

if failed_count > 0:
    sys.exit(1)
else:
    sys.exit(0)
