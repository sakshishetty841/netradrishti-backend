import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    screening_id = Column(String, ForeignKey("screenings.id"), unique=True, nullable=False)
    grade = Column(String, nullable=False, index=True) # No DR, Mild, Moderate, Severe, Proliferative
    confidence = Column(Float, nullable=False)
    findings = Column(Text, nullable=True) # JSON encoded list of findings
    heatmap_url = Column(String, nullable=True)
    explanation = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    urgency = Column(String, nullable=False, default="routine") # routine, moderate, high, urgent
    model_name = Column(String, nullable=False, default="NetraDrishti-DR")
    model_version = Column(String, nullable=False, default="prototype-v1")
    explainability_version = Column(String, nullable=False, default="gradcam-v1")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    screening = relationship("Screening", back_populates="prediction")
