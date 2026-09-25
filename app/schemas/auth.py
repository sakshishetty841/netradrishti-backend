from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    user_id: str
    password: str

class ForgotPasswordRequest(BaseModel):
    user_id: str

class VerifyOTPRequest(BaseModel):
    user_id: str
    otp: str

class ResetPasswordRequest(BaseModel):
    user_id: str
    otp: str
    new_password: str
