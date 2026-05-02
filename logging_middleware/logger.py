import httpx

_token: str = None
_log_url = "http://20.207.122.201/evaluation-service/logs"

def set_token(token: str):
    """Call this after authentication to set the Bearer token."""
    global _token
    _token = token

def Log(stack: str, level: str, package: str, message: str):
    """Synchronously POST log to test server."""
    if not _token:
        return  # Token not set yet (during startup)
    payload = {
        "stack": stack.lower(),
        "level": level.lower(),
        "package": package.lower(),
        "message": message
    }
    try:
        with httpx.Client() as client:
            client.post(
                _log_url,
                json=payload,
                headers={"Authorization": f"Bearer {_token}"}
            )
    except Exception:
        pass  # Silently fail — never crash app due to logging
