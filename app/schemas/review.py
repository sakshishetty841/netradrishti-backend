from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.db.models.review import DoctorDecisionEnum, SpecialistDecisionEnum

class DoctorReviewCreate(BaseModel):
    decision: DoctorDecisionEnum
    notes: Optional[str] = None

class DoctorReviewResponse(BaseModel):
    id: str
    review_id: str
    screening_id: str
    doctor_id: str
    decision: DoctorDecisionEnum
    notes: Optional[str] = None
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SpecialistReviewCreate(BaseModel):
    decision: SpecialistDecisionEnum
    notes: Optional[str] = None
    further_tests: Optional[str] = None

class SpecialistReviewResponse(BaseModel):
    id: str
    review_id: str
    referral_id: str
    doctor_id: str
    decision: SpecialistDecisionEnum
    notes: Optional[str] = None
    further_tests: Optional[str] = None
    consultation_status: str
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)
