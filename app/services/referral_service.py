from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.referral import Referral, PriorityEnum, ReferralStatusEnum
from app.db.models.screening import Screening
from app.schemas.referral import ReferralCreate, ReferralUpdate

class ReferralService:
    def _generate_referral_id(self, db: Session) -> str:
        count = db.query(Referral).count() + 10001
        return f"REF-{count}"

    def create_referral(self, db: Session, ref_in: ReferralCreate, creator_id: Optional[str] = None) -> Referral:
        screening = db.query(Screening).filter(
            (Screening.id == ref_in.screening_id) | (Screening.screening_id == ref_in.screening_id)
        ).first()
        if not screening:
            raise HTTPException(status_code=404, detail=f"Screening '{ref_in.screening_id}' not found")
            
        ref_id_str = self._generate_referral_id(db)
        referral = Referral(
            referral_id=ref_id_str,
            screening_id=screening.id,
            patient_id=screening.patient_id,
            destination_facility=ref_in.destination_facility,
            destination_doctor=ref_in.destination_doctor,
            priority=ref_in.priority,
            reason=ref_in.reason,
            status=ReferralStatusEnum.PENDING,
            created_by=creator_id
        )
        db.add(referral)
        db.commit()
        db.refresh(referral)
        return referral

    def get_referrals(
        self,
        db: Session,
        status: Optional[ReferralStatusEnum] = None,
        destination_doctor: Optional[str] = None
    ) -> List[Referral]:
        query = db.query(Referral)
        if status:
            query = query.filter(Referral.status == status)
        if destination_doctor:
            query = query.filter(Referral.destination_doctor == destination_doctor)
        return query.order_by(Referral.created_at.desc()).all()

    def get_referral(self, db: Session, referral_id_or_uuid: str) -> Optional[Referral]:
        return db.query(Referral).filter(
            (Referral.id == referral_id_or_uuid) | (Referral.referral_id == referral_id_or_uuid)
        ).first()

    def update_referral(self, db: Session, referral_id_or_uuid: str, ref_in: ReferralUpdate) -> Optional[Referral]:
        referral = self.get_referral(db, referral_id_or_uuid)
        if not referral:
            return None
        for k, v in ref_in.model_dump(exclude_unset=True).items():
            setattr(referral, k, v)
        db.commit()
        db.refresh(referral)
        return referral

referral_service = ReferralService()
