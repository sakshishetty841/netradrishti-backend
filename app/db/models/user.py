import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserRole(str, enum.Enum):
    ASHA = "ASHA"
    PHC_DOCTOR = "PHC_DOCTOR"
    OPHTHALMOLOGY_DOCTOR = "OPHTHALMOLOGY_DOCTOR"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, index=True, nullable=False) # e.g. USR-1001
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.ASHA)
    email = Column(String, unique=True, index=True, nullable=True)
    mobile = Column(String, nullable=True)
    facility_id = Column(String, ForeignKey("screening_centers.id"), nullable=True)
    district = Column(String, nullable=True)
    area = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    facility = relationship("ScreeningCenter", back_populates="staff_members")
