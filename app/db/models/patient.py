import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class DiabetesTypeEnum(str, enum.Enum):
    TYPE_1 = "TYPE_1"
    TYPE_2 = "TYPE_2"
    GESTATIONAL = "GESTATIONAL"
    UNKNOWN = "UNKNOWN"

class TreatmentEnum(str, enum.Enum):
    INSULIN = "INSULIN"
    ORAL_MEDICATION = "ORAL_MEDICATION"
    BOTH = "BOTH"
    UNKNOWN = "UNKNOWN"

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, unique=True, index=True, nullable=False) # e.g. PAT-10001
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False) # Male, Female, Other
    mobile_optional = Column(String, nullable=True)
    village = Column(String, nullable=True, index=True)
    screening_center_id = Column(String, ForeignKey("screening_centers.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    address_note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    screening_center = relationship("ScreeningCenter", back_populates="patients")
    diabetes_profile = relationship("DiabetesProfile", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    clinical_parameters = relationship("ClinicalParameters", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    screenings = relationship("Screening", back_populates="patient")

class DiabetesProfile(Base):
    __tablename__ = "diabetes_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), unique=True, nullable=False)
    diabetes_type = Column(SQLEnum(DiabetesTypeEnum), default=DiabetesTypeEnum.UNKNOWN)
    diabetes_duration_years = Column(Float, nullable=True)
    treatment = Column(SQLEnum(TreatmentEnum), default=TreatmentEnum.UNKNOWN)
    previous_diabetic_retinopathy = Column(Boolean, default=False)
    previous_eye_treatment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="diabetes_profile")

class ClinicalParameters(Base):
    __tablename__ = "clinical_parameters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), unique=True, nullable=False)
    fasting_glucose = Column(Float, nullable=True) # mg/dL
    post_meal_glucose = Column(Float, nullable=True) # mg/dL
    hba1c = Column(Float, nullable=True) # %
    systolic_bp = Column(Integer, nullable=True) # mmHg
    diastolic_bp = Column(Integer, nullable=True) # mmHg
    previous_eye_disease = Column(String, nullable=True)
    smoking_status = Column(String, nullable=True) # Non-smoker, Former, Current
    previous_dr_history = Column(Boolean, default=False)
    previous_ophthalmology_visit = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    recorded_by = Column(String, nullable=True)
    
    patient = relationship("Patient", back_populates="clinical_parameters")
