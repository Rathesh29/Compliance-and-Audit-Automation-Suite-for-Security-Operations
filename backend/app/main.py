import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging_config import logger
from app.database.session import engine, Base
from app.api.api import api_router
from app.services.websocket_manager import ws_manager
from app.services.scheduler_service import run_missed_shift_scheduler_loop
from app.middleware.audit_middleware import AuditLoggingMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is created
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    # Start background scheduler for automated missed-shift detection
    scheduler_task = asyncio.create_task(
        run_missed_shift_scheduler_loop(interval_seconds=settings.MISSED_SHIFT_CHECK_INTERVAL_SECONDS)
    )
    logger.info("Automatic missed-shift scheduler task started.")

    yield

    # Clean shutdown
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Compliance and Audit Automation Suite for Security Operations REST API. "
                "Provides tamper-evident audit logging, geofenced GPS validation, QR verification, "
                "automated shift exception detection, and enterprise reporting.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares
app.add_middleware(AuditLoggingMiddleware)

# Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_PREFIX)


# Real-time WebSockets
@app.websocket("/ws/compliance")
async def websocket_compliance_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket compliance error: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/notifications")
async def websocket_notifications_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket notification error: {e}")
        ws_manager.disconnect(websocket)


@app.get("/")
def root_index():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api": "/api"
    }
