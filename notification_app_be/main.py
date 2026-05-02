from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from logging_middleware.middleware import log_requests
from auth.token_manager import token_manager
from notification_app_be.api_client import fetch_notifications
from notification_app_be.priority_inbox import fetch_priority_inbox
from logging_middleware.logger import Log

app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

@app.on_event("startup")
async def startup():
    await token_manager.authenticate()

@app.get("/notifications")
async def get_notifications(type: Optional[str] = Query(None)):
    Log("backend", "info", "route", f"Fetching notifications (type filter: {type})")
    try:
        notifications = await fetch_notifications()
    except Exception as e:
        Log("backend", "error", "handler", f"Failed to fetch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching data from server")
        
    if type:
        notifications = [n for n in notifications if n["Type"] == type]
        
    return {"notifications": notifications}

@app.get("/notifications/unread/count")
async def get_unread_count():
    Log("backend", "info", "route", "Fetching unread notification count")
    try:
        notifications = await fetch_notifications()
    except Exception as e:
        Log("backend", "error", "handler", f"Failed to fetch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching data from server")
        
    # Assuming all fetched from this endpoint are unread or we count all for this mockup
    return {"unreadCount": len(notifications)}

@app.get("/notifications/priority")
async def get_priority_inbox(n: int = Query(10)):
    Log("backend", "info", "route", f"Fetching priority inbox (n={n})")
    try:
        return await fetch_priority_inbox(n)
    except Exception as e:
        Log("backend", "error", "handler", f"Failed to fetch priority inbox: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating priority inbox")

@app.get("/notifications/{id}")
async def get_notification(id: str):
    Log("backend", "info", "route", f"Fetching notification {id}")
    try:
        notifications = await fetch_notifications()
    except Exception as e:
        Log("backend", "error", "handler", f"Failed to fetch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching data from server")
        
    notif = next((n for n in notifications if n["ID"] == id), None)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    return notif

@app.patch("/notifications/{id}/read")
async def mark_as_read(id: str):
    Log("backend", "info", "handler", f"Marking notification {id} as read")
    # Mock behavior since we can't persist to the read-only test server
    return {"id": id, "isRead": True}

@app.patch("/notifications/read-all")
async def mark_all_as_read():
    Log("backend", "info", "handler", "Marking all notifications as read")
    try:
        notifications = await fetch_notifications()
    except Exception as e:
        Log("backend", "error", "handler", f"Failed to fetch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching data from server")
        
    return {"updatedCount": len(notifications), "message": "All notifications marked as read"}
