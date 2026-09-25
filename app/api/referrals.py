from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.referral import ReferralStatusEnum
from app.schemas.referral import ReferralCreate, ReferralResponse, ReferralUpdate
from app.services.referral_service import referral_service
from app.core.permissions import get_current_user, require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/referrals", tags=["Referrals"])

@router.post("", response_model=ReferralResponse, status_code=status.HTTP_201_CREATED, summary="Create a new referral")
def create_referral(
    req: ReferralCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ASHA, UserRole.PHC_DOCTOR, UserRole.ADMIN]))
):
    ref = referral_service.create_referral(db, req, creator_id=current_user.id)
    log_audit(db, user_id=current_user.user_id, action="REFERRAL_CREATED", entity_type="Referral", entity_id=ref.referral_id)
    return ref

@router.get("", response_model=List[ReferralResponse], summary="List referrals")
def list_referrals(
    status: Optional[ReferralStatusEnum] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dest_doc = current_user.id if current_user.role == UserRole.OPHTHALMOLOGY_DOCTOR else None
    return referral_service.get_referrals(db, status=status, destination_doctor=dest_doc)

@router.get("/{referral_id}", response_model=ReferralResponse, summary="Get referral by ID")
def get_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = referral_service.get_referral(db, referral_id)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Referral '{referral_id}' not found")
    return ref

@router.put("/{referral_id}", response_model=ReferralResponse, summary="Update referral details or status")
def update_referral(
    referral_id: str,
    req: ReferralUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = referral_service.update_referral(db, referral_id, req)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Referral '{referral_id}' not found")
    log_audit(db, user_id=current_user.user_id, action="REFERRAL_UPDATED", entity_type="Referral", entity_id=ref.referral_id)
    return ref
