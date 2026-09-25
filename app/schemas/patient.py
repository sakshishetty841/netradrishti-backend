from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.db.models.patient import DiabetesTypeEnum, TreatmentEnum

class DiabetesProfileSchema(BaseModel):
    diabetes_type: Optional[DiabetesTypeEnum] = DiabetesTypeEnum.UNKNOWN
    diabetes_duration_years: Optional[float] = None
    treatment: Optional[TreatmentEnum] = TreatmentEnum.UNKNOWN
    previous_diabetic_retinopathy: Optional[bool] = False
    previous_eye_treatment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ClinicalParametersSchema(BaseModel):
    fasting_glucose: Optional[float] = None
    post_meal_glucose: Optional[float] = None
    hba1c: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    previous_eye_disease: Optional[str] = None
    smoking_status: Optional[str] = None
    previous_dr_history: Optional[bool] = False
    previous_ophthalmology_visit: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    mobile_optional: Optional[str] = None
    village: Optional[str] = None
    screening_center_id: Optional[str] = None
    address_note: Optional[str] = None
    diabetes_profile: Optional[DiabetesProfileSchema] = None
    clinical_parameters: Optional[ClinicalParametersSchema] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    mobile_optional: Optional[str] = None
    village: Optional[str] = None
    screening_center_id: Optional[str] = None
    address_note: Optional[str] = None
    diabetes_profile: Optional[DiabetesProfileSchema] = None
    clinical_parameters: Optional[ClinicalParametersSchema] = None

class PatientResponse(BaseModel):
    id: str
    patient_id: str
    name: str
    age: int
    gender: str
    mobile_optional: Optional[str] = None
    village: Optional[str] = None
    screening_center_id: Optional[str] = None
    address_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    diabetes_profile: Optional[DiabetesProfileSchema] = None
    clinical_parameters: Optional[ClinicalParametersSchema] = None

    model_config = ConfigDict(from_attributes=True)

class PatientJourneyStage(BaseModel):
    stage: str
    status: str
    date: Optional[str] = None
    grade: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PatientJourneyResponse(BaseModel):
    patient_id: str
    stages: List[PatientJourneyStage]
