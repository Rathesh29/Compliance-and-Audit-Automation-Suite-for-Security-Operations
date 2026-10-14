import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.logging_config import logger


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method

        response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)

        # Do not log spammy polling or docs requests at warning level
        if not path.startswith("/static") and not path.endswith((".ico", ".png", ".jpg")):
            logger.info(
                f"{method} {path} -> {response.status_code} ({process_time_ms}ms)",
                extra={"props": {
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": process_time_ms,
                    "client": request.client.host if request.client else "unknown"
                }}
            )

        return response
