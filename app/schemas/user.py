from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.db.models.user import UserRole

class UserBase(BaseModel):
    name: str
    role: UserRole
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    facility_id: Optional[str] = None
    district: Optional[str] = None
    area: Optional[str] = None

class UserCreate(UserBase):
    user_id: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    facility_id: Optional[str] = None
    district: Optional[str] = None
    area: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
