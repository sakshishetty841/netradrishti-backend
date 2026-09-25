import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.db.database import Base

class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
