from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.db.models.referral import PriorityEnum, ReferralStatusEnum

class ReferralCreate(BaseModel):
    screening_id: str
    patient_id: str
    destination_facility: Optional[str] = None
    destination_doctor: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.ROUTINE
    reason: Optional[str] = None

class ReferralUpdate(BaseModel):
    priority: Optional[PriorityEnum] = None
    status: Optional[ReferralStatusEnum] = None
    destination_doctor: Optional[str] = None
    reason: Optional[str] = None

class ReferralResponse(BaseModel):
    id: str
    referral_id: str
    screening_id: str
    patient_id: str
    source_facility: Optional[str] = None
    destination_facility: Optional[str] = None
    destination_doctor: Optional[str] = None
    priority: PriorityEnum
    reason: Optional[str] = None
    status: ReferralStatusEnum
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
