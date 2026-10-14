from fastapi import APIRouter
from app.api.routes import (
    auth,
    users,
    sites,
    shifts,
    assignments,
    attendance,
    audit,
    dashboard,
    notifications,
    reports,
    health
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sites.router)
api_router.include_router(shifts.router)
api_router.include_router(assignments.router)
api_router.include_router(attendance.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
