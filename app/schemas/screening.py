from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.db.models.screening import EyeEnum, ScreeningStatusEnum

class ScreeningCreate(BaseModel):
    patient_id: str
    eye: EyeEnum = EyeEnum.RIGHT
    screening_center_id: Optional[str] = None
    local_id: Optional[str] = None

class ScreeningResponse(BaseModel):
    id: str
    screening_id: str
    local_id: Optional[str] = None
    patient_id: str
    eye: EyeEnum
    screening_center_id: Optional[str] = None
    health_worker_id: Optional[str] = None
    image_id: Optional[str] = None
    status: ScreeningStatusEnum
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ImageQualityResponse(BaseModel):
    status: str
    retina_visibility: str
    sharpness: str
    illumination: str
    field_of_view: str
    usable: bool
    messages: List[str]
