import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class ScreeningCenter(Base):
    __tablename__ = "screening_centers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    facility_type = Column(String, nullable=False) # e.g. PHC, CHC, Vision Center, Sub-Center
    village = Column(String, nullable=True)
    block = Column(String, nullable=True)
    district = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False, default="Karnataka")
    address = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    staff_members = relationship("User", back_populates="facility")
    patients = relationship("Patient", back_populates="screening_center")
