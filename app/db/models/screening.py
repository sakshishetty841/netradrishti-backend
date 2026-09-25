import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class EyeEnum(str, enum.Enum):
    RIGHT = "RIGHT"
    LEFT = "LEFT"
    BOTH = "BOTH"

class ScreeningStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REJECTED_POOR_QUALITY = "REJECTED_POOR_QUALITY"

class Screening(Base):
    __tablename__ = "screenings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    screening_id = Column(String, unique=True, index=True, nullable=False) # e.g. SCR-10001
    local_id = Column(String, unique=True, index=True, nullable=True) # Offline sync UUID
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    eye = Column(SQLEnum(EyeEnum), nullable=False, default=EyeEnum.RIGHT)
    screening_center_id = Column(String, ForeignKey("screening_centers.id"), nullable=True)
    health_worker_id = Column(String, ForeignKey("users.id"), nullable=True)
    image_id = Column(String, ForeignKey("retinal_images.id"), nullable=True)
    status = Column(SQLEnum(ScreeningStatusEnum), default=ScreeningStatusEnum.QUEUED, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    patient = relationship("Patient", back_populates="screenings")
    image = relationship("RetinalImage", foreign_keys=[image_id], post_update=True)
    prediction = relationship("Prediction", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    doctor_review = relationship("DoctorReview", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="screening", cascade="all, delete-orphan")

class RetinalImage(Base):
    __tablename__ = "retinal_images"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    screening_id = Column(String, nullable=True) # Linked back
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    checksum = Column(String, nullable=True)
    eye = Column(SQLEnum(EyeEnum), nullable=False, default=EyeEnum.RIGHT)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    quality_status = Column(String, default="pending") # good, poor, pending
