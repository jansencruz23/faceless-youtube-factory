"""Main API v1 router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.v1.projects import router as projects_router
from app.api.v1.casting import router as casting_router
from app.api.v1.youtube import router as youtube_router
from app.api.v1.health import router as health_router
from app.api.v1.websocket import router as websocket_router
from app.api.v1.scheduler import router as scheduler_router
from app.api.v1.automation import router as automation_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(casting_router, tags=["Casting"])
api_router.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
api_router.include_router(websocket_router, tags=["WebSocket"])
api_router.include_router(scheduler_router, prefix="/scheduler", tags=["Scheduler"])
api_router.include_router(automation_router, prefix="/automation", tags=["Automation"])
