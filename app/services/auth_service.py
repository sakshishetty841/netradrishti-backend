from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models.user import User, UserRole
from app.db.models.otp import PasswordResetOTP
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, generate_otp, hash_otp, verify_otp_hash
)
from app.core.config import settings

class AuthService:
    def authenticate_user(self, db: Session, user_id: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create_user_tokens(self, user: User) -> Tuple[str, str]:
        token_payload = {
            "sub": user.user_id,
            "id": user.id,
            "role": user.role.value if isinstance(user.role, UserRole) else str(user.role)
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        return access_token, refresh_token

    def request_password_reset(self, db: Session, user_id: str) -> Tuple[bool, str]:
        # Always return success message to prevent user enumeration
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return True, "If the account exists, an OTP has been dispatched."
            
        otp = generate_otp()
        otp_h = hash_otp(otp, user.user_id)
        expiry = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        
        # Clear existing active OTPs
        db.query(PasswordResetOTP).filter(PasswordResetOTP.user_id == user.user_id).delete()
        
        reset_otp = PasswordResetOTP(
            user_id=user.user_id,
            otp_hash=otp_h,
            expires_at=expiry,
            attempts=0
        )
        db.add(reset_otp)
        db.commit()
        
        # Mock provider dispatch (log or return for dev)
        return True, f"If the account exists, an OTP has been dispatched. (Dev Mock OTP: {otp})"

    def verify_otp(self, db: Session, user_id: str, otp: str) -> bool:
        record = db.query(PasswordResetOTP).filter(
            PasswordResetOTP.user_id == user_id,
            PasswordResetOTP.expires_at > datetime.utcnow()
        ).first()
        
        if not record:
            return False
            
        if record.attempts >= settings.MAX_OTP_ATTEMPTS:
            db.delete(record)
            db.commit()
            return False
            
        record.attempts += 1
        db.commit()
        
        return verify_otp_hash(otp, user_id, record.otp_hash)

    def reset_password(self, db: Session, user_id: str, otp: str, new_password: str) -> bool:
        if not self.verify_otp(db, user_id, otp):
            return False
            
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False
            
        user.password_hash = get_password_hash(new_password)
        db.query(PasswordResetOTP).filter(PasswordResetOTP.user_id == user_id).delete()
        db.commit()
        return True

auth_service = AuthService()
