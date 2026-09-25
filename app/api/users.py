from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.security import get_password_hash
from app.core.permissions import require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/admin/users", tags=["Admin User Management"])

@router.get("", response_model=List[UserResponse], summary="List all system users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return db.query(User).all()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create a new user account")
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    existing = db.query(User).filter(User.user_id == req.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"User ID '{req.user_id}' already exists")
        
    user = User(
        user_id=req.user_id,
        name=req.name,
        password_hash=get_password_hash(req.password),
        role=req.role,
        email=req.email,
        mobile=req.mobile,
        facility_id=req.facility_id,
        district=req.district,
        area=req.area
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_audit(db, user_id=current_user.user_id, action="USER_CREATED", entity_type="User", entity_id=user.user_id)
    return user

@router.put("/{user_id}", response_model=UserResponse, summary="Update user account")
def update_user(
    user_id: str,
    req: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    user = db.query(User).filter((User.id == user_id) | (User.user_id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
        
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
        
    db.commit()
    db.refresh(user)
    log_audit(db, user_id=current_user.user_id, action="USER_UPDATED", entity_type="User", entity_id=user.user_id)
    return user
