import httpx
from logging_middleware.logger import Log
from auth.token_manager import token_manager

async def fetch_depots():
    headers = token_manager.get_headers()
    Log("backend", "debug", "repository", "Fetching depots from test server")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://20.207.122.201/evaluation-service/depots",
            headers=headers
        )
        if response.status_code != 200:
            Log("backend", "error", "repository", f"Depots API failed: {response.status_code}")
            raise Exception("Failed to fetch depots")
        return response.json().get("depots", [])

async def fetch_vehicles():
    headers = token_manager.get_headers()
    Log("backend", "debug", "repository", "Fetching vehicles from test server")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://20.207.122.201/evaluation-service/vehicles",
            headers=headers
        )
        if response.status_code != 200:
            Log("backend", "error", "repository", f"Vehicles API failed: {response.status_code}")
            raise Exception("Failed to fetch vehicles")
        return response.json().get("vehicles", [])
