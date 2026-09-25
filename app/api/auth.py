from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import (
    LoginRequest, Token, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.core.permissions import get_current_user
from app.db.models.user import User
from app.utils.audit import log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token, summary="User login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, req.user_id, req.password)
    ip_addr = request.client.host if request.client else None
    
    if not user:
        log_audit(db, user_id=req.user_id, action="LOGIN_FAILED", ip_address=ip_addr)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID or password"
        )
        
    access_token, refresh_token = auth_service.create_user_tokens(user)
    log_audit(db, user_id=user.user_id, action="LOGIN_SUCCESS", entity_type="User", entity_id=user.id, ip_address=ip_addr)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", summary="User logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit(db, user_id=current_user.user_id, action="LOGOUT")
    return {"message": "Logged out successfully"}

@router.post("/forgot-password", summary="Request password reset OTP")
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    ip_addr = request.client.host if request.client else None
    success, msg = auth_service.request_password_reset(db, req.user_id)
    log_audit(db, user_id=req.user_id, action="FORGOT_PASSWORD_REQUEST", ip_address=ip_addr)
    return {"message": msg}

@router.post("/verify-otp", summary="Verify reset OTP")
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    valid = auth_service.verify_otp(db, req.user_id, req.otp)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code")
    return {"message": "OTP verified successfully"}

@router.post("/reset-password", summary="Reset password using OTP")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    success = auth_service.reset_password(db, req.user_id, req.otp, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Password reset failed. Invalid OTP or user.")
    log_audit(db, user_id=req.user_id, action="PASSWORD_RESET_SUCCESS")
    return {"message": "Password reset successfully. You may now login."}

@router.get("/me", response_model=UserResponse, summary="Get current logged in user details")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
