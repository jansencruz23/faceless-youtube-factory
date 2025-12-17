"""Health check endpoint."""
from fastapi import APIRouter

from app.database import check_db_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns 200 if all systems operational.
    """
    db_ok = await check_db_connection()

     return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": "1.0.0"
    }