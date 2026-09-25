from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.screening import Screening, EyeEnum
from app.services.patient_service import patient_service
from app.services.screening_service import screening_service
from app.schemas.patient import PatientCreate

class SyncService:
    def sync_screening(
        self,
        db: Session,
        local_id: str,
        patient_id: Optional[str],
        patient_name: Optional[str],
        age: Optional[int],
        gender: Optional[str],
        village: Optional[str],
        eye_str: str,
        image_bytes: bytes,
        filename: str,
        health_worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Idempotent offline screening synchronization service.
        Prevents duplicate processing for identical local UUIDs.
        """
        # Idempotency check
        existing = db.query(Screening).filter(Screening.local_id == local_id).first()
        if existing:
            pred = existing.prediction
            return {
                "local_id": local_id,
                "screening_id": existing.screening_id,
                "status": "already_synced",
                "message": "Screening already processed idempotently.",
                "result": {
                    "grade": pred.grade if pred else "Pending",
                    "confidence": pred.confidence if pred else 0.0,
                    "heatmap_url": pred.heatmap_url if pred else "",
                    "urgency": pred.urgency if pred else "routine"
                }
            }

        # Resolve or create Patient
        patient = None
        if patient_id:
            patient = patient_service.get_patient(db, patient_id)
            
        if not patient:
            p_in = PatientCreate(
                name=patient_name or "Anonymous Patient",
                age=age or 45,
                gender=gender or "Male",
                village=village or "Rural Village"
            )
            patient = patient_service.create_patient(db, p_in, creator_id=health_worker_id)

        try:
            eye_enum = EyeEnum(eye_str.upper())
        except Exception:
            eye_enum = EyeEnum.RIGHT

        screening = screening_service.create_screening_record(
            db,
            patient_id=patient.id,
            eye=eye_enum,
            health_worker_id=health_worker_id,
            local_id=local_id
        )

        analysis_res = screening_service.analyze(
            db,
            screening=screening,
            image_bytes=image_bytes,
            filename=filename,
            eye=eye_enum
        )

        return {
            "local_id": local_id,
            "screening_id": screening.screening_id,
            "status": "synced",
            "result": analysis_res
        }

sync_service = SyncService()
