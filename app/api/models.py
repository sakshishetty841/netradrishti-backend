from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.core.config import settings
from app.core.permissions import require_roles

router = APIRouter(prefix="/admin/models", tags=["Admin Model Management"])

@router.get("", summary="Get active model metadata")
def get_model_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return {
        "model_name": settings.MODEL_NAME,
        "active_version": settings.MODEL_VERSION,
        "explainability_version": settings.EXPLAINABILITY_VERSION,
        "metrics_available": False,
        "message": "Clinical validation metrics have not been configured."
    }

@router.get("/{model_version}", summary="Get model performance metrics for specified version")
def get_model_version_performance(
    model_version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return {
        "model_version": model_version,
        "metrics_available": False,
        "message": "Clinical validation metrics have not been configured."
    }
