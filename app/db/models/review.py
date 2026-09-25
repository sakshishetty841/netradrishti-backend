import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class DoctorDecisionEnum(str, enum.Enum):
    AGREE_WITH_SCREENING = "AGREE_WITH_SCREENING"
    REQUEST_RESCAN = "REQUEST_RESCAN"
    REFER_TO_SPECIALIST = "REFER_TO_SPECIALIST"
    FURTHER_CLINICAL_EVALUATION = "FURTHER_CLINICAL_EVALUATION"

class SpecialistDecisionEnum(str, enum.Enum):
    CONFIRM_FINDINGS = "CONFIRM_FINDINGS"
    REQUEST_FURTHER_TESTS = "REQUEST_FURTHER_TESTS"
    SCHEDULE_CONSULTATION = "SCHEDULE_CONSULTATION"
    CONSULTATION_COMPLETED = "CONSULTATION_COMPLETED"

class DoctorReview(Base):
    __tablename__ = "doctor_reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String, unique=True, index=True, nullable=False) # REV-10001
    screening_id = Column(String, ForeignKey("screenings.id"), unique=True, nullable=False)
    doctor_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision = Column(SQLEnum(DoctorDecisionEnum), nullable=False)
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    
    screening = relationship("Screening", back_populates="doctor_review")

class SpecialistReview(Base):
    __tablename__ = "specialist_reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String, unique=True, index=True, nullable=False) # SREV-10001
    referral_id = Column(String, ForeignKey("referrals.id"), unique=True, nullable=False)
    doctor_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision = Column(SQLEnum(SpecialistDecisionEnum), nullable=False)
    notes = Column(Text, nullable=True)
    further_tests = Column(Text, nullable=True)
    consultation_status = Column(String, default="PENDING") # PENDING, SCHEDULED, COMPLETED
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    
    referral = relationship("Referral", back_populates="specialist_review")
