from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.review import DoctorReview, SpecialistReview, DoctorDecisionEnum, SpecialistDecisionEnum
from app.db.models.screening import Screening, ScreeningStatusEnum
from app.db.models.referral import Referral, ReferralStatusEnum
from app.schemas.review import DoctorReviewCreate, SpecialistReviewCreate

class ReviewService:
    def _generate_review_id(self, db: Session, prefix: str = "REV") -> str:
        count = db.query(DoctorReview).count() + db.query(SpecialistReview).count() + 10001
        return f"{prefix}-{count}"

    def submit_doctor_review(
        self,
        db: Session,
        screening_id_or_uuid: str,
        review_in: DoctorReviewCreate,
        doctor_id: str
    ) -> DoctorReview:
        screening = db.query(Screening).filter(
            (Screening.id == screening_id_or_uuid) | (Screening.screening_id == screening_id_or_uuid)
        ).first()
        if not screening:
            raise HTTPException(status_code=404, detail=f"Screening '{screening_id_or_uuid}' not found")
            
        existing = db.query(DoctorReview).filter(DoctorReview.screening_id == screening.id).first()
        if existing:
            existing.decision = review_in.decision
            existing.notes = review_in.notes
            existing.reviewed_at = datetime.utcnow()
            review = existing
        else:
            rev_id = self._generate_review_id(db, "REV")
            review = DoctorReview(
                review_id=rev_id,
                screening_id=screening.id,
                doctor_id=doctor_id,
                decision=review_in.decision,
                notes=review_in.notes
            )
            db.add(review)

        # Update screening status based on review decision
        if review_in.decision == DoctorDecisionEnum.AGREE_WITH_SCREENING:
            screening.status = ScreeningStatusEnum.COMPLETED
        elif review_in.decision == DoctorDecisionEnum.REQUEST_RESCAN:
            screening.status = ScreeningStatusEnum.REJECTED_POOR_QUALITY
        elif review_in.decision == DoctorDecisionEnum.REFER_TO_SPECIALIST:
            screening.status = ScreeningStatusEnum.REQUIRES_REVIEW
            
        db.commit()
        db.refresh(review)
        return review

    def submit_specialist_review(
        self,
        db: Session,
        referral_id_or_uuid: str,
        review_in: SpecialistReviewCreate,
        doctor_id: str
    ) -> SpecialistReview:
        referral = db.query(Referral).filter(
            (Referral.id == referral_id_or_uuid) | (Referral.referral_id == referral_id_or_uuid)
        ).first()
        if not referral:
            raise HTTPException(status_code=404, detail=f"Referral '{referral_id_or_uuid}' not found")
            
        existing = db.query(SpecialistReview).filter(SpecialistReview.referral_id == referral.id).first()
        if existing:
            existing.decision = review_in.decision
            existing.notes = review_in.notes
            existing.further_tests = review_in.further_tests
            existing.reviewed_at = datetime.utcnow()
            review = existing
        else:
            rev_id = self._generate_review_id(db, "SREV")
            review = SpecialistReview(
                review_id=rev_id,
                referral_id=referral.id,
                doctor_id=doctor_id,
                decision=review_in.decision,
                notes=review_in.notes,
                further_tests=review_in.further_tests,
                consultation_status="IN_PROGRESS"
            )
            db.add(review)

        if review_in.decision == SpecialistDecisionEnum.CONSULTATION_COMPLETED:
            review.consultation_status = "COMPLETED"
            referral.status = ReferralStatusEnum.COMPLETED
        else:
            referral.status = ReferralStatusEnum.IN_REVIEW
            
        db.commit()
        db.refresh(review)
        return review

review_service = ReviewService()
