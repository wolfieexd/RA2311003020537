import time
from fastapi import Request
from logging_middleware.logger import Log

async def log_requests(request: Request, call_next):
    start = time.time()
    Log("backend", "info", "middleware", f"Incoming {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)
        Log("backend", "info", "middleware", f"Completed {request.method} {request.url.path} status={response.status_code} duration={duration_ms}ms")
        return response
    except Exception as e:
        Log("backend", "error", "handler", f"Unhandled error on {request.url.path}: {str(e)}")
        raise
