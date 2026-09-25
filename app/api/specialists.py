from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.referral import Referral
from app.schemas.referral import ReferralResponse
from app.schemas.review import SpecialistReviewCreate, SpecialistReviewResponse
from app.services.review_service import review_service
from app.core.permissions import require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/specialist", tags=["Specialist Reviews"])

@router.get("/referrals", response_model=List[ReferralResponse], summary="View incoming specialist referrals")
def get_specialist_referrals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPHTHALMOLOGY_DOCTOR, UserRole.ADMIN]))
):
    return db.query(Referral).filter(
        (Referral.destination_doctor == current_user.id) | (Referral.destination_doctor == None)
    ).all()

@router.get("/cases/{id}", response_model=ReferralResponse, summary="Get specialist referral case details")
def get_specialist_case(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPHTHALMOLOGY_DOCTOR, UserRole.ADMIN]))
):
    ref = db.query(Referral).filter((Referral.id == id) | (Referral.referral_id == id)).first()
    if not ref:
        raise HTTPException(status_code=404, detail=f"Specialist referral case '{id}' not found")
    return ref

@router.post("/cases/{id}/review", response_model=SpecialistReviewResponse, summary="Submit specialist review decision")
def submit_specialist_review(
    id: str,
    req: SpecialistReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPHTHALMOLOGY_DOCTOR, UserRole.ADMIN]))
):
    review = review_service.submit_specialist_review(db, id, req, doctor_id=current_user.id)
    log_audit(db, user_id=current_user.user_id, action="SPECIALIST_REVIEW_SUBMITTED", entity_type="SpecialistReview", entity_id=review.review_id)
    return review
