from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.screening import Screening, ScreeningStatusEnum
from app.schemas.screening import ScreeningResponse
from app.schemas.review import DoctorReviewCreate, DoctorReviewResponse
from app.services.review_service import review_service
from app.core.permissions import require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/doctor", tags=["PHC Doctor Reviews"])

@router.get("/reviews/pending", response_model=List[ScreeningResponse], summary="List pending screenings requiring PHC doctor clinical review")
def get_pending_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PHC_DOCTOR, UserRole.ADMIN]))
):
    return db.query(Screening).filter(Screening.status == ScreeningStatusEnum.REQUIRES_REVIEW).all()

@router.get("/cases/{screening_id}", response_model=ScreeningResponse, summary="Get doctor case details")
def get_doctor_case(
    screening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PHC_DOCTOR, UserRole.ADMIN]))
):
    screening = db.query(Screening).filter(
        (Screening.id == screening_id) | (Screening.screening_id == screening_id)
    ).first()
    if not screening:
        raise HTTPException(status_code=404, detail=f"Screening case '{screening_id}' not found")
    return screening

@router.post("/cases/{screening_id}/review", response_model=DoctorReviewResponse, summary="Submit PHC doctor review decision")
def submit_doctor_review(
    screening_id: str,
    req: DoctorReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PHC_DOCTOR, UserRole.ADMIN]))
):
    review = review_service.submit_doctor_review(db, screening_id, req, doctor_id=current_user.id)
    log_audit(db, user_id=current_user.user_id, action="PHC_DOCTOR_REVIEW_SUBMITTED", entity_type="DoctorReview", entity_id=review.review_id)
    return review
