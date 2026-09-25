import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.db.database import Base

class ClinicalProtocolSettings(Base):
    __tablename__ = "clinical_protocol_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(Integer, default=1, nullable=False)
    mapping_json = Column(Text, nullable=False) # JSON dict of protocol mappings
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
