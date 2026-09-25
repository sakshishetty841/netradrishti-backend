from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.schemas.analytics import DashboardAnalyticsResponse, AreaAnalyticsResponse
from app.services.analytics_service import analytics_service
from app.core.permissions import require_roles

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])

@router.get("/dashboard", response_model=DashboardAnalyticsResponse, summary="Get main admin dashboard analytics")
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return analytics_service.get_dashboard_analytics(db)

@router.get("/analytics", response_model=DashboardAnalyticsResponse, summary="Get system-wide analytics summary")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return analytics_service.get_dashboard_analytics(db)

@router.get("/analytics/area", response_model=AreaAnalyticsResponse, summary="Get area-wise aggregated statistics")
def get_area_analytics(
    area_level: str = Query("district", pattern="^(state|district|block|village)$"),
    area_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return analytics_service.get_area_analytics(db, area_level=area_level, area_name=area_name)
