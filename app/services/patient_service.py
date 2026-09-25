import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.patient import Patient, DiabetesProfile, ClinicalParameters
from app.db.models.screening import Screening, ScreeningStatusEnum
from app.db.models.referral import Referral
from app.db.models.review import DoctorReview, SpecialistReview
from app.schemas.patient import PatientCreate, PatientUpdate, PatientJourneyResponse, PatientJourneyStage

class PatientService:
    def _generate_patient_id(self, db: Session) -> str:
        count = db.query(Patient).count() + 10001
        return f"PAT-{count}"

    def create_patient(self, db: Session, patient_in: PatientCreate, creator_id: Optional[str] = None) -> Patient:
        patient_id_str = self._generate_patient_id(db)
        
        patient = Patient(
            patient_id=patient_id_str,
            name=patient_in.name,
            age=patient_in.age,
            gender=patient_in.gender,
            mobile_optional=patient_in.mobile_optional,
            village=patient_in.village,
            screening_center_id=patient_in.screening_center_id,
            created_by=creator_id,
            address_note=patient_in.address_note
        )
        db.add(patient)
        db.flush()
        
        if patient_in.diabetes_profile:
            dp_data = patient_in.diabetes_profile.model_dump(exclude_unset=True)
            dp = DiabetesProfile(patient_id=patient.id, **dp_data)
            db.add(dp)
            
        if patient_in.clinical_parameters:
            cp_data = patient_in.clinical_parameters.model_dump(exclude_unset=True)
            cp = ClinicalParameters(patient_id=patient.id, recorded_by=creator_id, **cp_data)
            db.add(cp)
            
        db.commit()
        db.refresh(patient)
        return patient

    def get_patient(self, db: Session, patient_id_or_uuid: str) -> Optional[Patient]:
        return db.query(Patient).filter(
            (Patient.id == patient_id_or_uuid) | (Patient.patient_id == patient_id_or_uuid)
        ).first()

    def update_patient(self, db: Session, patient_id_or_uuid: str, patient_in: PatientUpdate) -> Optional[Patient]:
        patient = self.get_patient(db, patient_id_or_uuid)
        if not patient:
            return None
            
        update_data = patient_in.model_dump(exclude={"diabetes_profile", "clinical_parameters"}, exclude_unset=True)
        for key, val in update_data.items():
            setattr(patient, key, val)
            
        if patient_in.diabetes_profile:
            if not patient.diabetes_profile:
                patient.diabetes_profile = DiabetesProfile(patient_id=patient.id)
            for key, val in patient_in.diabetes_profile.model_dump(exclude_unset=True).items():
                setattr(patient.diabetes_profile, key, val)

        if patient_in.clinical_parameters:
            if not patient.clinical_parameters:
                patient.clinical_parameters = ClinicalParameters(patient_id=patient.id)
            for key, val in patient_in.clinical_parameters.model_dump(exclude_unset=True).items():
                setattr(patient.clinical_parameters, key, val)
                
        db.commit()
        db.refresh(patient)
        return patient

    def get_patient_history(self, db: Session, patient_id_or_uuid: str) -> List[Dict[str, Any]]:
        patient = self.get_patient(db, patient_id_or_uuid)
        if not patient:
            return []
            
        screenings = db.query(Screening).filter(Screening.patient_id == patient.id).order_by(Screening.created_at.desc()).all()
        history = []
        for s in screenings:
            pred = s.prediction
            dr = s.doctor_review
            ref = db.query(Referral).filter(Referral.screening_id == s.id).first()
            
            history.append({
                "screening_id": s.screening_id,
                "date": s.created_at.strftime("%Y-%m-%d"),
                "eye": s.eye.value,
                "status": s.status.value,
                "grade": pred.grade if pred else None,
                "confidence": pred.confidence if pred else None,
                "recommendation": pred.recommendation if pred else None,
                "review_status": dr.decision.value if dr else "PENDING_REVIEW",
                "referral_status": ref.status.value if ref else "NONE"
            })
        return history

    def get_patient_journey(self, db: Session, patient_id_or_uuid: str) -> PatientJourneyResponse:
        patient = self.get_patient(db, patient_id_or_uuid)
        if not patient:
            return PatientJourneyResponse(patient_id=patient_id_or_uuid, stages=[])
            
        latest_screening = db.query(Screening).filter(Screening.patient_id == patient.id).order_by(Screening.created_at.desc()).first()
        
        stages = []
        if not latest_screening:
            stages.append(PatientJourneyStage(stage="SCREENING_REGISTERED", status="pending"))
            return PatientJourneyResponse(patient_id=patient.patient_id, stages=stages)

        stages.append(PatientJourneyStage(
            stage="SCREENING_COMPLETED",
            status="completed",
            date=latest_screening.created_at.strftime("%Y-%m-%d")
        ))
        
        pred = latest_screening.prediction
        if pred:
            stages.append(PatientJourneyStage(
                stage="AI_SCREENING",
                status="completed",
                grade=pred.grade,
                details={"confidence": pred.confidence, "urgency": pred.urgency}
            ))
        else:
            stages.append(PatientJourneyStage(stage="AI_SCREENING", status="pending"))

        dr = latest_screening.doctor_review
        if dr:
            stages.append(PatientJourneyStage(
                stage="CLINICAL_REVIEW",
                status="completed",
                details={"decision": dr.decision.value, "reviewed_at": dr.reviewed_at.strftime("%Y-%m-%d")}
            ))
        else:
            stages.append(PatientJourneyStage(stage="CLINICAL_REVIEW", status="pending"))

        ref = db.query(Referral).filter(Referral.screening_id == latest_screening.id).first()
        if ref:
            stages.append(PatientJourneyStage(
                stage="SPECIALIST_REFERRAL",
                status="completed" if ref.status != "CANCELLED" else "cancelled",
                details={"priority": ref.priority.value, "status": ref.status.value}
            ))
            srev = ref.specialist_review
            if srev:
                stages.append(PatientJourneyStage(
                    stage="SPECIALIST_CONSULTATION",
                    status="completed",
                    details={"decision": srev.decision.value, "consultation_status": srev.consultation_status}
                ))
            else:
                stages.append(PatientJourneyStage(stage="SPECIALIST_CONSULTATION", status="pending"))
        else:
            stages.append(PatientJourneyStage(stage="SPECIALIST_REFERRAL", status="not_required"))
            
        stages.append(PatientJourneyStage(stage="FOLLOW_UP_SCREENING", status="scheduled" if pred and pred.grade != "No DR" else "routine"))

        return PatientJourneyResponse(patient_id=patient.patient_id, stages=stages)

patient_service = PatientService()
