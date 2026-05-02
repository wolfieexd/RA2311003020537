from fastapi import FastAPI, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from logging_middleware.middleware import log_requests
from auth.token_manager import token_manager
from vehicle_maintence_scheduler.api_client import fetch_depots, fetch_vehicles
from vehicle_maintence_scheduler.scheduler import knapsack
from logging_middleware.logger import Log

app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

@app.on_event("startup")
async def startup():
    await token_manager.authenticate()

@app.get("/schedule")
async def get_all_schedules():
    Log("backend", "info", "route", "Fetching schedule for all depots")
    try:
        depots = await fetch_depots()
        vehicles = await fetch_vehicles()
    except Exception as e:
        Log("backend", "error", "handler", f"Error fetching data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching data from server")

    schedule = []
    for depot in depots:
        result = knapsack(vehicles, depot["MechanicHours"])
        schedule.append({
            "depotId": depot["ID"],
            "mechanicHoursBudget": depot["MechanicHours"],
            "mechanicHoursUsed": result["hours_used"],
            "totalImpactScore": result["total_impact"],
            "vehiclesSelected": [
                {
                    "taskId": v["TaskID"],
                    "duration": v["Duration"],
                    "impact": v["Impact"]
                } for v in result["selected_vehicles"]
            ]
        })
        
    return {
        "schedule": schedule,
        "generatedAt": datetime.utcnow().isoformat()
    }

@app.get("/schedule/{depot_id}")
async def get_depot_schedule(depot_id: int):
    Log("backend", "info", "route", f"Fetching schedule for depot {depot_id}")
    try:
        depots = await fetch_depots()
        vehicles = await fetch_vehicles()
    except Exception as e:
        Log("backend", "error", "handler", f"Error fetching data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching data from server")

    depot = next((d for d in depots if d["ID"] == depot_id), None)
    if not depot:
        Log("backend", "error", "handler", f"Depot {depot_id} not found")
        raise HTTPException(status_code=404, detail="Depot not found")
        
    result = knapsack(vehicles, depot["MechanicHours"])
    return {
        "schedule": [
            {
                "depotId": depot["ID"],
                "mechanicHoursBudget": depot["MechanicHours"],
                "mechanicHoursUsed": result["hours_used"],
                "totalImpactScore": result["total_impact"],
                "vehiclesSelected": [
                    {
                        "taskId": v["TaskID"],
                        "duration": v["Duration"],
                        "impact": v["Impact"]
                    } for v in result["selected_vehicles"]
                ]
            }
        ],
        "generatedAt": datetime.utcnow().isoformat()
    }
