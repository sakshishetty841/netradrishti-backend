import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.db.database import Base

class ReportJob(Base):
    __tablename__ = "report_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, unique=True, index=True, nullable=False) # e.g. JOB-10001
    report_type = Column(String, nullable=False) # screening, patient, analytics
    parameters_json = Column(Text, nullable=True)
    status = Column(String, default="PENDING", nullable=False) # PENDING, PROCESSING, COMPLETED, FAILED
    file_path = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
