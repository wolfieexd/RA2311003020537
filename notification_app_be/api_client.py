import httpx
from logging_middleware.logger import Log
from auth.token_manager import token_manager

async def fetch_notifications():
    headers = token_manager.get_headers()
    Log("backend", "debug", "repository", "Fetching notifications from test server")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://20.207.122.201/evaluation-service/notifications",
            headers=headers
        )
        if response.status_code != 200:
            Log("backend", "error", "repository", f"Notifications API failed: {response.status_code}")
            raise Exception("Failed to fetch notifications")
        return response.json().get("notifications", [])
