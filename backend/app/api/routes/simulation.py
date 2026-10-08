from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from datetime import UTC, timedelta
import random
from app.api.deps import get_optional_user, get_db
from app.services.documents import utc_now

router = APIRouter(tags=["simulation"])


@router.post("/run")
def run_simulation(
    payload: dict,
    db: Database = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user)
) -> dict:
    city = payload.get("city", "Delhi")
    scenario = payload.get("scenario", "normal")
    rate = payload.get("passenger_rate", 1.0)
    train_speed_mult = payload.get("train_speed", 1.0)
    
    stations = list(db.stations.find({"city": city}))
    if not stations:
        raise HTTPException(status_code=404, detail=f"No stations found in city {city} to simulate.")
        
    trains = list(db.trains.find({"city": city}))
    
    # Calculate simulation step details
    # Returns simulated platform queues, escalator densities, and train offsets
    simulated_stations = []
    for index, st in enumerate(stations):
        # Platform queue logic
        base_queue = int(st["baseline_capacity"] * 0.12 * rate)
        if scenario == "festival":
            base_queue = int(base_queue * 1.5)
        elif scenario == "monsoon":
            base_queue = int(base_queue * 1.3)
        elif scenario == "evacuation":
            base_queue = int(base_queue * 2.2)
            
        escalator_load = min(98, int(30 * rate + (10 if scenario in {"festival", "monsoon"} else 0) + (45 if scenario == "evacuation" else 0)))
        platform_density = min(99, int(25 * rate + (15 if scenario == "festival" else 0) + (55 if scenario == "evacuation" else 0)))
        
        # Determine safety index
        safety_status = "safe"
        if scenario == "evacuation":
            safety_status = "evacuating"
        elif platform_density > 80:
            safety_status = "overcrowded"
            
        # Exit vectors (for emergency evacuation paths)
        exit_vectors = []
        if scenario == "evacuation":
            exit_vectors = [
                {"exit_name": "Gate A", "vector_x": -0.8, "vector_y": 0.5, "flow_rate": 45},
                {"exit_name": "Gate B", "vector_x": 0.9, "vector_y": -0.2, "flow_rate": 35}
            ]
            
        simulated_stations.append({
            "station_code": st["code"],
            "station_name": st["name"],
            "line": st["line"],
            "queue_length": base_queue + random.randint(-5, 5),
            "escalator_load_pct": escalator_load,
            "platform_density_pct": platform_density,
            "safety_status": safety_status,
            "exit_vectors": exit_vectors
        })
        
    # Simulate train movements
    simulated_trains = []
    for index, tr in enumerate(trains):
        # Move trains incrementally
        speed = tr.get("speed_kmh", 40) * train_speed_mult
        status = "normal"
        if scenario == "monsoon":
            speed = speed * 0.75
            status = "delayed"
        elif scenario == "evacuation":
            status = "evacuation_mode"
            speed = 0  # Stop trains at station during evacuation
            
        simulated_trains.append({
            "code": tr["code"],
            "name": tr["name"],
            "line": tr["line"],
            "capacity": tr["capacity"],
            "speed_kmh": round(speed, 1),
            "status": status,
            "current_station": tr["current_station_code"],
            "occupancy_pct": min(95, int(50 * rate + (25 if scenario == "festival" else -15 if scenario == "evacuation" else 0)))
        })
        
    return {
        "city": city,
        "scenario": scenario,
        "timestamp": utc_now(),
        "stations": simulated_stations,
        "trains": simulated_trains,
        "is_active": True,
        "message": f"Simulation running under scenario: {scenario.upper()}"
    }
