import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class PriorityEnum(str, enum.Enum):
    ROUTINE = "ROUTINE"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ReferralStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String, unique=True, index=True, nullable=False) # e.g. REF-10001
    screening_id = Column(String, ForeignKey("screenings.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    source_facility = Column(String, nullable=True)
    destination_facility = Column(String, nullable=True)
    destination_doctor = Column(String, ForeignKey("users.id"), nullable=True)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.ROUTINE, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(SQLEnum(ReferralStatusEnum), default=ReferralStatusEnum.PENDING, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    screening = relationship("Screening", back_populates="referrals")
    specialist_review = relationship("SpecialistReview", back_populates="referral", uselist=False, cascade="all, delete-orphan")
