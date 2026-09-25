from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class DashboardAnalyticsResponse(BaseModel):
    total_screenings: int
    normal_cases: int
    referred_cases: int
    high_priority_cases: int
    pending_reviews: int
    observed_screening_findings: Dict[str, int]
    daily_trends: List[Dict[str, Any]]
    screening_centre_stats: List[Dict[str, Any]]

class AreaAnalyticsResponse(BaseModel):
    area_level: str # state, district, block, village
    area_name: Optional[str] = None
    aggregated_counts: Dict[str, Any]
