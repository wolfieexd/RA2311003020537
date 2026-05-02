import heapq
from datetime import datetime
from logging_middleware.logger import Log
from notification_app_be.api_client import fetch_notifications

TYPE_WEIGHT = {"Placement": 3, "Result": 2, "Event": 1}

def compute_priority_score(notification: dict) -> float:
    """Higher score = higher priority. Type is primary, recency is secondary."""
    type_score = TYPE_WEIGHT.get(notification["Type"], 0)
    ts = datetime.strptime(notification["Timestamp"], "%Y-%m-%d %H:%M:%S")
    recency_score = ts.timestamp() / 1e10  # Normalize to small float
    return type_score + recency_score

def get_top_n(notifications: list, n: int = 10) -> list:
    """
    Min-heap of size n to find top-n efficiently.
    Time: O(m log n) where m = total notifications
    Space: O(n)
    """
    Log("backend", "info", "service", f"Computing top-{n} priority inbox from {len(notifications)} notifications")
    heap = []

    for notif in notifications:
        score = compute_priority_score(notif)
        if len(heap) < n:
            heapq.heappush(heap, (score, notif["ID"], notif))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, notif["ID"], notif))

    result = [
        {**item[2], "priorityScore": round(item[0], 10)}
        for item in sorted(heap, key=lambda x: -x[0])
    ]
    Log("backend", "info", "service", f"Priority inbox ready: {len(result)} items")
    return result

async def fetch_priority_inbox(n: int = 10) -> dict:
    Log("backend", "debug", "service", "Fetching notifications for priority inbox")
    all_notifs = await fetch_notifications()
    
    top_n = get_top_n(all_notifs, n)
    return {
        "requested_top_n": n,
        "total_fetched": len(all_notifs),
        "priority_inbox": top_n
    }
