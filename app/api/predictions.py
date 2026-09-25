from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.screening import EyeEnum, Screening
from app.db.models.patient import Patient
from app.schemas.prediction import LegacyPredictResponse
from app.services.screening_service import screening_service
from app.services.patient_service import patient_service
from app.schemas.patient import PatientCreate
from app.core.permissions import get_current_user
from app.utils.audit import log_audit

router = APIRouter(tags=["Predictions & Legacy API Contract"])

@router.post(
    "/predict",
    response_model=LegacyPredictResponse,
    summary="Legacy-compatible AI screening endpoint (POST http://localhost:8000/predict)"
)
async def predict_legacy(
    image: UploadFile = File(...),
    eye: Optional[str] = Form("RIGHT"),
    patient_id: Optional[str] = Form(None),
    screening_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_bytes = await image.read()
    
    try:
        eye_enum = EyeEnum(eye.upper()) if eye else EyeEnum.RIGHT
    except Exception:
        eye_enum = EyeEnum.RIGHT

    # Resolve or create screening
    screening = None
    if screening_id:
        screening = db.query(Screening).filter(
            (Screening.id == screening_id) | (Screening.screening_id == screening_id)
        ).first()
        
    if not screening:
        patient = None
        if patient_id:
            patient = patient_service.get_patient(db, patient_id)
        if not patient:
            p_in = PatientCreate(name="Walk-in Patient", age=50, gender="Unknown")
            patient = patient_service.create_patient(db, p_in, creator_id=current_user.id)
            
        screening = screening_service.create_screening_record(
            db,
            patient_id=patient.id,
            eye=eye_enum,
            health_worker_id=current_user.id
        )

    # Call canonical single execution path in screening_service
    res = screening_service.analyze(
        db,
        screening=screening,
        image_bytes=image_bytes,
        filename=image.filename or "fundus_scan.jpg",
        eye=eye_enum
    )
    
    log_audit(db, user_id=current_user.user_id, action="LEGACY_PREDICT_EXECUTED", entity_type="Screening", entity_id=screening.screening_id)
    return res
