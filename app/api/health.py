from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.storage.local_storage import storage_service

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Liveness probe")
def health_check():
    return {"status": "ok", "service": "NetraDrishti Backend API"}

@router.get("/health/ready", summary="Readiness probe")
def readiness_check(db: Session = Depends(get_db)):
    # Check Database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False
        
    # Check Storage connectivity
    try:
        storage_path = storage_service.base_dir
        storage_ok = storage_path is not None
    except Exception:
        storage_ok = False
        
    if db_ok and storage_ok:
        return {
            "status": "ready",
            "database": "connected",
            "storage": "writable"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": db_ok, "storage": storage_ok}
        )
